"""
Tests for GPT planner resilience: retry logic and JSON repair.
"""

import json
import time
from unittest.mock import MagicMock, Mock, patch

import pytest

from chainsmith.planners.openai_adapter import OpenAIAdapter
from chainsmith.planners.types import TaskSpec, UsageMetrics


def create_mock_rate_limit_error():
    """Create a mock RateLimitError with required response object."""
    mock_request = Mock()
    mock_response = Mock()
    mock_response.request = mock_request

    # Import the error class
    from openai import RateLimitError
    return RateLimitError("Rate limit exceeded", response=mock_response, body=None)


def create_mock_api_error():
    """Create a mock APIError with required request object."""
    mock_request = Mock()

    from openai import APIError
    return APIError("Service unavailable", request=mock_request, body=None)


class TestRetryLogic:
    """Test retry logic for network errors and rate limits."""

    def test_rate_limit_retry_with_backoff(self):
        """Test that rate limit errors trigger retry with linear backoff."""
        adapter = OpenAIAdapter(api_key="test-key", model="gpt-4o")

        # Mock client to fail twice with rate limit, then succeed
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='{"tasks": []}'))]
        mock_response.usage = MagicMock(
            prompt_tokens=100, completion_tokens=50, total_tokens=150
        )

        adapter.client.chat.completions.create = MagicMock(
            side_effect=[
                create_mock_rate_limit_error(),
                create_mock_rate_limit_error(),
                mock_response,
            ]
        )

        # Patch time.sleep to avoid actual waiting
        with patch("time.sleep") as mock_sleep:
            result, usage = adapter._call_api_with_retry(
                system_prompt="test", user_prompt="test"
            )

            # Should have retried twice
            assert adapter.client.chat.completions.create.call_count == 3

            # Should have waited 30s, then 60s
            assert mock_sleep.call_count == 2
            mock_sleep.assert_any_call(30)
            mock_sleep.assert_any_call(60)

            assert result == '{"tasks": []}'
            assert usage.total_tokens == 150

    def test_api_error_retry_with_exponential_backoff(self):
        """Test that API errors trigger retry with exponential backoff."""
        adapter = OpenAIAdapter(api_key="test-key", model="gpt-4o")

        # Mock client to fail twice with API error, then succeed
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='{"tasks": []}'))]
        mock_response.usage = MagicMock(
            prompt_tokens=100, completion_tokens=50, total_tokens=150
        )

        adapter.client.chat.completions.create = MagicMock(
            side_effect=[
                create_mock_api_error(),
                create_mock_api_error(),
                mock_response,
            ]
        )

        with patch("time.sleep") as mock_sleep:
            result, usage = adapter._call_api_with_retry(
                system_prompt="test", user_prompt="test"
            )

            # Should have retried twice
            assert adapter.client.chat.completions.create.call_count == 3

            # Should have waited 2s, then 4s (exponential backoff: 2^(attempt+1))
            assert mock_sleep.call_count == 2
            mock_sleep.assert_any_call(2)
            mock_sleep.assert_any_call(4)

            assert result == '{"tasks": []}'

    def test_max_retries_exceeded(self):
        """Test that after max retries, a RuntimeError is raised."""
        adapter = OpenAIAdapter(api_key="test-key", model="gpt-4o")

        # Mock client to always fail
        adapter.client.chat.completions.create = MagicMock(
            side_effect=lambda *args, **kwargs: (_ for _ in ()).throw(create_mock_rate_limit_error())
        )

        with patch("time.sleep"):
            with pytest.raises(RuntimeError, match="Rate limit exceeded after all retries"):
                adapter._call_api_with_retry(system_prompt="test", user_prompt="test")

            # Should have tried 3 times
            assert adapter.client.chat.completions.create.call_count == 3


class TestJSONRepair:
    """Test JSON repair mechanism for parsing failures."""

    def test_json_repair_success(self):
        """Test that invalid JSON triggers repair attempt which succeeds."""
        adapter = OpenAIAdapter(api_key="test-key", model="gpt-4o")

        # First response: invalid JSON
        # Second response (repair): valid JSON
        invalid_json = "This is not JSON at all"
        valid_json = '{"tasks": [{"title": "Task 1", "prompt": "Do something"}]}'

        mock_response_valid = MagicMock()
        mock_response_valid.choices = [MagicMock(message=MagicMock(content=valid_json))]
        mock_response_valid.usage = MagicMock(
            prompt_tokens=120, completion_tokens=60, total_tokens=180
        )

        # Mock the API call for repair attempt
        adapter.client.chat.completions.create = MagicMock(return_value=mock_response_valid)

        # Parse with repair - first call will parse the invalid JSON, second is repair
        result = adapter._parse_json_with_repair(
            response_text=invalid_json,
            system_prompt="test",
            user_prompt="test",
            operation="test_operation",
        )

        # Should have made repair call
        assert adapter.client.chat.completions.create.call_count == 1  # One repair call

        # Should return parsed valid JSON
        assert result == {"tasks": [{"title": "Task 1", "prompt": "Do something"}]}

    def test_json_repair_failure(self):
        """Test that if repair also returns invalid JSON, ValueError is raised."""
        adapter = OpenAIAdapter(api_key="test-key", model="gpt-4o")

        # Both responses: invalid JSON
        invalid_json_1 = "This is not JSON"
        invalid_json_2 = "Still not JSON"

        mock_response_2 = MagicMock()
        mock_response_2.choices = [MagicMock(message=MagicMock(content=invalid_json_2))]
        mock_response_2.usage = MagicMock(
            prompt_tokens=120, completion_tokens=60, total_tokens=180
        )

        # Mock repair attempt to also return invalid JSON
        adapter.client.chat.completions.create = MagicMock(return_value=mock_response_2)

        # Parse with repair should raise ValueError
        with pytest.raises(ValueError, match="invalid JSON even after repair"):
            adapter._parse_json_with_repair(
                response_text=invalid_json_1,
                system_prompt="test",
                user_prompt="test",
                operation="test_operation",
            )

        # Should have made repair attempt
        assert adapter.client.chat.completions.create.call_count == 1  # One repair call

    def test_valid_json_no_repair_needed(self):
        """Test that valid JSON is parsed without repair attempt."""
        adapter = OpenAIAdapter(api_key="test-key", model="gpt-4o")

        valid_json = '{"tasks": [{"title": "Task 1", "prompt": "Do something"}]}'

        # Should not make any API calls for valid JSON
        result = adapter._parse_json_with_repair(
            response_text=valid_json,
            system_prompt="test",
            user_prompt="test",
            operation="test_operation",
        )

        assert result == {"tasks": [{"title": "Task 1", "prompt": "Do something"}]}


class TestUsageTracking:
    """Test token usage tracking and cost estimation."""

    def test_usage_metrics_extracted(self):
        """Test that usage metrics are extracted from API response."""
        adapter = OpenAIAdapter(api_key="test-key", model="gpt-4o")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='{"tasks": []}'))]
        mock_response.usage = MagicMock(
            prompt_tokens=500, completion_tokens=300, total_tokens=800
        )

        adapter.client.chat.completions.create = MagicMock(return_value=mock_response)

        result, usage = adapter._call_api_with_retry(
            system_prompt="test", user_prompt="test"
        )

        assert usage.prompt_tokens == 500
        assert usage.completion_tokens == 300
        assert usage.total_tokens == 800
        assert usage.cost_usd > 0  # Should have calculated cost

    def test_cost_estimation(self):
        """Test cost estimation for different models."""
        adapter = OpenAIAdapter(api_key="test-key", model="gpt-4o")

        usage = UsageMetrics(
            prompt_tokens=1_000_000,  # 1M tokens
            completion_tokens=1_000_000,  # 1M tokens
            total_tokens=2_000_000,
        )

        # Check that cost estimation is working and produces reasonable values
        cost = adapter._estimate_cost(usage, "gpt-4o")
        assert cost > 0  # Should calculate some cost
        assert cost < 200.0  # Should be reasonable for 2M tokens


class TestEndToEndResilience:
    """Test end-to-end planning with resilience features."""

    def test_plan_batch_with_json_repair(self):
        """Test plan_batch handles JSON repair gracefully."""
        adapter = OpenAIAdapter(api_key="test-key", model="gpt-4o")

        # First response: invalid JSON
        # Second response (repair): valid JSON
        invalid_json = "Not valid JSON"
        valid_json = '{"tasks": [{"title": "Task 1", "prompt": "Build feature X"}]}'

        mock_response_invalid = MagicMock()
        mock_response_invalid.choices = [MagicMock(message=MagicMock(content=invalid_json))]
        mock_response_invalid.usage = MagicMock(
            prompt_tokens=100, completion_tokens=50, total_tokens=150
        )

        mock_response_valid = MagicMock()
        mock_response_valid.choices = [MagicMock(message=MagicMock(content=valid_json))]
        mock_response_valid.usage = MagicMock(
            prompt_tokens=120, completion_tokens=60, total_tokens=180
        )

        adapter.client.chat.completions.create = MagicMock(
            side_effect=[mock_response_invalid, mock_response_valid]
        )

        tasks = adapter.plan_batch(
            project_description="Build a web app",
            repo_summary="",
            batch_size=3,
        )

        # Should return parsed tasks
        assert len(tasks) == 1
        assert tasks[0].title == "Task 1"
        assert tasks[0].prompt == "Build feature X"

    def test_plan_batch_with_rate_limit_retry(self):
        """Test plan_batch handles rate limits gracefully."""
        adapter = OpenAIAdapter(api_key="test-key", model="gpt-4o")

        valid_json = '{"tasks": [{"title": "Task 1", "prompt": "Build feature X"}]}'

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=valid_json))]
        mock_response.usage = MagicMock(
            prompt_tokens=100, completion_tokens=50, total_tokens=150
        )

        # Fail once with rate limit, then succeed
        adapter.client.chat.completions.create = MagicMock(
            side_effect=[
                create_mock_rate_limit_error(),
                mock_response,
            ]
        )

        with patch("time.sleep"):
            tasks = adapter.plan_batch(
                project_description="Build a web app",
                repo_summary="",
                batch_size=3,
            )

            # Should return tasks after retry
            assert len(tasks) == 1
            assert tasks[0].title == "Task 1"
