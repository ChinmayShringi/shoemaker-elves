# Example Planner Plugin

This is a minimal working example of a custom planner provider plugin for Shoemaker Elves.

## What This Demonstrates

- How to structure a planner plugin package
- How to implement the `PlannerAdapter` protocol
- How to register your provider via entrypoints
- How the plugin system discovers and loads your code

## Installation

Install this example plugin in development mode:

```bash
cd examples/planner_plugin_example
pip install -e .
```

## Usage

After installation, the `example` provider will be available to the orchestrator:

```bash
# Check that the plugin is available
shoemaker-elves init
# You should see "example" in the provider list

# Run with the example provider
shoemaker-elves gpt "Build a web app" \
    --planner-provider example \
    --planner-api-key demo-key \
    --planner-model example-model-v1
```

## How It Works

### 1. Entrypoint Registration

The plugin is registered via the `shoemaker_elves.planners` entrypoint group in `pyproject.toml`:

```toml
[project.entry-points."shoemaker_elves.planners"]
example = "example_planner:register"
```

When the orchestrator starts, it discovers this entrypoint and calls the `register` function.

### 2. Registration Function

The `register` function in `src/example_planner/__init__.py` receives a registry helper and uses it to register the provider:

```python
def register(registry_func):
    def example_factory(**kwargs):
        # Extract parameters
        api_key = kwargs.pop("api_key", "example-key")
        model = kwargs.pop("model", "example-model-v1")
        kwargs.pop("provider", None)
        return ExampleAdapter(api_key=api_key, model=model, **kwargs)

    registry_func("example", example_factory)
```

### 3. Adapter Implementation

The `ExampleAdapter` class implements the `PlannerAdapter` protocol with two required methods:

- `plan_batch()`: Generate a batch of tasks
- `review_batch()`: Review completed tasks and update project summary

This example returns mock data, but a real implementation would call an LLM API.

## Creating Your Own Plugin

Use this as a template:

1. Copy this directory structure
2. Rename `example_planner` to your plugin name
3. Update `pyproject.toml`:
   - Change `name`, `description`
   - Update entrypoint name and module path
4. Implement your adapter in `adapter.py`:
   - Add your API client code
   - Implement `plan_batch()` to call your LLM
   - Implement `review_batch()` to call your LLM
5. Update the factory in `__init__.py` to handle your parameters
6. Install and test: `pip install -e .`

## Testing

To verify the plugin works:

```bash
# Install the plugin
pip install -e .

# Check it's registered
python -c "from shoemaker-elves.planners.registry import get_available_providers; print(get_available_providers())"
# Should include 'example'

# Try running with it
shoemaker-elves gpt "test project" --planner-provider example
```

## Learn More

- See `docs/planners/plugin-development-guide.md` for detailed documentation
- Review built-in adapters in `src/shoemaker-elves/planners/` for reference implementations
- Check the `PlannerAdapter` protocol in `src/shoemaker-elves/planners/base.py`
