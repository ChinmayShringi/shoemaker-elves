#!/usr/bin/env python3
"""
SessionEnd hook handler for the GPT Agent Orchestrator.

This script is invoked when an AI agent session ends.
It reads hook JSON from stdin, processes the transcript,
updates shared state, and optionally spawns the next agent task.

CRITICAL: This runs as a subprocess of the AI agent CLI.
It must exit quickly and handle errors gracefully.
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from state import State
from transcript_parser import parse_transcript


def log(msg: str):
    """Log to stderr (visible in agent debug output)."""
    print(f"[orchestrator-hook] {msg}", file=sys.stderr)


def read_hook_input() -> dict:
    """Read and parse hook JSON from stdin."""
    try:
        return json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return {}


def find_state(cwd: str) -> State | None:
    """Find the orchestrator state file via the reference file in the project."""
    ref_path = Path(cwd) / ".claude" / "orchestrator_ref.json"
    if not ref_path.exists():
        return None

    try:
        ref = json.loads(ref_path.read_text())
        state_file = ref.get("state_file")
        if state_file and Path(state_file).exists():
            return State(state_file)
    except (json.JSONDecodeError, KeyError):
        pass

    return None


def update_context_md(project_dir: str, state_data: dict, completed_task: dict):
    """Append a brief summary of the completed task to the context file."""
    context_md = Path(project_dir) / "CLAUDE.md"
    if not context_md.exists():
        return

    task_index = completed_task["index"]
    title = completed_task.get("title", f"Task {task_index + 1}")
    summary = completed_task.get("result_summary", "")
    files = completed_task.get("files_modified", [])

    # Truncate summary for CLAUDE.md
    if isinstance(summary, str) and len(summary) > 300:
        summary = summary[:300] + "..."

    append_text = f"\n- Task {task_index + 1} ({completed_task['status']}): {title}"
    if summary:
        append_text += f"\n  Summary: {summary}"
    if files:
        append_text += f"\n  Files: {', '.join(files)}"

    try:
        content = context_md.read_text()

        # Find the "## Progress So Far" section and append there
        marker = "## Progress So Far"
        if marker in content:
            # Insert before the next section or at end of that section
            parts = content.split(marker, 1)
            # Find the next ## heading after our marker
            rest = parts[1]
            next_section = rest.find("\n## ")
            if next_section != -1:
                updated = (
                    parts[0]
                    + marker
                    + rest[:next_section]
                    + append_text
                    + rest[next_section:]
                )
            else:
                updated = parts[0] + marker + rest + append_text
        else:
            # Just append
            updated = content + "\n" + append_text

        context_md.write_text(updated)
    except OSError as e:
        log(f"Failed to update context file: {e}")


def launch_next_task(state_data: dict, next_task: dict):
    """Spawn a new agent process for the next task in the queue."""
    orchestrator_dir = state_data["orchestrator_dir"]
    project_dir = state_data["project_dir"]
    config = state_data.get("config", {})

    # Read task prompt from file
    task_file = Path(orchestrator_dir) / next_task["file"]
    if not task_file.exists():
        log(f"Task file not found: {task_file}")
        return

    task_prompt = task_file.read_text().strip()
    if not task_prompt:
        log(f"Task file is empty: {task_file}")
        return

    cmd = [
        "claude",
        "-p",
        task_prompt,
        "--output-format",
        "json",
    ]

    agent_model = config.get("agent_model")
    if agent_model:
        cmd.extend(["--model", agent_model])

    log(f"Launching task {next_task['index'] + 1}: {next_task.get('title', 'untitled')}")

    # Spawn detached so this hook can exit cleanly
    try:
        subprocess.Popen(
            cmd,
            cwd=project_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,  # Fully detach from parent
        )
    except OSError as e:
        log(f"Failed to launch agent: {e}")


def main():
    # 1. Read hook input
    hook_input = read_hook_input()
    if not hook_input:
        log("No hook input received, exiting")
        return

    session_id = hook_input.get("session_id", "")
    transcript_path = hook_input.get("transcript_path", "")
    cwd = hook_input.get("cwd", "")

    if not cwd:
        log("No cwd in hook input, exiting")
        return

    # 2. Find state file
    state = find_state(cwd)
    if state is None:
        # Not an orchestrated project, ignore silently
        return

    # 3. Read current state to check status
    try:
        state_data = state.read()
    except (json.JSONDecodeError, OSError) as e:
        log(f"Failed to read state: {e}")
        return

    # Check if orchestration was aborted
    if state_data.get("status") in ("aborted", "completed"):
        log(f"Orchestration status is {state_data['status']}, not launching next task")
        return

    # 4. Parse transcript
    result = {}
    if transcript_path:
        result = parse_transcript(transcript_path)
        result["session_id"] = session_id
        result["transcript_path"] = transcript_path
    else:
        # No transcript — mark as unknown success=False
        result = {"success": False, "summary": "No transcript available"}

    # 5. Advance state
    current_index = state_data.get("current_task_index", 0)
    tasks = state_data.get("tasks", [])

    if current_index < 0 or current_index >= len(tasks):
        log(f"Invalid current_task_index: {current_index} (total tasks: {len(tasks)})")
        return

    try:
        updated_state = state.advance_task(current_index, result)
    except (json.JSONDecodeError, OSError, IndexError) as e:
        log(f"Failed to advance task: {e}")
        return

    completed_task = updated_state["tasks"][current_index]

    # 6. Update CLAUDE.md with what was done
    update_context_md(cwd, updated_state, completed_task)

    # 7. Decide: launch next task or stop
    next_index = current_index + 1
    max_cost = updated_state.get("config", {}).get("max_cost_usd", float("inf"))
    cost_exceeded = updated_state.get("total_cost_usd", 0) >= max_cost

    if cost_exceeded:
        log(f"Cost ceiling reached: ${updated_state.get('total_cost_usd', 0):.2f}")
        state.set_status("completed", "Cost ceiling reached")
        return

    if next_index < len(updated_state.get("tasks", [])):
        next_task = updated_state["tasks"][next_index]

        # Mark next task as running in state and get fresh state
        fresh_state = state.update_task(next_index, {"status": "running"})

        # Launch it using the fresh state data
        launch_next_task(fresh_state, next_task)
    else:
        # All tasks in current batch done
        log("All tasks in batch completed")
        # Check if this is the last batch or if GPT mode needs to plan next
        current_batch = str(updated_state.get("current_batch", 1))
        batch = updated_state.get("batches", {}).get(current_batch, {})
        if batch:
            # The orchestrator polling loop will detect this and handle GPT assessment
            pass


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"Unhandled error: {e}")
        sys.exit(1)
