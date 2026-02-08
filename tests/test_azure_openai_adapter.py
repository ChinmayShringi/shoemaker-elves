"""
Unit tests for Azure OpenAI planner adapter.

Tests JSON parsing, validation, and error handling with mocked Azure OpenAI client.
"""

import json
from unittest.mock import Mock, patch

import pytest

from shoemaker_elves.planners.azure_openai_adapter import AzureOpenAIAdapter
from shoemaker_elves.planners.types import ReviewSpec, TaskSpec

# ─────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────


@pytest.fixture
def mock_azure_client():
    """Mock Azure OpenAI client for testing."""
    with patch("shoemaker_elves.planners.azure_openai_adapter.AzureOpenAI") as mock_azure:
        client = Mock()
        mock_azure.return_value = client
        yield client


@pytest.fixture
def adapter(mock_azure_client):
    """Create Azure OpenAI adapter with mocked client."""
    return AzureOpenAIAdapter(
        api_key="test-key",
        endpoint="https://test.openai.azure.com/",
        deployment="gpt-4o",
        api_version="2024-02-01",
    )


# ─────────────────────────────────────────────────────────────
# Initialization Tests
# ─────────────────────────────────────────────────────────────


def test_adapter_init():
    """Test Azure OpenAI initialization."""
    with patch("shoemaker_elves.planners.azure_openai_adapter.AzureOpenAI") as mock_azure:
        adapter = AzureOpenAIAdapter(
            api_key="test-key",
            endpoint="https://test.openai.azure.com/",
            deployment="gpt-4o",
            api_version="2024-02-01",
        )

        # Should initialize with Azure-specific parameters
        mock_azure.assert_called_once_with(
            api_key="test-key",
            azure_endpoint="https://test.openai.azure.com/",
            api_version="2024-02-01",
        )
        assert adapter.deployment == "gpt-4o"
        assert adapter.endpoint == "https://test.openai.azure.com/"
        assert adapter.api_version == "2024-02-01"


def test_adapter_init_default_api_version():
    """Test Azure OpenAI initialization with default API version."""
    with patch("shoemaker_elves.planners.azure_openai_adapter.AzureOpenAI") as mock_azure:
        adapter = AzureOpenAIAdapter(
            api_key="test-key",
            endpoint="https://test.openai.azure.com/",
            deployment="gpt-4o",
        )

        # Should use default API version
        mock_azure.assert_called_once_with(
            api_key="test-key",
            azure_endpoint="https://test.openai.azure.com/",
            api_version="2024-02-01",
        )
        assert adapter.api_version == "2024-02-01"


# ─────────────────────────────────────────────────────────────
# plan_batch Tests
# ─────────────────────────────────────────────────────────────


def test_plan_batch_success(adapter, mock_azure_client):
    """Test successful task planning."""
    # Mock successful API response
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(
        {
            "tasks": [
                {"title": "Task 1", "prompt": "Do thing 1"},
                {"title": "Task 2", "prompt": "Do thing 2"},
            ],
            "batch_reasoning": "These tasks set up the foundation",
        }
    )
    mock_azure_client.chat.completions.create.return_value = mock_response

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

    # Verify API was called correctly with deployment name
    mock_azure_client.chat.completions.create.assert_called_once()
    call_args = mock_azure_client.chat.completions.create.call_args
    assert call_args.kwargs["model"] == "gpt-4o"  # deployment name
    assert call_args.kwargs["response_format"] == {"type": "json_object"}
    assert call_args.kwargs["temperature"] == 0.2


def test_plan_batch_empty_tasks(adapter, mock_azure_client):
    """Test project complete signal (empty tasks array)."""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(
        {
            "tasks": [],
            "batch_reasoning": "Project is complete",
        }
    )
    mock_azure_client.chat.completions.create.return_value = mock_response

    tasks = adapter.plan_batch(
        project_description="Build a web app",
        repo_summary="All features implemented",
        batch_size=5,
    )

    assert tasks == []


def test_plan_batch_invalid_json(adapter, mock_azure_client):
    """Test handling of malformed JSON response."""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "This is not JSON"
    mock_azure_client.chat.completions.create.return_value = mock_response

    with pytest.raises(ValueError) as exc_info:
        adapter.plan_batch(
            project_description="Build a web app",
            repo_summary="",
            batch_size=5,
        )

    assert "invalid JSON" in str(exc_info.value)
    assert "Azure OpenAI" in str(exc_info.value)


def test_plan_batch_missing_tasks_field(adapter, mock_azure_client):
    """Test handling of response missing 'tasks' field."""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(
        {
            "batch_reasoning": "Missing tasks field",
        }
    )
    mock_azure_client.chat.completions.create.return_value = mock_response

    with pytest.raises(ValueError) as exc_info:
        adapter.plan_batch(
            project_description="Build a web app",
            repo_summary="",
            batch_size=5,
        )

    assert "missing 'tasks' field" in str(exc_info.value)


def test_plan_batch_invalid_task_structure(adapter, mock_azure_client):
    """Test handling of invalid task structure."""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(
        {
            "tasks": [
                {"title": "Valid task", "prompt": "Do something"},
                {"title": "Missing prompt"},  # Missing required field
            ],
        }
    )
    mock_azure_client.chat.completions.create.return_value = mock_response

    with pytest.raises(ValueError) as exc_info:
        adapter.plan_batch(
            project_description="Build a web app",
            repo_summary="",
            batch_size=5,
        )

    assert "missing required 'prompt' field" in str(exc_info.value)


def test_plan_batch_tasks_not_array(adapter, mock_azure_client):
    """Test handling when 'tasks' is not an array."""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(
        {
            "tasks": "not an array",
        }
    )
    mock_azure_client.chat.completions.create.return_value = mock_response

    with pytest.raises(ValueError) as exc_info:
        adapter.plan_batch(
            project_description="Build a web app",
            repo_summary="",
            batch_size=5,
        )

    assert "'tasks' field must be a list" in str(exc_info.value)


# ─────────────────────────────────────────────────────────────
# review_batch Tests
# ─────────────────────────────────────────────────────────────


def test_review_batch_success(adapter, mock_azure_client):
    """Test successful batch review."""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(
        {
            "cumulative_summary": "Completed setup and basic features",
            "batch_assessment": "Batch completed successfully",
            "issues": [],
            "project_complete": False,
            "completion_percentage": 30,
            "recommendations": "Continue with authentication",
        }
    )
    mock_azure_client.chat.completions.create.return_value = mock_response

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


def test_review_batch_project_complete(adapter, mock_azure_client):
    """Test review indicating project completion."""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(
        {
            "cumulative_summary": "All features implemented and tested",
            "batch_assessment": "Final polish complete",
            "issues": [],
            "project_complete": True,
            "completion_percentage": 100,
            "recommendations": "Project ready for deployment",
        }
    )
    mock_azure_client.chat.completions.create.return_value = mock_response

    review = adapter.review_batch(
        project_description="Build a web app",
        repo_summary="All features done",
        task_results=[],
    )

    assert review.project_complete is True
    assert review.completion_percentage == 100


def test_review_batch_with_issues(adapter, mock_azure_client):
    """Test review with identified issues."""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(
        {
            "cumulative_summary": "Setup complete with issues",
            "batch_assessment": "Some tasks failed",
            "issues": ["Database connection failed", "Tests not passing"],
            "project_complete": False,
            "completion_percentage": 20,
            "recommendations": "Fix database config",
        }
    )
    mock_azure_client.chat.completions.create.return_value = mock_response

    review = adapter.review_batch(
        project_description="Build a web app",
        repo_summary="",
        task_results=[],
    )

    assert len(review.issues) == 2
    assert "Database connection failed" in review.issues


def test_review_batch_invalid_json(adapter, mock_azure_client):
    """Test graceful handling of invalid JSON in review."""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Not JSON"
    mock_azure_client.chat.completions.create.return_value = mock_response

    # Should return a basic ReviewSpec instead of raising
    review = adapter.review_batch(
        project_description="Build a web app",
        repo_summary="Previous work",
        task_results=[],
    )

    assert isinstance(review, ReviewSpec)
    assert "Previous work" in review.cumulative_summary
    assert "parse error" in review.cumulative_summary.lower()
    assert "Azure OpenAI" in review.batch_assessment


def test_review_batch_missing_required_fields(adapter, mock_azure_client):
    """Test handling of missing required fields in review response."""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(
        {
            "batch_assessment": "Missing cumulative_summary",
            "issues": [],
        }
    )
    mock_azure_client.chat.completions.create.return_value = mock_response

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


def test_authentication_error(adapter, mock_azure_client):
    """Test handling of authentication errors."""
    from openai import AuthenticationError

    mock_azure_client.chat.completions.create.side_effect = AuthenticationError(
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
    assert "azure" in str(exc_info.value).lower()


def test_rate_limit_retry(adapter, mock_azure_client):
    """Test retry logic for rate limits."""
    from openai import RateLimitError

    # First two calls fail with rate limit, third succeeds
    mock_azure_client.chat.completions.create.side_effect = [
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
        Mock(
            choices=[
                Mock(
                    message=Mock(
                        content=json.dumps(
                            {
                                "tasks": [{"title": "Test", "prompt": "Test task"}],
                            }
                        )
                    )
                )
            ]
        ),
    ]

    # Mock time.sleep to avoid actual delays in tests
    with patch("shoemaker_elves.planners.azure_openai_adapter.time.sleep"):
        tasks = adapter.plan_batch(
            project_description="Build a web app",
            repo_summary="",
            batch_size=5,
        )

    assert len(tasks) == 1
    assert mock_azure_client.chat.completions.create.call_count == 3


def test_api_error_max_retries(adapter, mock_azure_client):
    """Test that API errors cause failure after max retries."""
    from openai import APIError

    mock_azure_client.chat.completions.create.side_effect = APIError(
        message="Server error",
        request=Mock(),
        body=None,
    )

    with patch("shoemaker_elves.planners.azure_openai_adapter.time.sleep"):
        with pytest.raises(RuntimeError) as exc_info:
            adapter.plan_batch(
                project_description="Build a web app",
                repo_summary="",
                batch_size=5,
            )

    assert "after" in str(exc_info.value).lower()
    assert "retries" in str(exc_info.value).lower()
    # Should have tried 3 times
    assert mock_azure_client.chat.completions.create.call_count == 3


# ─────────────────────────────────────────────────────────────
# Azure-Specific Tests
# ─────────────────────────────────────────────────────────────


def test_deployment_name_used_as_model(adapter, mock_azure_client):
    """Test that deployment name is used as model parameter."""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(
        {
            "tasks": [{"title": "Test", "prompt": "Test task"}],
        }
    )
    mock_azure_client.chat.completions.create.return_value = mock_response

    adapter.plan_batch(
        project_description="Build a web app",
        repo_summary="",
        batch_size=5,
    )

    # Verify deployment name is used as model
    call_args = mock_azure_client.chat.completions.create.call_args
    assert call_args.kwargs["model"] == "gpt-4o"


def test_different_api_versions(mock_azure_client):
    """Test initialization with different API versions."""
    with patch("shoemaker_elves.planners.azure_openai_adapter.AzureOpenAI") as mock_azure:
        adapter = AzureOpenAIAdapter(
            api_key="test-key",
            endpoint="https://test.openai.azure.com/",
            deployment="gpt-4o",
            api_version="2023-12-01-preview",
        )

        # Should use specified API version
        mock_azure.assert_called_once_with(
            api_key="test-key",
            azure_endpoint="https://test.openai.azure.com/",
            api_version="2023-12-01-preview",
        )
        assert adapter.api_version == "2023-12-01-preview"
