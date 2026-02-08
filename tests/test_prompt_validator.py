"""
Unit tests for the prompt validator.

Tests validation of task planning and review responses.
"""

import pytest

from shoemaker_elves.prompt_validator import (
    PromptValidator,
    ValidationError,
)

# ─────────────────────────────────────────────────────────────
# Task Validation Tests
# ─────────────────────────────────────────────────────────────


def test_validate_task_valid():
    """Test validation of a valid task."""
    task = {
        "id": "task-1",
        "title": "Implement feature",
        "summary": "Add a new feature",
        "prompt": "Create a feature that does X",
        "steps": ["Step 1", "Step 2"],
        "files": ["src/feature.py"],
        "acceptance_checks": ["Run tests"],
        "risks": ["Risk 1"],
        "constraints": ["Constraint 1"],
    }

    errors = PromptValidator.validate_task(task)
    assert errors == []


def test_validate_task_minimal():
    """Test validation of a minimal valid task."""
    task = {
        "title": "Simple task",
        "prompt": "Do something",
    }

    errors = PromptValidator.validate_task(task)
    assert errors == []


def test_validate_task_missing_required_fields():
    """Test validation fails for missing required fields."""
    task = {
        "summary": "Has summary but no title",
    }

    errors = PromptValidator.validate_task(task)
    assert any("missing required 'title' field" in err for err in errors)
    assert any("missing required 'prompt' field" in err for err in errors)


def test_validate_task_empty_required_fields():
    """Test validation fails for empty required fields."""
    task = {
        "title": "   ",
        "prompt": "",
    }

    errors = PromptValidator.validate_task(task)
    assert any("'title' cannot be empty" in err for err in errors)
    assert any("'prompt' cannot be empty" in err for err in errors)


def test_validate_task_wrong_types():
    """Test validation fails for wrong field types."""
    task = {
        "title": 123,  # Should be string
        "prompt": "Valid prompt",
        "steps": "Should be a list",  # Should be list
        "files": {"file1": "path"},  # Should be list
    }

    errors = PromptValidator.validate_task(task)
    assert any("'title' must be a string" in err for err in errors)
    assert any("'steps' should be list" in err for err in errors)
    assert any("'files' should be list" in err for err in errors)


def test_validate_task_list_contents_wrong_type():
    """Test validation fails for non-string list items."""
    task = {
        "title": "Task",
        "prompt": "Prompt",
        "steps": ["Step 1", 123, "Step 3"],  # 123 is not a string
        "risks": [None, "Risk"],  # None is not a string
    }

    errors = PromptValidator.validate_task(task)
    assert any("steps[1] must be a string" in err for err in errors)
    assert any("risks[0] must be a string" in err for err in errors)


def test_validate_task_title_too_long():
    """Test validation fails for overly long titles."""
    task = {
        "title": "A" * 101,  # Over 100 chars
        "prompt": "Valid prompt",
    }

    errors = PromptValidator.validate_task(task)
    assert any("Title too long" in err for err in errors)


def test_validate_task_not_dict():
    """Test validation fails when task is not a dict."""
    task = "not a dict"

    errors = PromptValidator.validate_task(task)
    assert any("Must be a dictionary" in err for err in errors)


# ─────────────────────────────────────────────────────────────
# Planning Response Validation Tests
# ─────────────────────────────────────────────────────────────


def test_validate_planning_response_valid():
    """Test validation of a valid planning response."""
    response = {
        "tasks": [
            {
                "id": "task-1",
                "title": "Task 1",
                "prompt": "Do task 1",
                "summary": "Summary 1",
                "steps": ["S1"],
                "files": ["f1.py"],
                "acceptance_checks": ["Check 1"],
                "risks": ["Risk 1"],
                "constraints": ["Constraint 1"],
            },
            {
                "id": "task-2",
                "title": "Task 2",
                "prompt": "Do task 2",
            },
        ],
        "batch_reasoning": "These tasks make sense",
    }

    errors = PromptValidator.validate_planning_response(response, batch_size=5)
    assert errors == []


def test_validate_planning_response_empty_tasks():
    """Test validation allows empty tasks list (project complete)."""
    response = {
        "tasks": [],
        "batch_reasoning": "Project is complete",
    }

    errors = PromptValidator.validate_planning_response(response, batch_size=5)
    assert errors == []


def test_validate_planning_response_missing_tasks():
    """Test validation fails when tasks field is missing."""
    response = {
        "batch_reasoning": "Oops, forgot tasks",
    }

    errors = PromptValidator.validate_planning_response(response, batch_size=5)
    assert any("missing 'tasks' field" in err for err in errors)


def test_validate_planning_response_tasks_not_list():
    """Test validation fails when tasks is not a list."""
    response = {
        "tasks": "should be a list",
    }

    errors = PromptValidator.validate_planning_response(response, batch_size=5)
    assert any("'tasks' field must be a list" in err for err in errors)


def test_validate_planning_response_batch_size_exceeded():
    """Test validation fails when batch size is exceeded."""
    response = {
        "tasks": [{"title": f"Task {i}", "prompt": f"Do task {i}"} for i in range(11)],
    }

    errors = PromptValidator.validate_planning_response(response, batch_size=10)
    assert any("Batch size exceeded" in err for err in errors)


def test_validate_planning_response_invalid_task():
    """Test validation fails when a task is invalid."""
    response = {
        "tasks": [
            {"title": "Valid", "prompt": "Valid"},
            {"title": "Missing prompt"},  # Missing required prompt
        ],
    }

    errors = PromptValidator.validate_planning_response(response, batch_size=5)
    assert any("Task 1" in err and "prompt" in err for err in errors)


def test_validate_planning_response_not_dict():
    """Test validation fails when response is not a dict."""
    response = ["not", "a", "dict"]

    errors = PromptValidator.validate_planning_response(response, batch_size=5)
    assert any("must be a JSON object" in err for err in errors)


# ─────────────────────────────────────────────────────────────
# Review Response Validation Tests
# ─────────────────────────────────────────────────────────────


def test_validate_review_response_valid():
    """Test validation of a valid review response."""
    response = {
        "cumulative_summary": "All work completed so far",
        "batch_assessment": "This batch went well",
        "issues": ["Issue 1", "Issue 2"],
        "project_complete": False,
        "completion_percentage": 75,
        "recommendations": "Continue with next batch",
        "next_tasks": [
            {
                "title": "Fix bug",
                "summary": "Fix the critical bug",
                "priority": "high",
                "reason": "Blocking users",
            }
        ],
    }

    errors = PromptValidator.validate_review_response(response)
    assert errors == []


def test_validate_review_response_minimal():
    """Test validation of minimal valid review response."""
    response = {
        "cumulative_summary": "Summary",
        "batch_assessment": "Assessment",
        "issues": [],
        "project_complete": False,
        "completion_percentage": 50,
    }

    errors = PromptValidator.validate_review_response(response)
    assert errors == []


def test_validate_review_response_missing_required_fields():
    """Test validation fails for missing required fields."""
    response = {
        "cumulative_summary": "Summary",
        # Missing batch_assessment
        "issues": [],
    }

    errors = PromptValidator.validate_review_response(response)
    assert any("missing required field 'batch_assessment'" in err for err in errors)


def test_validate_review_response_empty_required_fields():
    """Test validation fails for empty required string fields."""
    response = {
        "cumulative_summary": "   ",
        "batch_assessment": "",
        "issues": [],
        "project_complete": False,
        "completion_percentage": 0,
    }

    errors = PromptValidator.validate_review_response(response)
    assert any("'cumulative_summary' cannot be empty" in err for err in errors)
    assert any("'batch_assessment' cannot be empty" in err for err in errors)


def test_validate_review_response_wrong_types():
    """Test validation fails for wrong field types."""
    response = {
        "cumulative_summary": "Summary",
        "batch_assessment": "Assessment",
        "issues": "should be a list",  # Wrong type
        "project_complete": "yes",  # Should be boolean
        "completion_percentage": "50%",  # Should be number
    }

    errors = PromptValidator.validate_review_response(response)
    assert any("'issues' must be a list" in err for err in errors)
    assert any("'project_complete' must be a boolean" in err for err in errors)
    assert any("'completion_percentage' must be a number" in err for err in errors)


def test_validate_review_response_completion_percentage_out_of_range():
    """Test validation fails for completion_percentage out of range."""
    response = {
        "cumulative_summary": "Summary",
        "batch_assessment": "Assessment",
        "issues": [],
        "project_complete": False,
        "completion_percentage": 150,  # Over 100
    }

    errors = PromptValidator.validate_review_response(response)
    assert any("must be between 0 and 100" in err for err in errors)


def test_validate_review_response_invalid_next_task():
    """Test validation fails for invalid next_tasks."""
    response = {
        "cumulative_summary": "Summary",
        "batch_assessment": "Assessment",
        "issues": [],
        "project_complete": False,
        "completion_percentage": 50,
        "next_tasks": [
            {
                "title": "Fix bug",
                "summary": "Fix it",
                # Missing priority and reason
            }
        ],
    }

    errors = PromptValidator.validate_review_response(response)
    assert any("next_tasks[0]" in err and "priority" in err for err in errors)
    assert any("next_tasks[0]" in err and "reason" in err for err in errors)


def test_validate_review_response_invalid_priority():
    """Test validation fails for invalid priority values."""
    response = {
        "cumulative_summary": "Summary",
        "batch_assessment": "Assessment",
        "issues": [],
        "project_complete": False,
        "completion_percentage": 50,
        "next_tasks": [
            {
                "title": "Task",
                "summary": "Summary",
                "priority": "urgent",  # Invalid, should be high/medium/low
                "reason": "Reason",
            }
        ],
    }

    errors = PromptValidator.validate_review_response(response)
    assert any("priority must be 'high', 'medium', or 'low'" in err for err in errors)


# ─────────────────────────────────────────────────────────────
# validate_and_raise Tests
# ─────────────────────────────────────────────────────────────


def test_validate_and_raise_valid_planning():
    """Test validate_and_raise does not raise for valid planning response."""
    response = {
        "tasks": [{"title": "Task", "prompt": "Prompt"}],
    }

    # Should not raise
    PromptValidator.validate_and_raise(response, operation="plan_batch", batch_size=5)


def test_validate_and_raise_invalid_planning():
    """Test validate_and_raise raises ValidationError for invalid planning."""
    response = {
        "tasks": "not a list",
    }

    with pytest.raises(ValidationError) as exc_info:
        PromptValidator.validate_and_raise(response, operation="plan_batch", batch_size=5)

    assert "plan_batch" in str(exc_info.value)


def test_validate_and_raise_valid_review():
    """Test validate_and_raise does not raise for valid review response."""
    response = {
        "cumulative_summary": "Summary",
        "batch_assessment": "Assessment",
        "issues": [],
        "project_complete": False,
        "completion_percentage": 50,
    }

    # Should not raise
    PromptValidator.validate_and_raise(response, operation="review_batch")


def test_validate_and_raise_invalid_review():
    """Test validate_and_raise raises ValidationError for invalid review."""
    response = {
        "cumulative_summary": "Summary",
        # Missing batch_assessment
    }

    with pytest.raises(ValidationError) as exc_info:
        PromptValidator.validate_and_raise(response, operation="review_batch")

    assert "review_batch" in str(exc_info.value)


def test_validate_and_raise_unknown_operation():
    """Test validate_and_raise raises ValueError for unknown operation."""
    response = {"data": "anything"}

    with pytest.raises(ValueError) as exc_info:
        PromptValidator.validate_and_raise(response, operation="unknown_op")

    assert "Unknown operation" in str(exc_info.value)
