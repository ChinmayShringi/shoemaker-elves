"""
Example Planner Plugin for GPT Agent Orchestrator.

This is a minimal working example of how to create a custom planner provider plugin.
It demonstrates the plugin interface and registration mechanism.
"""


def register(registry_func):
    """
    Register the example planner adapter.

    This function is called by the orchestrator's plugin loader.
    It receives a registry function that can be used to register
    one or more planner providers.

    Args:
        registry_func: Function to register providers.
                      Signature: registry_func(provider: str, factory: Callable)

    Example:
        >>> def register(registry_func):
        ...     registry_func("my_provider", my_factory_function)
    """

    def example_factory(**kwargs):
        """
        Factory function for creating ExampleAdapter instances.

        Args:
            **kwargs: Arguments passed from CLI/config:
                - api_key: API key for the provider
                - model: Model name/identifier
                - provider: Provider name (typically removed)
                - base_url: Optional base URL for API
                - ... any other custom parameters

        Returns:
            ExampleAdapter instance
        """
        # Lazy import to avoid circular dependency
        from .adapter import ExampleAdapter

        # Extract parameters needed for this adapter
        api_key = kwargs.pop("api_key", "example-key")
        model = kwargs.pop("model", "example-model-v1")

        # Remove provider argument (not needed by adapter)
        kwargs.pop("provider", None)

        # Create and return adapter instance
        return ExampleAdapter(api_key=api_key, model=model, **kwargs)

    # Register the provider with a unique name
    registry_func("example", example_factory)


__all__ = ["register"]
