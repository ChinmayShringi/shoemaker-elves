"""
Unit tests for planner adapter registry.

Tests provider registration and adapter factory functionality.
"""

import pytest

from shoemaker_elves.planners.registry import (
    create_planner,
    get_available_providers,
    register_planner,
)
from shoemaker_elves.planners.anthropic_adapter import AnthropicAdapter
from shoemaker_elves.planners.azure_openai_adapter import AzureOpenAIAdapter
from shoemaker_elves.planners.openai_adapter import OpenAIAdapter


def test_get_available_providers():
    """Test listing registered providers."""
    providers = get_available_providers()

    assert "openai" in providers
    assert "anthropic" in providers
    assert "azure_openai" in providers
    assert "openai_compatible" in providers
    assert "deepseek" in providers
    assert isinstance(providers, list)
    # Should be sorted
    assert providers == sorted(providers)


def test_create_openai_planner():
    """Test creating standard OpenAI planner."""
    from unittest.mock import patch

    with patch("src.chainsmith.planners.openai_adapter.OpenAI"):
        planner = create_planner(
            provider="openai",
            api_key="test-key",
            model="gpt-4o",
        )

        assert isinstance(planner, OpenAIAdapter)
        assert planner.model == "gpt-4o"
        assert planner.base_url is None


def test_create_openai_compatible_planner():
    """Test creating OpenAI-compatible planner."""
    from unittest.mock import patch

    with patch("src.chainsmith.planners.openai_adapter.OpenAI"):
        planner = create_planner(
            provider="openai_compatible",
            api_key="test-key",
            model="gpt-4o",
            base_url="http://localhost:8000/v1",
        )

        assert isinstance(planner, OpenAIAdapter)
        assert planner.base_url == "http://localhost:8000/v1"


def test_create_anthropic_planner():
    """Test creating Anthropic planner."""
    from unittest.mock import patch

    with patch("src.chainsmith.planners.anthropic_adapter.Anthropic"):
        planner = create_planner(
            provider="anthropic",
            api_key="test-key",
            model="claude-sonnet-4-5-20250929",
        )

        assert isinstance(planner, AnthropicAdapter)
        assert planner.model == "claude-sonnet-4-5-20250929"


def test_create_azure_openai_planner():
    """Test creating Azure OpenAI planner."""
    from unittest.mock import patch

    with patch("src.chainsmith.planners.azure_openai_adapter.AzureOpenAI"):
        planner = create_planner(
            provider="azure_openai",
            api_key="test-key",
            endpoint="https://test.openai.azure.com/",
            deployment="gpt-4o",
            api_version="2024-02-01",
        )

        assert isinstance(planner, AzureOpenAIAdapter)
        assert planner.deployment == "gpt-4o"
        assert planner.endpoint == "https://test.openai.azure.com/"
        assert planner.api_version == "2024-02-01"


def test_create_azure_openai_missing_endpoint():
    """Test that azure_openai requires endpoint."""
    with pytest.raises(ValueError) as exc_info:
        create_planner(
            provider="azure_openai",
            api_key="test-key",
            deployment="gpt-4o",
        )

    assert "endpoint" in str(exc_info.value).lower()
    assert "required" in str(exc_info.value).lower()


def test_create_azure_openai_missing_deployment():
    """Test that azure_openai requires deployment."""
    with pytest.raises(ValueError) as exc_info:
        create_planner(
            provider="azure_openai",
            api_key="test-key",
            endpoint="https://test.openai.azure.com/",
        )

    assert "deployment" in str(exc_info.value).lower()
    assert "required" in str(exc_info.value).lower()


def test_create_openai_compatible_missing_base_url():
    """Test that openai_compatible requires base_url."""
    with pytest.raises(ValueError) as exc_info:
        create_planner(
            provider="openai_compatible",
            api_key="test-key",
            model="gpt-4o",
        )

    assert "base_url" in str(exc_info.value).lower()
    assert "required" in str(exc_info.value).lower()


def test_create_deepseek_planner():
    """Test creating DeepSeek planner with default base_url."""
    from unittest.mock import patch

    with patch("src.chainsmith.planners.openai_adapter.OpenAI"):
        planner = create_planner(
            provider="deepseek",
            api_key="test-key",
            model="deepseek-chat",
        )

        assert isinstance(planner, OpenAIAdapter)
        assert planner.model == "deepseek-chat"
        assert planner.base_url == "https://api.deepseek.com"


def test_create_deepseek_planner_custom_base_url():
    """Test creating DeepSeek planner with custom base_url."""
    from unittest.mock import patch

    with patch("src.chainsmith.planners.openai_adapter.OpenAI"):
        planner = create_planner(
            provider="deepseek",
            api_key="test-key",
            model="deepseek-chat",
            base_url="https://custom.deepseek.endpoint/v1",
        )

        assert isinstance(planner, OpenAIAdapter)
        assert planner.base_url == "https://custom.deepseek.endpoint/v1"


def test_create_unknown_provider():
    """Test error for unknown provider."""
    with pytest.raises(ValueError) as exc_info:
        create_planner(
            provider="unknown_provider",
            api_key="test-key",
            model="test-model",
        )

    error_msg = str(exc_info.value)
    assert "unknown_provider" in error_msg.lower()
    assert "available providers" in error_msg.lower()


def test_register_custom_planner():
    """Test registering a custom planner."""
    from shoemaker_elves.planners.base import PlannerAdapter
    from shoemaker_elves.planners.types import ReviewSpec, TaskSpec

    class MockAdapter:
        """Mock adapter for testing."""

        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def plan_batch(self, project_description, repo_summary, batch_size):
            return []

        def review_batch(self, project_description, repo_summary, task_results):
            return ReviewSpec(
                cumulative_summary="",
                batch_assessment="",
            )

    def mock_factory(**kwargs):
        return MockAdapter(**kwargs)

    # Register custom provider
    register_planner("test_provider", mock_factory)

    # Verify it's listed
    assert "test_provider" in get_available_providers()

    # Verify we can create it
    planner = create_planner(
        provider="test_provider",
        custom_arg="test_value",
    )

    assert isinstance(planner, MockAdapter)
    assert planner.kwargs["custom_arg"] == "test_value"


def test_load_plugins_with_mock_entrypoint():
    """Test plugin loading with mocked entrypoint."""
    from unittest.mock import Mock, patch
    from shoemaker_elves.planners.registry import load_plugins, _REGISTRY
    from shoemaker_elves.planners.types import ReviewSpec, TaskSpec

    class MockPluginAdapter:
        """Mock adapter from a plugin."""

        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def plan_batch(self, project_description, repo_summary, batch_size):
            return [TaskSpec(task="Plugin task", rationale="From plugin")]

        def review_batch(self, project_description, repo_summary, task_results):
            return ReviewSpec(status="success", new_summary="Plugin review")

    def mock_plugin_factory(**kwargs):
        kwargs.pop("provider", None)
        return MockPluginAdapter(**kwargs)

    def mock_register(registry_func):
        """Mock plugin register function."""
        registry_func("mock_plugin_provider", mock_plugin_factory)

    # Create mock entrypoint
    mock_ep = Mock()
    mock_ep.name = "mock_plugin"
    mock_ep.value = "mock_plugin:register"
    mock_ep.load.return_value = mock_register

    # Mock entry_points to return our mock entrypoint
    mock_eps = Mock()
    mock_eps.select.return_value = [mock_ep]

    # Track built-in providers before loading
    initial_providers = set(get_available_providers())

    with patch("src.chainsmith.planners.registry.entry_points", return_value=mock_eps):
        # Manually call load_plugins (normally called on import)
        load_plugins()

    # Verify plugin was loaded
    assert "mock_plugin_provider" in get_available_providers()
    assert "mock_plugin_provider" not in initial_providers

    # Verify we can create the plugin adapter
    planner = create_planner(
        provider="mock_plugin_provider",
        api_key="test-key",
    )
    assert isinstance(planner, MockPluginAdapter)

    # Clean up registry
    if "mock_plugin_provider" in _REGISTRY:
        del _REGISTRY["mock_plugin_provider"]


def test_plugin_cannot_override_builtin():
    """Test that plugins cannot override built-in providers."""
    from unittest.mock import Mock, patch
    from shoemaker_elves.planners.registry import load_plugins

    def bad_register(registry_func):
        """Plugin that tries to override built-in."""
        # This should raise ValueError
        registry_func("openai", lambda **k: None)

    # Create mock entrypoint for bad plugin
    mock_ep = Mock()
    mock_ep.name = "bad_plugin"
    mock_ep.value = "bad_plugin:register"
    mock_ep.load.return_value = bad_register

    mock_eps = Mock()
    mock_eps.select.return_value = [mock_ep]

    # Plugin should fail to load but not crash the app
    with patch("src.chainsmith.planners.registry.entry_points", return_value=mock_eps):
        with patch("src.chainsmith.planners.registry.logger") as mock_logger:
            load_plugins()
            # Should have logged a warning
            mock_logger.warning.assert_called()


def test_plugin_load_failure_is_non_fatal():
    """Test that plugin load failures don't crash the application."""
    from unittest.mock import Mock, patch
    from shoemaker_elves.planners.registry import load_plugins

    def broken_register(registry_func):
        """Plugin that raises an error."""
        raise RuntimeError("Plugin initialization failed")

    # Create mock entrypoint for broken plugin
    mock_ep = Mock()
    mock_ep.name = "broken_plugin"
    mock_ep.value = "broken_plugin:register"
    mock_ep.load.return_value = broken_register

    mock_eps = Mock()
    mock_eps.select.return_value = [mock_ep]

    # Plugin should fail to load but not crash
    with patch("src.chainsmith.planners.registry.entry_points", return_value=mock_eps):
        with patch("src.chainsmith.planners.registry.logger") as mock_logger:
            # Should not raise
            load_plugins()
            # Should have logged a warning
            mock_logger.warning.assert_called()

    # Built-in providers should still work
    assert "openai" in get_available_providers()
    assert "anthropic" in get_available_providers()


def test_plugin_load_failure_missing_module():
    """Test handling of plugins with missing modules."""
    from unittest.mock import Mock, patch
    from shoemaker_elves.planners.registry import load_plugins

    # Create mock entrypoint that fails to load
    mock_ep = Mock()
    mock_ep.name = "missing_plugin"
    mock_ep.value = "nonexistent_module:register"
    mock_ep.load.side_effect = ImportError("No module named 'nonexistent_module'")

    mock_eps = Mock()
    mock_eps.select.return_value = [mock_ep]

    # Should handle gracefully
    with patch("src.chainsmith.planners.registry.entry_points", return_value=mock_eps):
        with patch("src.chainsmith.planners.registry.logger") as mock_logger:
            load_plugins()
            # Should have logged a warning
            mock_logger.warning.assert_called()

    # Built-in providers should still work
    assert "openai" in get_available_providers()


def test_entrypoint_discovery_failure():
    """Test handling of entry_points() call failure."""
    from unittest.mock import patch
    from shoemaker_elves.planners.registry import load_plugins

    # Mock entry_points to raise an error
    with patch("src.chainsmith.planners.registry.entry_points", side_effect=RuntimeError("Discovery failed")):
        with patch("src.chainsmith.planners.registry.logger") as mock_logger:
            load_plugins()
            # Should have logged a warning
            mock_logger.warning.assert_called()

    # Built-in providers should still work
    assert "openai" in get_available_providers()
    assert "anthropic" in get_available_providers()


def test_plugin_with_python39_entrypoints_api():
    """Test plugin loading with Python 3.9 dict-style entry_points API."""
    from unittest.mock import Mock, patch
    from shoemaker_elves.planners.registry import load_plugins, _REGISTRY
    from shoemaker_elves.planners.types import ReviewSpec, TaskSpec

    class MockPluginAdapter39:
        """Mock adapter for Python 3.9 test."""

        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def plan_batch(self, project_description, repo_summary, batch_size):
            return []

        def review_batch(self, project_description, repo_summary, task_results):
            return ReviewSpec(status="success", new_summary="")

    def mock_plugin_factory_39(**kwargs):
        kwargs.pop("provider", None)
        return MockPluginAdapter39(**kwargs)

    def mock_register_39(registry_func):
        registry_func("plugin_39", mock_plugin_factory_39)

    # Create mock entrypoint
    mock_ep = Mock()
    mock_ep.name = "plugin_39"
    mock_ep.value = "plugin_39:register"
    mock_ep.load.return_value = mock_register_39

    # Mock Python 3.9 style dict API (no 'select' method)
    mock_eps_dict = {"gpt_orch.planners": [mock_ep]}

    with patch("src.chainsmith.planners.registry.entry_points", return_value=mock_eps_dict):
        load_plugins()

    # Verify plugin was loaded
    assert "plugin_39" in get_available_providers()

    # Clean up
    if "plugin_39" in _REGISTRY:
        del _REGISTRY["plugin_39"]
