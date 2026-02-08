"""
Tests for the logging module.

These tests ensure the logging module works correctly both with and without rich installed.
"""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


def test_logger_imports_without_rich():
    """Test that logger can be imported even if rich is not available."""
    # Mock rich as unavailable
    with patch.dict(
        sys.modules,
        {
            "rich": None,
            "rich.console": None,
            "rich.progress": None,
            "rich.table": None,
            "rich.panel": None,
            "rich.text": None,
        },
    ):
        # Reload the module to trigger the import error path
        import importlib

        from shoemaker_elves import logging as log_module

        importlib.reload(log_module)

        # Should be able to create a logger
        logger = log_module.Logger(enable_rich=True)
        assert logger is not None
        assert not logger.use_rich  # Should fall back to plain text


def test_logger_basic_functions_without_rich():
    """Test that basic logging functions work without rich."""
    from shoemaker_elves.logging import Logger

    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir)

        # Force disable rich for this test
        logger = Logger(log_dir=log_dir, enable_rich=False)

        # Should not crash
        logger.print("Test message")
        logger.error("Error message")
        logger.warning("Warning message")
        logger.success("Success message")
        logger.info("Info message")
        logger.header("Header")
        logger.section("Section")

        # Test table
        logger.table("Test Table", ["Col1", "Col2"], [["A", "B"], ["C", "D"]])

        # Test progress context manager
        with logger.progress("Test progress") as progress:
            task = progress.add_task("Task 1", total=100)
            progress.update(task, advance=10)

        # Test task summary
        tasks = [
            {"title": "Task 1", "status": "completed", "files_modified": ["file1.py"]},
            {"title": "Task 2", "status": "failed", "files_modified": []},
        ]
        logger.task_summary(tasks, 10.5)

        # Close logger
        logger.close()


def test_logger_creates_log_file():
    """Test that logger creates machine-readable log files."""
    from shoemaker_elves.logging import Logger

    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir)
        logger = Logger(log_dir=log_dir, enable_rich=False)

        # Write some log entries
        logger.error("Test error")
        logger.warning("Test warning")
        logger.success("Test success")
        logger.info("Test info")

        logger.close()

        # Check that log file was created
        log_file = log_dir / "run.log"
        assert log_file.exists()

        # Check that log entries are valid JSON Lines
        with open(log_file) as f:
            lines = f.readlines()

        assert len(lines) > 0

        # Parse and validate each line
        for line in lines:
            entry = json.loads(line.strip())
            assert "timestamp" in entry
            assert "event" in entry


def test_logger_log_event():
    """Test custom event logging."""
    from shoemaker_elves.logging import Logger

    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir)
        logger = Logger(log_dir=log_dir, enable_rich=False)

        # Log custom event
        logger.log_event("custom_event", {"key": "value", "number": 42})
        logger.close()

        # Check log file
        log_file = log_dir / "run.log"
        with open(log_file) as f:
            lines = f.readlines()

        # Find the custom event
        custom_events = [
            json.loads(line) for line in lines if json.loads(line).get("event") == "custom_event"
        ]
        assert len(custom_events) == 1
        assert custom_events[0]["key"] == "value"
        assert custom_events[0]["number"] == 42


def test_logger_without_log_dir():
    """Test that logger works without a log directory."""
    from shoemaker_elves.logging import Logger

    # Should not crash
    logger = Logger(log_dir=None, enable_rich=False)
    logger.info("Test message")
    logger.error("Error message")
    logger.close()


def test_is_rich_available():
    """Test the is_rich_available function."""
    from shoemaker_elves.logging import is_rich_available

    # Should return a boolean
    result = is_rich_available()
    assert isinstance(result, bool)


def test_get_logger_singleton():
    """Test that get_logger returns a singleton."""
    from shoemaker_elves.logging import get_logger

    logger1 = get_logger()
    logger2 = get_logger()

    # Should return the same instance
    assert logger1 is logger2


def test_logger_table_with_rich(monkeypatch):
    """Test table display with rich available."""
    from shoemaker_elves.logging import RICH_AVAILABLE, Logger

    if not RICH_AVAILABLE:
        pytest.skip("Rich not installed")

    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir)
        logger = Logger(log_dir=log_dir, enable_rich=True)

        # Should not crash with rich enabled
        logger.table("Test Table", ["Col1", "Col2"], [["A", "B"], ["C", "D"]])

        logger.close()


def test_logger_progress_with_rich(monkeypatch):
    """Test progress display with rich available."""
    from shoemaker_elves.logging import RICH_AVAILABLE, Logger

    if not RICH_AVAILABLE:
        pytest.skip("Rich not installed")

    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir)
        logger = Logger(log_dir=log_dir, enable_rich=True)

        # Should not crash with rich enabled
        with logger.progress("Test progress") as progress:
            task = progress.add_task("Task 1", total=100)
            progress.update(task, advance=10)

        logger.close()


def test_logger_task_summary_with_rich():
    """Test task summary display with rich available."""
    from shoemaker_elves.logging import RICH_AVAILABLE, Logger

    if not RICH_AVAILABLE:
        pytest.skip("Rich not installed")

    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir)
        logger = Logger(log_dir=log_dir, enable_rich=True)

        tasks = [
            {"title": "Task 1", "status": "completed", "files_modified": ["file1.py", "file2.py"]},
            {"title": "Task 2", "status": "running", "files_modified": ["file3.py"]},
            {"title": "Task 3", "status": "pending", "files_modified": []},
            {"title": "Task 4", "status": "failed", "files_modified": ["file4.py"]},
        ]

        # Should not crash with rich enabled
        logger.task_summary(tasks, 25.50)

        logger.close()


def test_logger_handles_log_file_errors():
    """Test that logger handles log file write errors gracefully."""
    from shoemaker_elves.logging import Logger

    # Use an invalid directory path
    logger = Logger(log_dir=Path("/invalid/directory/that/does/not/exist"), enable_rich=False)

    # Should not crash even if log file cannot be created
    logger.info("Test message")
    logger.error("Error message")
    logger.log_event("custom", {"data": "value"})
    logger.close()
