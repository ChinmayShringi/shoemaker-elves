"""
State management for the GPT Agent Orchestrator.
Uses cross-platform file locking (filelock) and atomic writes for safe concurrent access
between the main orchestrator process and the SessionEnd hook subprocess.

Features:
- Cross-platform file locking (Windows, macOS, Linux)
- Atomic writes with temp file + rename
- State file validation and corruption recovery
- Backup mechanism for safety
"""

import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    from filelock import FileLock
except ImportError:
    raise ImportError(
        "filelock is required for state management. "
        "Install it with: pip install filelock"
    )


class StateError(Exception):
    """Base exception for state management errors."""
    pass


class StateCorruptionError(StateError):
    """Raised when state file is corrupted."""
    pass


class State:
    """Thread-safe and crash-safe state management with automatic backup."""

    def __init__(self, path: str):
        self.path = Path(path)
        self.lock_path = Path(str(self.path) + ".lock")
        self.backup_path = Path(str(self.path) + ".backup")
        self._lock = FileLock(str(self.lock_path), timeout=10)

    def exists(self) -> bool:
        """Check if state file exists."""
        return self.path.exists()

    def _validate_state(self, data: dict) -> bool:
        """Validate state structure."""
        required_keys = ["version", "status", "tasks", "current_task_index"]
        return all(key in data for key in required_keys)

    def _create_backup(self):
        """Create a backup of the current state file."""
        if self.path.exists():
            try:
                shutil.copy2(self.path, self.backup_path)
            except OSError:
                pass  # Backup is optional, don't fail

    def _recover_from_backup(self) -> Optional[dict]:
        """Attempt to recover state from backup file."""
        if not self.backup_path.exists():
            return None

        try:
            with open(self.backup_path, "r") as f:
                data = json.load(f)
                if self._validate_state(data):
                    return data
        except (json.JSONDecodeError, OSError):
            pass

        return None

    def read(self) -> dict:
        """Read state with shared lock and corruption recovery."""
        with self._lock:
            try:
                with open(self.path, "r") as f:
                    data = json.load(f)
                    if not self._validate_state(data):
                        raise StateCorruptionError("Invalid state structure")
                    return data
            except (json.JSONDecodeError, OSError, StateCorruptionError) as e:
                # Try to recover from backup
                backup_data = self._recover_from_backup()
                if backup_data:
                    # Restore from backup
                    self._atomic_write(backup_data)
                    return backup_data
                raise StateCorruptionError(f"State file corrupted and no valid backup: {e}")

    def _atomic_write(self, data: dict):
        """Atomically write data to state file using temp file + rename.

        This ensures that readers never see a partially written file.
        """
        # Ensure parent directory exists
        self.path.parent.mkdir(parents=True, exist_ok=True)

        # Create backup before write (only if file exists)
        if self.path.exists():
            self._create_backup()

        # Write to temp file in same directory (required for atomic rename)
        tmp_fd, tmp_path = tempfile.mkstemp(
            dir=str(self.path.parent),
            prefix=".state_",
            suffix=".tmp"
        )

        try:
            with os.fdopen(tmp_fd, "w") as f:
                json.dump(data, f, indent=2)
                f.flush()
                os.fsync(f.fileno())  # Ensure data is written to disk

            # Atomic rename (POSIX guarantees atomicity)
            os.replace(tmp_path, str(self.path))

            # Create backup after successful write for next time
            self._create_backup()
        except Exception:
            # Clean up temp file on error
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def write(self, data: dict):
        """Write state atomically with exclusive lock.

        Acquires an exclusive lock to prevent concurrent reads/writes.
        Updates timestamp automatically.
        """
        data["updated_at"] = datetime.now(timezone.utc).isoformat()

        with self._lock:
            self._atomic_write(data)

    def update_task(self, task_index: int, updates: dict) -> dict:
        """Atomically update a specific task and return the full state.

        Uses exclusive file lock so the orchestrator and hook handler
        never corrupt each other's writes.
        """
        with self._lock:
            data = self.read()
            task = data["tasks"][task_index]
            task.update(updates)
            data["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._atomic_write(data)
            return data

    def advance_task(self, completed_index: int, result: dict) -> dict:
        """Mark a task completed, advance current_task_index, return state.

        This is the primary method used by hook_handler.py.
        Returns the updated state so the caller can decide what to do next.

        Idempotency: If the task is already marked as completed for this session,
        this operation is skipped to prevent duplicate processing.
        """
        with self._lock:
            data = self.read()
            task = data["tasks"][completed_index]

            # Idempotency check: Skip if task already completed for this session
            if task["status"] in ("completed", "failed"):
                session_id = result.get("session_id")
                if task.get("session_id") == session_id:
                    # Task already processed for this session, skip
                    return data

            # Mark completed task
            task["status"] = "completed" if result.get("success", True) else "failed"
            task["session_id"] = result.get("session_id")
            task["transcript_path"] = result.get("transcript_path")
            task["result_summary"] = result.get("summary", "")
            task["files_modified"] = result.get("files_modified", [])
            task["cost_usd"] = result.get("cost_usd", 0)
            task["completed_at"] = datetime.now(timezone.utc).isoformat()

            # Add execution marker for idempotency
            if "executions" not in task:
                task["executions"] = []
            task["executions"].append({
                "session_id": result.get("session_id"),
                "completed_at": task["completed_at"],
                "success": result.get("success", True)
            })

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
            self._atomic_write(data)
            return data

    def set_status(self, status: str, reason: str = None):
        """Set the overall orchestration status."""
        with self._lock:
            data = self.read()
            data["status"] = status
            if reason:
                data["abort_reason"] = reason
            data["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._atomic_write(data)

    def mark_task_running(self, task_index: int) -> dict:
        """Mark a task as running with timestamp for stall detection."""
        with self._lock:
            data = self.read()
            task = data["tasks"][task_index]
            task["status"] = "running"
            task["started_at"] = datetime.now(timezone.utc).isoformat()
            data["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._atomic_write(data)
            return data

    @staticmethod
    def create_initial(
        path: str,
        project_dir: str,
        orchestrator_dir: str,
        tasks: list,
        config: dict,
        mode: str = "manual",
    ) -> "State":
        """Create a fresh state file with atomic write."""
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
                    "started_at": None,
                    "completed_at": None,
                    "executions": [],
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
        state.write(data)
        return state
