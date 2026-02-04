"""
State management for the GPT Agent Orchestrator.
Uses file locking (fcntl.flock) for safe concurrent access
between the main orchestrator process and the SessionEnd hook subprocess.
"""

import fcntl
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path


class State:
    def __init__(self, path: str):
        self.path = Path(path)

    def exists(self) -> bool:
        return self.path.exists()

    def read(self) -> dict:
        """Read state with shared lock."""
        with open(self.path, "r") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            try:
                data = json.load(f)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        return data

    def write(self, data: dict):
        """Write state atomically with exclusive lock.

        Acquires an exclusive lock on the target file during the write
        to prevent concurrent reads from seeing stale data.
        Writes to a temp file, fsyncs, then renames.
        """
        data["updated_at"] = datetime.now(timezone.utc).isoformat()

        # Acquire exclusive lock on the actual file (if it exists) to block readers
        lock_fd = None
        if self.path.exists():
            lock_fd = open(self.path, "r")
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX)

        try:
            tmp_fd, tmp_path = tempfile.mkstemp(
                dir=str(self.path.parent), suffix=".tmp"
            )
            try:
                with os.fdopen(tmp_fd, "w") as f:
                    json.dump(data, f, indent=2)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp_path, str(self.path))
            except Exception:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                raise
        finally:
            if lock_fd:
                fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
                lock_fd.close()

    def update_task(self, task_index: int, updates: dict) -> dict:
        """Atomically update a specific task and return the full state.

        Uses exclusive file lock so the orchestrator and hook handler
        never corrupt each other's writes.
        """
        with open(self.path, "r+") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                data = json.load(f)
                task = data["tasks"][task_index]
                task.update(updates)
                data["updated_at"] = datetime.now(timezone.utc).isoformat()

                f.seek(0)
                f.truncate()
                json.dump(data, f, indent=2)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        return data

    def advance_task(self, completed_index: int, result: dict) -> dict:
        """Mark a task completed, advance current_task_index, return state.

        This is the primary method used by hook_handler.py.
        Returns the updated state so the caller can decide what to do next.
        """
        with open(self.path, "r+") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                data = json.load(f)

                # Mark completed task
                task = data["tasks"][completed_index]
                task["status"] = "completed" if result.get("success", True) else "failed"
                task["session_id"] = result.get("session_id")
                task["transcript_path"] = result.get("transcript_path")
                task["result_summary"] = result.get("summary", "")
                task["files_modified"] = result.get("files_modified", [])
                task["cost_usd"] = result.get("cost_usd", 0)

                # Update cumulative cost
                data["total_cost_usd"] = data.get("total_cost_usd", 0) + task["cost_usd"]

                # Advance index
                next_index = completed_index + 1
                data["current_task_index"] = next_index

                # Check if all tasks in current batch are done
                current_batch = str(data["current_batch"])
                if current_batch in data.get("batches", {}):
                    batch = data["batches"][current_batch]
                    batch_indices = batch["task_indices"]
                    all_done = all(
                        data["tasks"][i]["status"] in ("completed", "failed")
                        for i in batch_indices
                    )
                    if all_done:
                        batch["status"] = "completed"

                data["updated_at"] = datetime.now(timezone.utc).isoformat()

                f.seek(0)
                f.truncate()
                json.dump(data, f, indent=2)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        return data

    def set_status(self, status: str, reason: str = None):
        """Set the overall orchestration status."""
        with open(self.path, "r+") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                data = json.load(f)
                data["status"] = status
                if reason:
                    data["abort_reason"] = reason
                data["updated_at"] = datetime.now(timezone.utc).isoformat()

                f.seek(0)
                f.truncate()
                json.dump(data, f, indent=2)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    @staticmethod
    def create_initial(
        path: str,
        project_dir: str,
        orchestrator_dir: str,
        tasks: list,
        config: dict,
        mode: str = "manual",
    ) -> "State":
        """Create a fresh state file."""
        now = datetime.now(timezone.utc).isoformat()

        # Build task entries
        task_entries = []
        for i, t in enumerate(tasks):
            task_entries.append(
                {
                    "index": i,
                    "title": t.get("title", f"Task {i + 1}"),
                    "file": t.get("file", f"tasks/{i + 1}.md"),
                    "status": "pending",
                    "session_id": None,
                    "transcript_path": None,
                    "result_summary": None,
                    "files_modified": [],
                    "cost_usd": 0,
                }
            )

        # First batch covers all tasks in manual mode
        batch_indices = list(range(len(task_entries)))

        data = {
            "version": 1,
            "status": "running",
            "mode": mode,
            "project_dir": str(project_dir),
            "orchestrator_dir": str(orchestrator_dir),
            "config": config,
            "current_batch": 1,
            "current_task_index": 0,
            "total_cost_usd": 0.0,
            "tasks": task_entries,
            "batches": {"1": {"task_indices": batch_indices, "status": "running"}},
            "started_at": now,
            "updated_at": now,
        }

        state = State(path)
        state.path.parent.mkdir(parents=True, exist_ok=True)
        state.write(data)
        return state
