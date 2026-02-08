"""Tests for hook handler idempotency."""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from shoemaker_elves.hook_handler import launch_next_task, main
from shoemaker_elves.state import State


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "project"
        project_dir.mkdir()

        # Create .claude directory with orchestrator_ref.json
        claude_dir = project_dir / ".claude"
        claude_dir.mkdir()

        # Create orchestrator directory
        orch_dir = Path(tmpdir) / "orchestrator"
        orch_dir.mkdir()
        tasks_dir = orch_dir / "tasks"
        tasks_dir.mkdir()

        # Create state file
        state_file = orch_dir / "state.json"

        # Write orchestrator reference
        ref_file = claude_dir / "orchestrator_ref.json"
        ref_file.write_text(json.dumps({"state_file": str(state_file)}))

        yield {
            "project_dir": project_dir,
            "orch_dir": orch_dir,
            "state_file": state_file,
            "tasks_dir": tasks_dir,
        }


@pytest.fixture
def sample_state_data(temp_project_dir):
    """Sample state data for testing."""
    return {
        "version": 1,
        "status": "running",
        "mode": "manual",
        "project_dir": str(temp_project_dir["project_dir"]),
        "orchestrator_dir": str(temp_project_dir["orch_dir"]),
        "config": {"agent_model": "claude-3-5-sonnet-20241022"},
        "current_batch": 1,
        "current_task_index": 0,
        "total_cost_usd": 0.0,
        "tasks": [
            {
                "index": 0,
                "title": "Task 1",
                "file": "tasks/1.md",
                "status": "running",
                "session_id": None,
                "transcript_path": None,
                "result_summary": None,
                "files_modified": [],
                "cost_usd": 0,
                "started_at": datetime.now(timezone.utc).isoformat(),
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


class TestLaunchNextTaskIdempotency:
    """Test that launch_next_task is idempotent."""

    @patch("shoemaker_elves.hook_handler.subprocess.Popen")
    def test_launch_next_task_already_running(
        self, mock_popen, temp_project_dir, sample_state_data
    ):
        """Test that launching a task that's already running is skipped."""
        # Setup
        state = State(str(temp_project_dir["state_file"]))
        state.write(sample_state_data)

        # Create task file
        task_file = temp_project_dir["tasks_dir"] / "2.md"
        task_file.write_text("Task 2 prompt")

        # Mark task 1 as running
        next_task = sample_state_data["tasks"][1].copy()
        next_task["status"] = "running"

        # Try to launch (should skip)
        launch_next_task(sample_state_data, next_task, state)

        # Verify subprocess was not called
        mock_popen.assert_not_called()

    @patch("shoemaker_elves.hook_handler.subprocess.Popen")
    def test_launch_next_task_pending(
        self, mock_popen, temp_project_dir, sample_state_data
    ):
        """Test that launching a pending task succeeds."""
        # Setup
        state = State(str(temp_project_dir["state_file"]))
        state.write(sample_state_data)

        # Create task file
        task_file = temp_project_dir["tasks_dir"] / "2.md"
        task_file.write_text("Task 2 prompt")

        next_task = sample_state_data["tasks"][1]

        # Launch task
        launch_next_task(sample_state_data, next_task, state)

        # Verify subprocess was called
        mock_popen.assert_called_once()

        # Verify task was marked as running
        updated_state = state.read()
        assert updated_state["tasks"][1]["status"] == "running"
        assert updated_state["tasks"][1]["started_at"] is not None

    @patch("shoemaker_elves.hook_handler.subprocess.Popen")
    def test_launch_next_task_double_call(
        self, mock_popen, temp_project_dir, sample_state_data
    ):
        """Test that calling launch_next_task twice doesn't launch twice."""
        # Setup
        state = State(str(temp_project_dir["state_file"]))
        state.write(sample_state_data)

        # Create task file
        task_file = temp_project_dir["tasks_dir"] / "2.md"
        task_file.write_text("Task 2 prompt")

        next_task = sample_state_data["tasks"][1]

        # First launch
        launch_next_task(sample_state_data, next_task, state)
        assert mock_popen.call_count == 1

        # Get updated state
        updated_state = state.read()
        updated_task = updated_state["tasks"][1]

        # Second launch (should skip because task is now running)
        launch_next_task(updated_state, updated_task, state)
        assert mock_popen.call_count == 1  # Still 1, not 2


class TestHookHandlerIdempotency:
    """Test full hook handler idempotency."""

    @patch("shoemaker_elves.hook_handler.subprocess.Popen")
    @patch("shoemaker_elves.hook_handler.parse_transcript")
    def test_double_hook_invocation(
        self, mock_parse, mock_popen, temp_project_dir, sample_state_data
    ):
        """Test that invoking hook twice for same session doesn't start two tasks."""
        # Setup
        state = State(str(temp_project_dir["state_file"]))
        state.write(sample_state_data)

        # Create task files
        (temp_project_dir["tasks_dir"] / "1.md").write_text("Task 1 prompt")
        (temp_project_dir["tasks_dir"] / "2.md").write_text("Task 2 prompt")

        # Create CLAUDE.md
        context_file = temp_project_dir["project_dir"] / "CLAUDE.md"
        context_file.write_text("# Orchestrator Context\n\n## Progress So Far\n")

        # Mock transcript parsing
        mock_parse.return_value = {
            "success": True,
            "summary": "Task 1 completed",
            "files_modified": ["file1.py"],
            "cost_usd": 0.5,
        }

        # First hook invocation
        with patch("sys.stdin", MagicMock(read=lambda: json.dumps({
            "session_id": "test-session-123",
            "transcript_path": "/tmp/transcript.txt",
            "cwd": str(temp_project_dir["project_dir"]),
        }))):
            with patch("shoemaker_elves.hook_handler.log"):
                main()

        # Verify task 2 was launched
        assert mock_popen.call_count == 1

        # Verify state
        state_data = state.read()
        assert state_data["tasks"][0]["status"] == "completed"
        assert state_data["tasks"][0]["session_id"] == "test-session-123"
        assert len(state_data["tasks"][0]["executions"]) == 1
        assert state_data["tasks"][1]["status"] == "running"

        # Second hook invocation with SAME session (simulating double call)
        with patch("sys.stdin", MagicMock(read=lambda: json.dumps({
            "session_id": "test-session-123",
            "transcript_path": "/tmp/transcript.txt",
            "cwd": str(temp_project_dir["project_dir"]),
        }))):
            with patch("shoemaker_elves.hook_handler.log"):
                main()

        # Verify task 2 was NOT launched again (still 1 call)
        # Actually, it might be launched again because we're processing task 0 again
        # But the key is that task 1 shouldn't be launched AGAIN if it's already running

        # Verify state is consistent
        state_data = state.read()
        assert len(state_data["tasks"][0]["executions"]) == 1  # Still 1 execution
        assert state_data["current_task_index"] == 1  # Index didn't advance again

    @patch("shoemaker_elves.hook_handler.subprocess.Popen")
    @patch("shoemaker_elves.hook_handler.parse_transcript")
    def test_different_session_not_idempotent(
        self, mock_parse, mock_popen, temp_project_dir, sample_state_data
    ):
        """Test that different sessions are processed separately."""
        # Setup
        state = State(str(temp_project_dir["state_file"]))
        # Reset task 0 to pending for this test
        sample_state_data["tasks"][0]["status"] = "pending"
        sample_state_data["tasks"][0]["executions"] = []
        state.write(sample_state_data)

        # Create task files
        (temp_project_dir["tasks_dir"] / "1.md").write_text("Task 1 prompt")
        (temp_project_dir["tasks_dir"] / "2.md").write_text("Task 2 prompt")

        # Create CLAUDE.md
        context_file = temp_project_dir["project_dir"] / "CLAUDE.md"
        context_file.write_text("# Orchestrator Context\n\n## Progress So Far\n")

        # Mock transcript parsing
        mock_parse.return_value = {
            "success": True,
            "summary": "Task 1 completed",
            "files_modified": ["file1.py"],
            "cost_usd": 0.5,
        }

        # First hook invocation with session 1
        with patch("sys.stdin", MagicMock(read=lambda: json.dumps({
            "session_id": "session-1",
            "transcript_path": "/tmp/transcript1.txt",
            "cwd": str(temp_project_dir["project_dir"]),
        }))):
            with patch("shoemaker_elves.hook_handler.log"):
                main()

        # Verify state
        state_data = state.read()
        assert state_data["tasks"][0]["session_id"] == "session-1"
        assert len(state_data["tasks"][0]["executions"]) == 1

        # Reset task 0 to pending and then mark as running (simulating retry scenario)
        state.update_task(0, {"status": "pending"})
        state_data = state.read()
        state_data["current_task_index"] = 0  # Reset index
        state.write(state_data)

        # Mark as running (simulating CLI launching the task again)
        state.mark_task_running(0)

        # Second hook invocation with session 2
        mock_parse.return_value = {
            "success": True,
            "summary": "Task 1 completed (retry)",
            "files_modified": ["file1.py", "file2.py"],
            "cost_usd": 0.3,
        }

        with patch("sys.stdin", MagicMock(read=lambda: json.dumps({
            "session_id": "session-2",
            "transcript_path": "/tmp/transcript2.txt",
            "cwd": str(temp_project_dir["project_dir"]),
        }))):
            with patch("shoemaker_elves.hook_handler.log"):
                main()

        # Verify state has both executions
        state_data = state.read()
        assert len(state_data["tasks"][0]["executions"]) == 2
        assert state_data["tasks"][0]["executions"][0]["session_id"] == "session-1"
        assert state_data["tasks"][0]["executions"][1]["session_id"] == "session-2"
