"""
Unit tests for planner data types.

Tests TaskSpec and ReviewSpec serialization and deserialization.
"""


from shoemaker_elves.planners.types import ReviewSpec, TaskSpec

# ─────────────────────────────────────────────────────────────
# TaskSpec Tests
# ─────────────────────────────────────────────────────────────


def test_task_spec_creation():
    """Test creating a TaskSpec."""
    task = TaskSpec(
        title="Implement feature X",
        prompt="Create a new feature that does X, Y, and Z.",
    )

    assert task.title == "Implement feature X"
    assert task.prompt == "Create a new feature that does X, Y, and Z."


def test_task_spec_to_dict():
    """Test converting TaskSpec to dictionary."""
    task = TaskSpec(
        title="Test task",
        prompt="Test prompt",
    )

    result = task.to_dict()

    assert result == {
        "title": "Test task",
        "prompt": "Test prompt",
        "id": None,
        "summary": "",
        "steps": [],
        "files": [],
        "acceptance_checks": [],
        "risks": [],
        "constraints": [],
    }


def test_task_spec_from_dict():
    """Test creating TaskSpec from dictionary."""
    data = {
        "title": "Test task",
        "prompt": "Test prompt",
    }

    task = TaskSpec.from_dict(data)

    assert task.title == "Test task"
    assert task.prompt == "Test prompt"


def test_task_spec_from_dict_missing_fields():
    """Test TaskSpec handles missing fields gracefully."""
    # Missing title
    data = {"prompt": "Test prompt"}
    task = TaskSpec.from_dict(data)
    assert task.title == "Untitled Task"
    assert task.prompt == "Test prompt"

    # Missing prompt
    data = {"title": "Test task"}
    task = TaskSpec.from_dict(data)
    assert task.title == "Test task"
    assert task.prompt == ""

    # Empty dict
    task = TaskSpec.from_dict({})
    assert task.title == "Untitled Task"
    assert task.prompt == ""


def test_task_spec_round_trip():
    """Test TaskSpec serialization round-trip."""
    original = TaskSpec(
        title="Original task",
        prompt="Original prompt",
    )

    # to_dict -> from_dict should preserve data
    data = original.to_dict()
    restored = TaskSpec.from_dict(data)

    assert restored.title == original.title
    assert restored.prompt == original.prompt


def test_task_spec_with_enhanced_fields():
    """Test TaskSpec with new enhanced fields."""
    task = TaskSpec(
        id="task-1",
        title="Implement authentication",
        summary="Add JWT-based authentication to the API",
        prompt="Create login endpoint with JWT token generation",
        steps=[
            "Create auth.py file",
            "Add JWT dependency",
            "Implement login function",
        ],
        files=["src/api/auth.py", "tests/test_auth.py"],
        acceptance_checks=[
            "Run: pytest tests/test_auth.py",
            "Test: Login with valid credentials returns 200",
        ],
        risks=["JWT secret must be configured"],
        constraints=["Do not implement OAuth yet", "Use existing database connection"],
    )

    assert task.id == "task-1"
    assert task.summary == "Add JWT-based authentication to the API"
    assert len(task.steps) == 3
    assert len(task.files) == 2
    assert len(task.acceptance_checks) == 2
    assert len(task.risks) == 1
    assert len(task.constraints) == 2


def test_task_spec_enhanced_to_dict():
    """Test converting enhanced TaskSpec to dictionary."""
    task = TaskSpec(
        id="task-1",
        title="Test task",
        summary="Test summary",
        prompt="Test prompt",
        steps=["Step 1", "Step 2"],
        files=["file1.py", "file2.py"],
        acceptance_checks=["Check 1"],
        risks=["Risk 1"],
        constraints=["Constraint 1"],
    )

    result = task.to_dict()

    assert result["id"] == "task-1"
    assert result["summary"] == "Test summary"
    assert result["steps"] == ["Step 1", "Step 2"]
    assert result["files"] == ["file1.py", "file2.py"]
    assert result["acceptance_checks"] == ["Check 1"]
    assert result["risks"] == ["Risk 1"]
    assert result["constraints"] == ["Constraint 1"]


def test_task_spec_enhanced_from_dict():
    """Test creating enhanced TaskSpec from dictionary."""
    data = {
        "id": "task-2",
        "title": "Test task",
        "summary": "Summary",
        "prompt": "Prompt",
        "steps": ["Step A"],
        "files": ["test.py"],
        "acceptance_checks": ["pytest"],
        "risks": ["Risk"],
        "constraints": ["No refactoring"],
    }

    task = TaskSpec.from_dict(data)

    assert task.id == "task-2"
    assert task.summary == "Summary"
    assert task.steps == ["Step A"]
    assert task.files == ["test.py"]
    assert task.acceptance_checks == ["pytest"]
    assert task.risks == ["Risk"]
    assert task.constraints == ["No refactoring"]


def test_task_spec_enhanced_round_trip():
    """Test enhanced TaskSpec serialization round-trip."""
    original = TaskSpec(
        id="task-99",
        title="Complex task",
        summary="Do something complex",
        prompt="Detailed instructions",
        steps=["S1", "S2", "S3"],
        files=["a.py", "b.py"],
        acceptance_checks=["Test all"],
        risks=["Breaking changes"],
        constraints=["Keep it simple"],
    )

    data = original.to_dict()
    restored = TaskSpec.from_dict(data)

    assert restored.id == original.id
    assert restored.summary == original.summary
    assert restored.steps == original.steps
    assert restored.files == original.files
    assert restored.acceptance_checks == original.acceptance_checks
    assert restored.risks == original.risks
    assert restored.constraints == original.constraints


# ─────────────────────────────────────────────────────────────
# ReviewSpec Tests
# ─────────────────────────────────────────────────────────────


def test_review_spec_creation():
    """Test creating a ReviewSpec."""
    review = ReviewSpec(
        cumulative_summary="Work completed so far",
        batch_assessment="This batch went well",
        issues=["Minor issue 1", "Minor issue 2"],
        project_complete=False,
        completion_percentage=45,
        recommendations="Continue with next phase",
    )

    assert review.cumulative_summary == "Work completed so far"
    assert review.batch_assessment == "This batch went well"
    assert len(review.issues) == 2
    assert review.project_complete is False
    assert review.completion_percentage == 45


def test_review_spec_defaults():
    """Test ReviewSpec default values."""
    review = ReviewSpec(
        cumulative_summary="Summary",
        batch_assessment="Assessment",
    )

    assert review.issues == []
    assert review.project_complete is False
    assert review.completion_percentage == 0
    assert review.recommendations == ""


def test_review_spec_to_dict():
    """Test converting ReviewSpec to dictionary."""
    review = ReviewSpec(
        cumulative_summary="Summary",
        batch_assessment="Assessment",
        issues=["Issue 1"],
        project_complete=True,
        completion_percentage=100,
        recommendations="Done",
    )

    result = review.to_dict()

    assert result == {
        "cumulative_summary": "Summary",
        "batch_assessment": "Assessment",
        "issues": ["Issue 1"],
        "project_complete": True,
        "completion_percentage": 100,
        "recommendations": "Done",
        "next_tasks": [],
    }


def test_review_spec_from_dict():
    """Test creating ReviewSpec from dictionary."""
    data = {
        "cumulative_summary": "Summary",
        "batch_assessment": "Assessment",
        "issues": ["Issue 1", "Issue 2"],
        "project_complete": False,
        "completion_percentage": 50,
        "recommendations": "Keep going",
    }

    review = ReviewSpec.from_dict(data)

    assert review.cumulative_summary == "Summary"
    assert review.batch_assessment == "Assessment"
    assert len(review.issues) == 2
    assert review.completion_percentage == 50


def test_review_spec_from_dict_missing_fields():
    """Test ReviewSpec handles missing fields with defaults."""
    # Minimal data
    data = {
        "cumulative_summary": "Summary",
        "batch_assessment": "Assessment",
    }

    review = ReviewSpec.from_dict(data)

    assert review.cumulative_summary == "Summary"
    assert review.batch_assessment == "Assessment"
    assert review.issues == []
    assert review.project_complete is False
    assert review.completion_percentage == 0
    assert review.recommendations == ""

    # Empty dict
    review = ReviewSpec.from_dict({})
    assert review.cumulative_summary == ""
    assert review.batch_assessment == ""


def test_review_spec_round_trip():
    """Test ReviewSpec serialization round-trip."""
    original = ReviewSpec(
        cumulative_summary="Original summary",
        batch_assessment="Original assessment",
        issues=["Issue 1", "Issue 2"],
        project_complete=True,
        completion_percentage=100,
        recommendations="All done",
    )

    # to_dict -> from_dict should preserve data
    data = original.to_dict()
    restored = ReviewSpec.from_dict(data)

    assert restored.cumulative_summary == original.cumulative_summary
    assert restored.batch_assessment == original.batch_assessment
    assert restored.issues == original.issues
    assert restored.project_complete == original.project_complete
    assert restored.completion_percentage == original.completion_percentage
    assert restored.recommendations == original.recommendations


def test_review_spec_project_complete_flag():
    """Test project_complete flag behavior."""
    # Incomplete project
    review = ReviewSpec(
        cumulative_summary="Partial work",
        batch_assessment="In progress",
        project_complete=False,
        completion_percentage=60,
    )
    assert review.project_complete is False

    # Complete project
    review = ReviewSpec(
        cumulative_summary="All done",
        batch_assessment="Finished",
        project_complete=True,
        completion_percentage=100,
    )
    assert review.project_complete is True


def test_review_spec_with_next_tasks():
    """Test ReviewSpec with next_tasks field."""
    review = ReviewSpec(
        cumulative_summary="Work in progress",
        batch_assessment="Batch completed successfully",
        next_tasks=[
            {
                "title": "Fix bug in login",
                "summary": "Handle edge case for expired tokens",
                "priority": "high",
                "reason": "Blocking user flow",
            },
            {
                "title": "Add tests",
                "summary": "Increase test coverage",
                "priority": "medium",
                "reason": "Quality improvement",
            },
        ],
    )

    assert len(review.next_tasks) == 2
    assert review.next_tasks[0]["priority"] == "high"
    assert review.next_tasks[1]["title"] == "Add tests"


def test_review_spec_next_tasks_to_dict():
    """Test ReviewSpec with next_tasks serialization."""
    review = ReviewSpec(
        cumulative_summary="Summary",
        batch_assessment="Assessment",
        next_tasks=[{"title": "Task 1", "summary": "Do X", "priority": "low", "reason": "Nice to have"}],
    )

    result = review.to_dict()

    assert "next_tasks" in result
    assert len(result["next_tasks"]) == 1
    assert result["next_tasks"][0]["title"] == "Task 1"


def test_review_spec_next_tasks_from_dict():
    """Test ReviewSpec with next_tasks deserialization."""
    data = {
        "cumulative_summary": "Summary",
        "batch_assessment": "Assessment",
        "next_tasks": [
            {
                "title": "Urgent fix",
                "summary": "Fix critical bug",
                "priority": "high",
                "reason": "Production issue",
            }
        ],
    }

    review = ReviewSpec.from_dict(data)

    assert len(review.next_tasks) == 1
    assert review.next_tasks[0]["title"] == "Urgent fix"
    assert review.next_tasks[0]["priority"] == "high"
