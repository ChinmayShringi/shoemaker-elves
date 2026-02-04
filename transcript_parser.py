"""
Parse JSONL transcript files to extract task results.
Transcripts are written by the AI agent at the path provided in the
SessionEnd hook's `transcript_path` field.
"""

import json
from pathlib import Path


def parse_transcript(transcript_path: str) -> dict:
    """Parse a JSONL transcript and return a structured result summary.

    Returns:
        {
            "summary": str,          # Final assistant text
            "files_modified": list,   # Files created/edited
            "tool_calls": int,        # Number of tool invocations
            "input_tokens": int,      # Total input tokens
            "output_tokens": int,     # Total output tokens
            "cost_usd": float,        # Estimated cost
            "success": bool,          # Whether task completed without errors
            "errors": list,           # Any error messages found
        }
    """
    path = Path(transcript_path)
    if not path.exists():
        return {
            "summary": "Transcript file not found",
            "files_modified": [],
            "tool_calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "cost_usd": 0,
            "success": False,
            "errors": [f"Transcript not found: {transcript_path}"],
        }

    entries = []
    for line in path.read_text().strip().split("\n"):
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    assistant_texts = []
    files_modified = set()
    tool_call_count = 0
    total_input_tokens = 0
    total_output_tokens = 0
    errors = []

    for entry in entries:
        entry_type = entry.get("type")

        if entry_type == "assistant":
            msg = entry.get("message", {})

            # Token usage
            usage = msg.get("usage", {})
            total_input_tokens += usage.get("input_tokens", 0)
            total_output_tokens += usage.get("output_tokens", 0)

            # Content blocks
            for block in msg.get("content", []):
                block_type = block.get("type")

                if block_type == "text" and block.get("text"):
                    assistant_texts.append(block["text"])

                elif block_type == "tool_use":
                    tool_call_count += 1
                    tool_name = block.get("name", "")
                    tool_input = block.get("input", {})

                    # Track file modifications
                    if tool_name in ("Edit", "Write", "NotebookEdit"):
                        fp = tool_input.get("file_path", "")
                        if fp:
                            files_modified.add(fp)

                    # Track Bash file operations
                    if tool_name == "Bash":
                        cmd = tool_input.get("command", "")
                        # Rough detection of file-modifying commands
                        if any(
                            op in cmd
                            for op in ["mv ", "cp ", "mkdir ", "rm ", "touch "]
                        ):
                            # Can't precisely track, but note it
                            pass

        elif entry_type == "tool_result":
            # Check for error results
            if entry.get("is_error"):
                error_content = entry.get("content", "")
                if isinstance(error_content, list):
                    for block in error_content:
                        if block.get("type") == "text":
                            errors.append(block.get("text", "")[:200])
                elif isinstance(error_content, str):
                    errors.append(error_content[:200])

    # Estimate cost (Sonnet pricing approximation)
    # Input: $3/MTok, Output: $15/MTok
    cost_usd = (total_input_tokens * 3.0 / 1_000_000) + (
        total_output_tokens * 15.0 / 1_000_000
    )

    # Use the last substantive assistant text as the summary
    summary = ""
    if assistant_texts:
        # Find the last non-trivial text
        for text in reversed(assistant_texts):
            if len(text.strip()) > 20:
                summary = text.strip()
                break
        if not summary:
            summary = assistant_texts[-1].strip()

    # Truncate summary if very long
    if len(summary) > 1000:
        summary = summary[:1000] + "..."

    return {
        "summary": summary,
        "files_modified": sorted(files_modified),
        "tool_calls": tool_call_count,
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        "cost_usd": round(cost_usd, 4),
        "success": len(errors) == 0,
        "errors": errors,
    }
