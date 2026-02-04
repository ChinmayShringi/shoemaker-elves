"""
Unit tests for Anthropic planner adapter.

Tests JSON parsing, validation, and error handling with mocked Anthropic client.
"""

import json
from unittest.mock import MagicMock, Mock, patch

import pytest

from gpt_agent_orchestrator.planners.anthropic_adapter import AnthropicAdapter
from gpt_agent_orchestrator.planners.types import ReviewSpec, TaskSpec


# ─────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client for testing."""
    with patch("src.gpt_agent_orchestrator.planners.anthropic_adapter.Anthropic") as mock_anthropic:
        client = Mock()
        mock_anthropic.return_value = client
        yield client


@pytest.fixture
def adapter(mock_anthropic_client):
    """Create Anthropic adapter with mocked client."""
    return AnthropicAdapter(api_key="test-key", model="claude-sonnet-4-5-20250929")


# ─────────────────────────────────────────────────────────────
# Initialization Tests
# ─────────────────────────────────────────────────────────────


def test_adapter_init():
    """Test Anthropic adapter initialization."""
    with patch("src.gpt_agent_orchestrator.planners.anthropic_adapter.Anthropic") as mock_anthropic:
        adapter = AnthropicAdapter(api_key="test-key", model="claude-sonnet-4-5-20250929")

        # Should initialize with api_key
        mock_anthropic.assert_called_once_with(api_key="test-key")
        assert adapter.model == "claude-sonnet-4-5-20250929"


def test_adapter_init_default_model():
    """Test Anthropic adapter initialization with default model."""
    with patch("src.gpt_agent_orchestrator.planners.anthropic_adapter.Anthropic") as mock_anthropic:
        adapter = AnthropicAdapter(api_key="test-key")

        assert adapter.model == "claude-sonnet-4-5-20250929"


# ─────────────────────────────────────────────────────────────
# plan_batch Tests
# ─────────────────────────────────────────────────────────────


def test_plan_batch_success(adapter, mock_anthropic_client):
    """Test successful task planning."""
    # Mock successful API response
    mock_response = Mock()
    mock_text_block = Mock()
    mock_text_block.text = json.dumps({
        "tasks": [
            {"title": "Task 1", "prompt": "Do thing 1"},
            {"title": "Task 2", "prompt": "Do thing 2"},
        ],
        "batch_reasoning": "These tasks set up the foundation",
    })
    mock_response.content = [mock_text_block]
    mock_anthropic_client.messages.create.return_value = mock_response

    # Call plan_batch
    tasks = adapter.plan_batch(
        project_description="Build a web app",
        repo_summary="",
        batch_size=5,
    )

    # Verify results
    assert len(tasks) == 2
    assert isinstance(tasks[0], TaskSpec)
    assert tasks[0].title == "Task 1"
    assert tasks[0].prompt == "Do thing 1"
    assert tasks[1].title == "Task 2"

    # Verify API was called correctly
    mock_anthropic_client.messages.create.assert_called_once()
    call_args = mock_anthropic_client.messages.create.call_args
    assert call_args.kwargs["model"] == "claude-sonnet-4-5-20250929"
    assert call_args.kwargs["max_tokens"] == 4096
    assert call_args.kwargs["temperature"] == 0.2
    assert "JSON" in call_args.kwargs["system"]


def test_plan_batch_empty_tasks(adapter, mock_anthropic_client):
    """Test project complete signal (empty tasks array)."""
    mock_response = Mock()
    mock_text_block = Mock()
    mock_text_block.text = json.dumps({
        "tasks": [],
        "batch_reasoning": "Project is complete",
    })
    mock_response.content = [mock_text_block]
    mock_anthropic_client.messages.create.return_value = mock_response

    tasks = adapter.plan_batch(
        project_description="Build a web app",
        repo_summary="All features implemented",
        batch_size=5,
    )

    assert tasks == []


def test_plan_batch_invalid_json(adapter, mock_anthropic_client):
    """Test handling of malformed JSON response with repair attempt."""
    mock_response = Mock()
    mock_text_block = Mock()
    mock_text_block.text = "This is not JSON"
    mock_response.content = [mock_text_block]
    mock_anthropic_client.messages.create.return_value = mock_response

    with pytest.raises(ValueError) as exc_info:
        adapter.plan_batch(
            project_description="Build a web app",
            repo_summary="",
            batch_size=5,
        )

    # New behavior: attempts repair, so error message indicates repair was tried
    assert "invalid JSON" in str(exc_info.value)
    assert "after repair" in str(exc_info.value)


def test_plan_batch_missing_tasks_field(adapter, mock_anthropic_client):
    """Test handling of response missing 'tasks' field."""
    mock_response = Mock()
    mock_text_block = Mock()
    mock_text_block.text = json.dumps({
        "batch_reasoning": "Missing tasks field",
    })
    mock_response.content = [mock_text_block]
    mock_anthropic_client.messages.create.return_value = mock_response

    with pytest.raises(ValueError) as exc_info:
        adapter.plan_batch(
            project_description="Build a web app",
            repo_summary="",
            batch_size=5,
        )

    assert "missing 'tasks' field" in str(exc_info.value)


def test_plan_batch_invalid_task_structure(adapter, mock_anthropic_client):
    """Test handling of invalid task structure."""
    mock_response = Mock()
    mock_text_block = Mock()
    mock_text_block.text = json.dumps({
        "tasks": [
            {"title": "Valid task", "prompt": "Do something"},
            {"title": "Missing prompt"},  # Missing required field
        ],
    })
    mock_response.content = [mock_text_block]
    mock_anthropic_client.messages.create.return_value = mock_response

    with pytest.raises(ValueError) as exc_info:
        adapter.plan_batch(
            project_description="Build a web app",
            repo_summary="",
            batch_size=5,
        )

    assert "missing required 'prompt' field" in str(exc_info.value)


def test_plan_batch_tasks_not_array(adapter, mock_anthropic_client):
    """Test handling when 'tasks' is not an array."""
    mock_response = Mock()
    mock_text_block = Mock()
    mock_text_block.text = json.dumps({
        "tasks": "not an array",
    })
    mock_response.content = [mock_text_block]
    mock_anthropic_client.messages.create.return_value = mock_response

    with pytest.raises(ValueError) as exc_info:
        adapter.plan_batch(
            project_description="Build a web app",
            repo_summary="",
            batch_size=5,
        )

    assert "'tasks' field must be a list" in str(exc_info.value)


def test_plan_batch_empty_response_content(adapter, mock_anthropic_client):
    """Test handling of empty response content."""
    mock_response = Mock()
    mock_response.content = []
    mock_anthropic_client.messages.create.return_value = mock_response

    with pytest.raises(ValueError) as exc_info:
        adapter.plan_batch(
            project_description="Build a web app",
            repo_summary="",
            batch_size=5,
        )

    assert "Empty response" in str(exc_info.value)


# ─────────────────────────────────────────────────────────────
# review_batch Tests
# ─────────────────────────────────────────────────────────────


def test_review_batch_success(adapter, mock_anthropic_client):
    """Test successful batch review."""
    mock_response = Mock()
    mock_text_block = Mock()
    mock_text_block.text = json.dumps({
        "cumulative_summary": "Completed setup and basic features",
        "batch_assessment": "Batch completed successfully",
        "issues": [],
        "project_complete": False,
        "completion_percentage": 30,
        "recommendations": "Continue with authentication",
    })
    mock_response.content = [mock_text_block]
    mock_anthropic_client.messages.create.return_value = mock_response

    task_results = [
        {"title": "Task 1", "success": True, "result_summary": "Done"},
    ]

    review = adapter.review_batch(
        project_description="Build a web app",
        repo_summary="Initial setup complete",
        task_results=task_results,
    )

    assert isinstance(review, ReviewSpec)
    assert review.cumulative_summary == "Completed setup and basic features"
    assert review.batch_assessment == "Batch completed successfully"
    assert review.project_complete is False
    assert review.completion_percentage == 30


def test_review_batch_project_complete(adapter, mock_anthropic_client):
    """Test review indicating project completion."""
    mock_response = Mock()
    mock_text_block = Mock()
    mock_text_block.text = json.dumps({
        "cumulative_summary": "All features implemented and tested",
        "batch_assessment": "Final polish complete",
        "issues": [],
        "project_complete": True,
        "completion_percentage": 100,
        "recommendations": "Project ready for deployment",
    })
    mock_response.content = [mock_text_block]
    mock_anthropic_client.messages.create.return_value = mock_response

    review = adapter.review_batch(
        project_description="Build a web app",
        repo_summary="All features done",
        task_results=[],
    )

    assert review.project_complete is True
    assert review.completion_percentage == 100


def test_review_batch_with_issues(adapter, mock_anthropic_client):
    """Test review with identified issues."""
    mock_response = Mock()
    mock_text_block = Mock()
    mock_text_block.text = json.dumps({
        "cumulative_summary": "Setup complete with issues",
        "batch_assessment": "Some tasks failed",
        "issues": ["Database connection failed", "Tests not passing"],
        "project_complete": False,
        "completion_percentage": 20,
        "recommendations": "Fix database config",
    })
    mock_response.content = [mock_text_block]
    mock_anthropic_client.messages.create.return_value = mock_response

    review = adapter.review_batch(
        project_description="Build a web app",
        repo_summary="",
        task_results=[],
    )

    assert len(review.issues) == 2
    assert "Database connection failed" in review.issues


def test_review_batch_invalid_json(adapter, mock_anthropic_client):
    """Test graceful handling of invalid JSON in review."""
    mock_response = Mock()
    mock_text_block = Mock()
    mock_text_block.text = "Not JSON"
    mock_response.content = [mock_text_block]
    mock_anthropic_client.messages.create.return_value = mock_response

    # Should return a basic ReviewSpec instead of raising
    review = adapter.review_batch(
        project_description="Build a web app",
        repo_summary="Previous work",
        task_results=[],
    )

    assert isinstance(review, ReviewSpec)
    assert "Previous work" in review.cumulative_summary
    assert "parse error" in review.cumulative_summary.lower()


def test_review_batch_missing_required_fields(adapter, mock_anthropic_client):
    """Test handling of missing required fields in review response."""
    mock_response = Mock()
    mock_text_block = Mock()
    mock_text_block.text = json.dumps({
        "batch_assessment": "Missing cumulative_summary",
        "issues": [],
    })
    mock_response.content = [mock_text_block]
    mock_anthropic_client.messages.create.return_value = mock_response

    with pytest.raises(ValueError) as exc_info:
        adapter.review_batch(
            project_description="Build a web app",
            repo_summary="",
            task_results=[],
        )

    assert "missing required fields" in str(exc_info.value)


# ─────────────────────────────────────────────────────────────
# Error Handling Tests
# ─────────────────────────────────────────────────────────────


def test_authentication_error(adapter, mock_anthropic_client):
    """Test handling of authentication errors."""
    from anthropic import AuthenticationError

    mock_anthropic_client.messages.create.side_effect = AuthenticationError(
        message="Invalid API key",
        response=Mock(status_code=401),
        body=None,
    )

    with pytest.raises(RuntimeError) as exc_info:
        adapter.plan_batch(
            project_description="Build a web app",
            repo_summary="",
            batch_size=5,
        )

    assert "authentication failed" in str(exc_info.value).lower()


def test_rate_limit_retry(adapter, mock_anthropic_client):
    """Test retry logic for rate limits."""
    from anthropic import RateLimitError

    # First two calls fail with rate limit, third succeeds
    mock_success_response = Mock()
    mock_text_block = Mock()
    mock_text_block.text = json.dumps({
        "tasks": [{"title": "Test", "prompt": "Test task"}],
    })
    mock_success_response.content = [mock_text_block]

    mock_anthropic_client.messages.create.side_effect = [
        RateLimitError(
            message="Rate limited",
            response=Mock(status_code=429),
            body=None,
        ),
        RateLimitError(
            message="Rate limited",
            response=Mock(status_code=429),
            body=None,
        ),
        mock_success_response,
    ]

    # Mock time.sleep to avoid actual delays in tests
    with patch("src.gpt_agent_orchestrator.planners.anthropic_adapter.time.sleep"):
        tasks = adapter.plan_batch(
            project_description="Build a web app",
            repo_summary="",
            batch_size=5,
        )

    assert len(tasks) == 1
    assert mock_anthropic_client.messages.create.call_count == 3


def test_api_error_max_retries(adapter, mock_anthropic_client):
    """Test that API errors cause failure after max retries."""
    from anthropic import APIError

    mock_anthropic_client.messages.create.side_effect = APIError(
        message="Server error",
        request=Mock(),
        body=None,
    )

    with patch("src.gpt_agent_orchestrator.planners.anthropic_adapter.time.sleep"):
        with pytest.raises(RuntimeError) as exc_info:
            adapter.plan_batch(
                project_description="Build a web app",
                repo_summary="",
                batch_size=5,
            )

    assert "after" in str(exc_info.value).lower()
    assert "retries" in str(exc_info.value).lower()
    # Should have tried 3 times
    assert mock_anthropic_client.messages.create.call_count == 3


def test_plan_batch_with_reasoning(adapter, mock_anthropic_client, capsys):
    """Test that batch reasoning is printed when provided."""
    mock_response = Mock()
    mock_text_block = Mock()
    mock_text_block.text = json.dumps({
        "tasks": [{"title": "Task 1", "prompt": "Do thing 1"}],
        "batch_reasoning": "Starting with database setup",
    })
    mock_response.content = [mock_text_block]
    mock_anthropic_client.messages.create.return_value = mock_response

    adapter.plan_batch(
        project_description="Build a web app",
        repo_summary="",
        batch_size=5,
    )

    captured = capsys.readouterr()
    assert "Claude reasoning" in captured.out
    assert "Starting with database setup" in captured.out


def test_plan_batch_multiple_text_blocks(adapter, mock_anthropic_client):
    """Test handling of multiple text blocks in response content."""
    mock_response = Mock()
    mock_text_block1 = Mock()
    mock_text_block1.text = '{"tasks": ['
    mock_text_block2 = Mock()
    mock_text_block2.text = '{"title": "Task 1", "prompt": "Do thing"}]}'
    mock_response.content = [mock_text_block1, mock_text_block2]
    mock_anthropic_client.messages.create.return_value = mock_response

    tasks = adapter.plan_batch(
        project_description="Build a web app",
        repo_summary="",
        batch_size=5,
    )

    assert len(tasks) == 1
    assert tasks[0].title == "Task 1"
