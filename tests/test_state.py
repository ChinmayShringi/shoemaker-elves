"""Tests for state management hardening."""

import json
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

from shoemaker_elves.state import State, StateCorruptionError


@pytest.fixture
def temp_state_path():
    """Create a temporary state file path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "state.json"


@pytest.fixture
def sample_state_data():
    """Sample state data for testing."""
    return {
        "version": 1,
        "status": "running",
        "mode": "manual",
        "project_dir": "/tmp/test",
        "orchestrator_dir": "/tmp/orch",
        "config": {},
        "current_batch": 1,
        "current_task_index": 0,
        "total_cost_usd": 0.0,
        "tasks": [
            {
                "index": 0,
                "title": "Task 1",
                "file": "tasks/1.md",
                "status": "pending",
                "session_id": None,
                "transcript_path": None,
                "result_summary": None,
                "files_modified": [],
                "cost_usd": 0,
                "started_at": None,
                "completed_at": None,
                "executions": [],
            },
            {
                "index": 1,
                "title": "Task 2",
                "file": "tasks/2.md",
                "status": "pending",
                "session_id": None,
                "transcript_path": None,
                "result_summary": None,
                "files_modified": [],
                "cost_usd": 0,
                "started_at": None,
                "completed_at": None,
                "executions": [],
            },
        ],
        "batches": {"1": {"task_indices": [0, 1], "status": "running"}},
        "started_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


class TestStateBasics:
    """Test basic state operations."""

    def test_create_initial_state(self, temp_state_path):
        """Test creating initial state file."""
        tasks = [
            {"title": "Task 1", "file": "tasks/1.md"},
            {"title": "Task 2", "file": "tasks/2.md"},
        ]

        state = State.create_initial(
            path=str(temp_state_path),
            project_dir="/tmp/project",
            orchestrator_dir="/tmp/orch",
            tasks=tasks,
            config={"agent_model": "claude-3-5-sonnet-20241022"},
        )

        assert state.exists()
        data = state.read()
        assert data["version"] == 1
        assert data["status"] == "running"
        assert len(data["tasks"]) == 2
        assert data["tasks"][0]["title"] == "Task 1"
        assert data["current_task_index"] == 0

    def test_read_write_state(self, temp_state_path, sample_state_data):
        """Test reading and writing state."""
        state = State(str(temp_state_path))
        state.write(sample_state_data)

        read_data = state.read()
        assert read_data["version"] == sample_state_data["version"]
        assert read_data["status"] == sample_state_data["status"]
        assert len(read_data["tasks"]) == len(sample_state_data["tasks"])

    def test_update_task(self, temp_state_path, sample_state_data):
        """Test updating a specific task."""
        state = State(str(temp_state_path))
        state.write(sample_state_data)

        updated = state.update_task(0, {"status": "running", "started_at": "2026-02-04T10:00:00Z"})

        assert updated["tasks"][0]["status"] == "running"
        assert updated["tasks"][0]["started_at"] == "2026-02-04T10:00:00Z"

    def test_mark_task_running(self, temp_state_path, sample_state_data):
        """Test marking task as running with timestamp."""
        state = State(str(temp_state_path))
        state.write(sample_state_data)

        updated = state.mark_task_running(0)

        assert updated["tasks"][0]["status"] == "running"
        assert updated["tasks"][0]["started_at"] is not None
        # Verify timestamp is recent (within last 5 seconds)
        started_at = datetime.fromisoformat(updated["tasks"][0]["started_at"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        assert (now - started_at).total_seconds() < 5


class TestStateIdempotency:
    """Test idempotent behavior of state operations."""

    def test_advance_task_idempotency(self, temp_state_path, sample_state_data):
        """Test that advancing the same task twice with same session doesn't duplicate."""
        state = State(str(temp_state_path))
        state.write(sample_state_data)

        result1 = {
            "success": True,
            "session_id": "test-session-123",
            "summary": "Task completed",
            "files_modified": ["file1.py"],
            "cost_usd": 0.5,
        }

        # First advance
        state1 = state.advance_task(0, result1)
        assert state1["tasks"][0]["status"] == "completed"
        assert state1["tasks"][0]["session_id"] == "test-session-123"
        assert len(state1["tasks"][0]["executions"]) == 1
        assert state1["current_task_index"] == 1

        # Second advance with same session (simulating double hook call)
        state2 = state.advance_task(0, result1)
        assert state2["tasks"][0]["status"] == "completed"
        assert state2["tasks"][0]["session_id"] == "test-session-123"
        # Should still be 1 execution (idempotent)
        assert len(state2["tasks"][0]["executions"]) == 1
        # Index should not advance again
        assert state2["current_task_index"] == 1

    def test_advance_task_different_session(self, temp_state_path, sample_state_data):
        """Test that advancing with different session ID adds new execution."""
        state = State(str(temp_state_path))
        state.write(sample_state_data)

        result1 = {
            "success": True,
            "session_id": "session-1",
            "summary": "First attempt",
            "cost_usd": 0.5,
        }

        # First advance
        state1 = state.advance_task(0, result1)
        assert len(state1["tasks"][0]["executions"]) == 1

        # Manually reset task to pending (simulating retry)
        state.update_task(0, {"status": "pending"})

        # Second advance with different session
        result2 = {
            "success": True,
            "session_id": "session-2",
            "summary": "Second attempt",
            "cost_usd": 0.3,
        }

        state2 = state.advance_task(0, result2)
        assert len(state2["tasks"][0]["executions"]) == 2
        assert state2["tasks"][0]["executions"][0]["session_id"] == "session-1"
        assert state2["tasks"][0]["executions"][1]["session_id"] == "session-2"


class TestStateConcurrency:
    """Test concurrent access to state."""

    def test_concurrent_reads(self, temp_state_path, sample_state_data):
        """Test multiple threads reading state simultaneously."""
        state = State(str(temp_state_path))
        state.write(sample_state_data)

        results = []
        errors = []

        def read_state():
            try:
                data = state.read()
                results.append(data)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=read_state) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(results) == 10
        # All reads should return consistent data
        assert all(r["version"] == 1 for r in results)

    def test_concurrent_writes(self, temp_state_path, sample_state_data):
        """Test multiple threads writing state simultaneously."""
        state = State(str(temp_state_path))
        state.write(sample_state_data)

        errors = []

        def update_state(task_index, status):
            try:
                state.update_task(task_index, {"status": status})
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=update_state, args=(0, f"running-{i}"))
            for i in range(5)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        # Verify state is still valid
        data = state.read()
        assert "version" in data
        assert "tasks" in data


class TestStateCorruptionRecovery:
    """Test state corruption detection and recovery."""

    def test_corrupted_json_recovery(self, temp_state_path, sample_state_data):
        """Test recovery from corrupted JSON."""
        state = State(str(temp_state_path))
        state.write(sample_state_data)

        # Corrupt the state file
        with open(temp_state_path, "w") as f:
            f.write("{ invalid json")

        # Should recover from backup
        data = state.read()
        assert data["version"] == 1
        assert data["status"] == "running"

    def test_missing_required_fields_recovery(self, temp_state_path):
        """Test recovery from state with missing required fields."""
        state = State(str(temp_state_path))

        # Write valid state first (creates backup)
        valid_data = {
            "version": 1,
            "status": "running",
            "tasks": [],
            "current_task_index": 0,
        }
        state.write(valid_data)

        # Ensure backup was created
        assert state.backup_path.exists()

        # Corrupt the main file by directly overwriting it
        # (simulating a crash during write)
        with open(temp_state_path, "w") as f:
            json.dump({"invalid": "data"}, f)

        # Should recover from backup
        data = state.read()
        assert data["version"] == 1
        assert data["status"] == "running"

    def test_no_backup_corruption_fails(self, temp_state_path):
        """Test that corruption without backup raises error."""
        state = State(str(temp_state_path))

        # Write corrupted state without creating valid backup first
        with open(temp_state_path, "w") as f:
            f.write("{ corrupt }")

        with pytest.raises(StateCorruptionError):
            state.read()


class TestAtomicWrites:
    """Test atomic write behavior."""

    def test_write_creates_backup(self, temp_state_path, sample_state_data):
        """Test that writes create backups."""
        state = State(str(temp_state_path))
        state.write(sample_state_data)

        assert state.backup_path.exists()

    def test_partial_write_cleanup(self, temp_state_path, sample_state_data):
        """Test that failed writes clean up temp files."""
        state = State(str(temp_state_path))

        # Create a state that will fail JSON serialization
        class NonSerializable:
            pass

        bad_data = sample_state_data.copy()
        bad_data["bad_field"] = NonSerializable()

        try:
            state.write(bad_data)
        except TypeError:
            pass  # Expected

        # Check no temp files left behind
        temp_files = list(temp_state_path.parent.glob(".state_*.tmp"))
        assert len(temp_files) == 0

    def test_atomic_replace(self, temp_state_path, sample_state_data):
        """Test that writes are atomic (reader never sees partial write)."""
        state = State(str(temp_state_path))
        state.write(sample_state_data)

        errors = []
        reads_completed = []

        def continuous_reader():
            """Continuously read state."""
            try:
                for _ in range(50):
                    data = state.read()
                    # All reads should see valid state
                    assert "version" in data
                    assert "tasks" in data
                    reads_completed.append(True)
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)

        def continuous_writer():
            """Continuously write state."""
            try:
                for i in range(20):
                    data = sample_state_data.copy()
                    data["current_task_index"] = i
                    state.write(data)
                    time.sleep(0.002)
            except Exception as e:
                errors.append(e)

        reader_threads = [threading.Thread(target=continuous_reader) for _ in range(3)]
        writer_thread = threading.Thread(target=continuous_writer)

        for t in reader_threads:
            t.start()
        writer_thread.start()

        writer_thread.join()
        for t in reader_threads:
            t.join()

        assert len(errors) == 0
        assert len(reads_completed) > 0


class TestSetStatus:
    """Test status management."""

    def test_set_status(self, temp_state_path, sample_state_data):
        """Test setting orchestration status."""
        state = State(str(temp_state_path))
        state.write(sample_state_data)

        state.set_status("completed", "All tasks done")

        data = state.read()
        assert data["status"] == "completed"
        assert data["abort_reason"] == "All tasks done"

    def test_set_status_without_reason(self, temp_state_path, sample_state_data):
        """Test setting status without reason."""
        state = State(str(temp_state_path))
        state.write(sample_state_data)

        state.set_status("aborted")

        data = state.read()
        assert data["status"] == "aborted"
        assert "abort_reason" not in data or data.get("abort_reason") is None
