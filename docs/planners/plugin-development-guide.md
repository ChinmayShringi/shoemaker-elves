# Plugin Development Guide

This guide explains how to create custom planner provider plugins for the GPT Agent Orchestrator.

## Overview

The plugin system allows you to add support for new LLM providers without modifying the core orchestrator code. Plugins are discovered automatically via Python entrypoints and loaded at runtime.

## Plugin Interface

### Entrypoint Group

Plugins must register under the `gpt_orch.planners` entrypoint group.

### Registration Function

Each plugin must expose a `register` function that accepts a registration helper:

```python
def register(registry_func):
    """
    Register custom planner providers.

    Args:
        registry_func: Function to register providers.
                      Signature: registry_func(provider: str, factory: Callable)
    """
    registry_func("my_provider", my_factory_function)
```

### Adapter Factory

Your factory function must return an object that implements the `PlannerAdapter` protocol:

```python
from shoemaker-elves.planners.base import PlannerAdapter
from shoemaker-elves.planners.types import TaskSpec, ReviewSpec

class MyCustomAdapter:
    """Custom planner adapter for My Provider."""

    def __init__(self, api_key: str, model: str, **kwargs):
        """Initialize the adapter with provider-specific parameters."""
        self.api_key = api_key
        self.model = model
        # Initialize your client here

    def plan_batch(
        self,
        project_description: str,
        repo_summary: str,
        batch_size: int,
    ) -> list[TaskSpec]:
        """
        Generate a batch of tasks.

        Returns:
            List of TaskSpec objects, or empty list if complete
        """
        # Call your LLM API and parse response
        # Return list of TaskSpec(title="...", prompt="...")
        pass

    def review_batch(
        self,
        project_description: str,
        repo_summary: str,
        task_results: list[dict],
    ) -> ReviewSpec:
        """
        Review batch results and update summary.

        Returns:
            ReviewSpec(cumulative_summary="...", batch_assessment="...")
        """
        # Call your LLM API and parse response
        # Return ReviewSpec with cumulative_summary and batch_assessment
        pass


def my_factory(**kwargs) -> MyCustomAdapter:
    """Factory function for creating adapter instances."""
    api_key = kwargs.pop("api_key")
    model = kwargs.pop("model", "default-model")
    # Remove provider arg
    kwargs.pop("provider", None)
    return MyCustomAdapter(api_key=api_key, model=model, **kwargs)
```

## Types Reference

### TaskSpec

```python
from dataclasses import dataclass

@dataclass
class TaskSpec:
    title: str    # Short task title
    prompt: str   # Full task description/prompt (markdown)
```

### ReviewSpec

```python
from dataclasses import dataclass

@dataclass
class ReviewSpec:
    cumulative_summary: str      # Updated project summary
    batch_assessment: str        # Assessment of this batch
    issues: list[str]            # Optional list of issues found
    project_complete: bool       # Whether project is complete
    completion_percentage: int   # Estimated completion (0-100)
    recommendations: str         # Optional recommendations
```

## Example: Creating a Plugin

### 1. Project Structure

```
my_planner_plugin/
├── pyproject.toml
├── src/
│   └── my_planner/
│       ├── __init__.py
│       └── adapter.py
└── README.md
```

### 2. Implement the Adapter

`src/my_planner/adapter.py`:

```python
"""Custom planner adapter for My Provider."""

import requests
from shoemaker-elves.planners.types import TaskSpec, ReviewSpec


class MyProviderAdapter:
    """Adapter for My Provider API."""

    def __init__(self, api_key: str, model: str = "my-model-v1", **kwargs):
        self.api_key = api_key
        self.model = model
        self.base_url = kwargs.get("base_url", "https://api.myprovider.com")

    def plan_batch(
        self,
        project_description: str,
        repo_summary: str,
        batch_size: int,
    ) -> list[TaskSpec]:
        """Generate tasks using My Provider API."""
        prompt = self._build_planning_prompt(
            project_description, repo_summary, batch_size
        )

        # Call your API
        response = requests.post(
            f"{self.base_url}/v1/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "prompt": prompt}
        )
        response.raise_for_status()

        # Parse response and return TaskSpec list
        result = response.json()
        # ... parse your response format ...
        return [TaskSpec(title="Task 1", prompt="Full task description...")]

    def review_batch(
        self,
        project_description: str,
        repo_summary: str,
        task_results: list[dict],
    ) -> ReviewSpec:
        """Review tasks using My Provider API."""
        prompt = self._build_review_prompt(
            project_description, repo_summary, task_results
        )

        # Call your API
        response = requests.post(
            f"{self.base_url}/v1/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "prompt": prompt}
        )
        response.raise_for_status()

        # Parse response and return ReviewSpec
        result = response.json()
        # ... parse your response format ...
        return ReviewSpec(
            cumulative_summary="Updated summary...",
            batch_assessment="Batch completed successfully...",
            project_complete=False,
        )

    def _build_planning_prompt(self, desc: str, summary: str, size: int) -> str:
        """Build prompt for task planning."""
        # Construct your prompt
        return f"Project: {desc}\nProgress: {summary}\nGenerate {size} tasks..."

    def _build_review_prompt(self, desc: str, summary: str, results: list) -> str:
        """Build prompt for batch review."""
        # Construct your prompt
        return f"Project: {desc}\nReview these results..."
```

### 3. Create Registration Function

`src/my_planner/__init__.py`:

```python
"""My Planner Plugin for GPT Agent Orchestrator."""

from .adapter import MyProviderAdapter


def register(registry_func):
    """
    Register the My Provider planner adapter.

    Args:
        registry_func: Function to register providers
    """
    def my_provider_factory(**kwargs):
        """Factory for My Provider adapter."""
        api_key = kwargs.pop("api_key")
        model = kwargs.pop("model", "my-model-v1")
        kwargs.pop("provider", None)  # Remove provider arg
        return MyProviderAdapter(api_key=api_key, model=model, **kwargs)

    registry_func("my_provider", my_provider_factory)
```

### 4. Configure Entrypoint

`pyproject.toml`:

```toml
[project]
name = "my-planner-plugin"
version = "0.1.0"
description = "My Provider plugin for GPT Agent Orchestrator"
requires-python = ">=3.9"
dependencies = [
    "gpt-agent-orchestrator",
    "requests>=2.31.0",
]

[project.entry-points."gpt_orch.planners"]
my_provider = "my_planner:register"

[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"
```

### 5. Install and Test

```bash
# Install in development mode
pip install -e .

# Test that your provider is available
shoemaker-elves init
# Select "my_provider" from the list

# Run with your provider
shoemaker-elves gpt "Build a web app" \
    --planner-provider my_provider \
    --planner-api-key YOUR_API_KEY \
    --planner-model my-model-v1
```

## Best Practices

### Error Handling

- Always validate required parameters in your factory
- Raise `ValueError` for configuration errors
- Raise `RuntimeError` for API failures
- Let exceptions propagate - the orchestrator will handle retries

### API Keys

- Support environment variables for API keys (e.g., `MY_PROVIDER_API_KEY`)
- Never hardcode credentials
- Document environment variables in your README

### Models

- Provide sensible defaults for model names
- Allow users to override via `--planner-model`
- Document which models are supported

### Logging

- Use Python's `logging` module for debugging
- Log at INFO level for successful operations
- Log at WARNING for recoverable errors
- Log at ERROR for failures

```python
import logging

logger = logging.getLogger(__name__)

def plan_batch(self, ...):
    logger.info(f"Planning batch with {self.model}")
    # ... your code ...
    logger.debug(f"Got response: {response}")
```

### Testing

- Write unit tests for your adapter
- Mock external API calls
- Test error conditions (network failures, invalid responses)
- Test with the actual orchestrator in integration tests

## Troubleshooting

### Plugin Not Loading

1. Check that entrypoint is correctly defined in `pyproject.toml`
2. Verify the plugin is installed: `pip list | grep my-plugin`
3. Check orchestrator logs for warnings: `shoemaker-elves --verbose ...`

### Provider Not Available

1. Ensure plugin loaded successfully (check logs)
2. Verify registration function was called
3. Check that provider name doesn't conflict with built-ins

### Plugin Errors

1. Plugin load failures are logged as warnings (not errors)
2. Check that `register()` function signature is correct
3. Verify your factory function returns a valid adapter
4. Test your adapter independently before plugging in

## Plugin Limitations

- **Cannot override built-in providers**: Attempting to register `openai`, `anthropic`, etc. will fail
- **Load order not guaranteed**: Don't depend on other plugins being loaded
- **No plugin-to-plugin communication**: Plugins are isolated
- **Single registry per process**: All plugins share the same provider namespace

## Reference Implementations

See `examples/planner_plugin_example/` for a complete working example.

For built-in adapter implementations, review:
- `src/shoemaker-elves/planners/openai_adapter.py`
- `src/shoemaker-elves/planners/anthropic_adapter.py`
