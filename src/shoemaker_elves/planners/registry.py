"""
Registry for planner adapters.
Maps provider strings to adapter factory functions.
Supports plugin discovery via importlib.metadata entrypoints.
"""

import logging
from importlib.metadata import entry_points
from typing import Callable

from .base import PlannerAdapter
from .anthropic_adapter import AnthropicAdapter
from .azure_openai_adapter import AzureOpenAIAdapter
from .openai_adapter import OpenAIAdapter

logger = logging.getLogger(__name__)

# Type for adapter factory functions
AdapterFactory = Callable[..., PlannerAdapter]

# Registry mapping provider names to factory functions
_REGISTRY: dict[str, AdapterFactory] = {}


def register_planner(provider: str, factory: AdapterFactory) -> None:
    """
    Register a planner adapter factory.

    Args:
        provider: Provider identifier (e.g., "openai", "openai_compatible")
        factory: Factory function that creates adapter instances
    """
    _REGISTRY[provider] = factory


def create_planner(provider: str, **kwargs) -> PlannerAdapter:
    """
    Create a planner adapter instance.

    Args:
        provider: Provider identifier
        **kwargs: Arguments to pass to the adapter factory

    Returns:
        Initialized PlannerAdapter instance

    Raises:
        ValueError: If provider is not registered
    """
    if provider not in _REGISTRY:
        available = ", ".join(sorted(_REGISTRY.keys()))
        raise ValueError(
            f"Unknown planner provider: {provider}. "
            f"Available providers: {available}"
        )

    factory = _REGISTRY[provider]
    return factory(**kwargs)


def get_available_providers() -> list[str]:
    """
    Get list of registered provider names.

    Returns:
        Sorted list of provider identifiers
    """
    return sorted(_REGISTRY.keys())


def load_plugins() -> None:
    """
    Discover and load planner plugins via importlib.metadata entrypoints.

    Plugins are loaded from the 'gpt_orch.planners' entrypoint group.
    Each plugin should expose a 'register' function that accepts the registry
    as an argument and registers one or more providers.

    Plugin failures are logged as warnings but do not stop the application.
    Built-in providers cannot be overridden by plugins.
    """
    # Get snapshot of built-in providers before loading plugins
    builtin_providers = set(_REGISTRY.keys())

    # Discover plugins from the entrypoint group
    try:
        eps = entry_points()
        # Handle both old (dict) and new (SelectableGroups) API
        if hasattr(eps, "select"):
            # Python 3.10+ API
            plugin_entries = eps.select(group="gpt_orch.planners")
        else:
            # Python 3.9 API (dict-like)
            plugin_entries = eps.get("gpt_orch.planners", [])
    except Exception as e:
        logger.warning(f"Failed to discover plugins: {e}")
        return

    # Load each plugin
    for entry_point in plugin_entries:
        try:
            # Load the plugin's register function
            register_func = entry_point.load()

            # Call the register function with a registration helper
            register_func(_create_plugin_registrar(builtin_providers))

            logger.info(f"Loaded plugin: {entry_point.name} from {entry_point.value}")
        except Exception as e:
            logger.warning(
                f"Failed to load plugin '{entry_point.name}' from {entry_point.value}: {e}"
            )


def _create_plugin_registrar(builtin_providers: set[str]):
    """
    Create a plugin registration helper that prevents overriding built-ins.

    Args:
        builtin_providers: Set of built-in provider names to protect

    Returns:
        A registration function that plugins can use
    """

    def plugin_register(provider: str, factory: AdapterFactory) -> None:
        """
        Register a planner adapter from a plugin.

        Args:
            provider: Provider identifier
            factory: Factory function that creates adapter instances

        Raises:
            ValueError: If attempting to override a built-in provider
        """
        if provider in builtin_providers:
            raise ValueError(
                f"Plugin attempted to override built-in provider '{provider}'. "
                f"Built-in providers cannot be overridden."
            )

        # Register the plugin provider
        register_planner(provider, factory)
        logger.info(f"Plugin registered provider: {provider}")

    return plugin_register


# Register built-in providers
def _openai_factory(**kwargs) -> OpenAIAdapter:
    """Factory for standard OpenAI adapter."""
    # Remove provider-specific args that aren't needed
    kwargs.pop("provider", None)
    return OpenAIAdapter(**kwargs)


def _openai_compatible_factory(**kwargs) -> OpenAIAdapter:
    """Factory for OpenAI-compatible endpoints."""
    # Require base_url for compatible providers
    if "base_url" not in kwargs or not kwargs["base_url"]:
        raise ValueError(
            "base_url is required for openai_compatible provider. "
            "Use --planner-base-url to specify the endpoint."
        )
    kwargs.pop("provider", None)
    return OpenAIAdapter(**kwargs)


def _anthropic_factory(**kwargs) -> AnthropicAdapter:
    """Factory for Anthropic (Claude) adapter."""
    # Remove provider-specific args that aren't needed
    kwargs.pop("provider", None)
    # Remove base_url if present (not used by Anthropic)
    kwargs.pop("base_url", None)
    return AnthropicAdapter(**kwargs)


def _azure_openai_factory(**kwargs) -> AzureOpenAIAdapter:
    """Factory for Azure OpenAI adapter."""
    # Extract Azure-specific parameters
    endpoint = kwargs.pop("endpoint", None)
    deployment = kwargs.pop("deployment", None)
    api_version = kwargs.pop("api_version", "2024-02-01")
    api_key = kwargs.pop("api_key", None)

    # Validate required parameters
    if not endpoint:
        raise ValueError(
            "endpoint is required for azure_openai provider. "
            "Use --azure-endpoint or set SHOEMAKER_ELVES_AZURE_ENDPOINT."
        )
    if not deployment:
        raise ValueError(
            "deployment is required for azure_openai provider. "
            "Use --azure-deployment or set SHOEMAKER_ELVES_AZURE_DEPLOYMENT."
        )
    if not api_key:
        raise ValueError(
            "api_key is required for azure_openai provider. "
            "Set SHOEMAKER_ELVES_AZURE_OPENAI_API_KEY."
        )

    # Remove provider and other unused args
    kwargs.pop("provider", None)
    kwargs.pop("base_url", None)
    kwargs.pop("model", None)  # Azure uses deployment instead

    return AzureOpenAIAdapter(
        api_key=api_key,
        endpoint=endpoint,
        deployment=deployment,
        api_version=api_version,
    )


def _deepseek_factory(**kwargs) -> OpenAIAdapter:
    """Factory for DeepSeek adapter (OpenAI-compatible)."""
    # Set default base_url if not provided
    if "base_url" not in kwargs or not kwargs["base_url"]:
        kwargs["base_url"] = "https://api.deepseek.com"

    kwargs.pop("provider", None)
    return OpenAIAdapter(**kwargs)


# Register built-in providers
register_planner("openai", _openai_factory)
register_planner("openai_compatible", _openai_compatible_factory)
register_planner("anthropic", _anthropic_factory)
register_planner("azure_openai", _azure_openai_factory)
register_planner("deepseek", _deepseek_factory)

# Load plugins on module import
load_plugins()
