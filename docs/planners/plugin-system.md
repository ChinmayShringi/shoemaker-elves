# Plugin System for Custom Planner Providers

## Pre-work

**Date**: 2026-02-04
**Task**: Add plugin system for custom planner providers (user-defined models)

### Plan

1. **Understand Current Architecture**
   - Review existing registry and planner base classes
   - Understand how built-in providers are registered

2. **Design Plugin Interface**
   - Define entrypoint group name: `gpt_orch.planners`
   - Design plugin registration API (function-based: `register(registry)`)
   - Define plugin contract and requirements

3. **Implement Plugin Loading**
   - Add plugin discovery using `importlib.metadata`
   - Load plugins on registry initialization
   - Handle plugin failures gracefully (warn, don't crash)
   - Ensure built-in providers work even if plugins fail

4. **Create Example Plugin**
   - Create `examples/planner_plugin_example/` directory
   - Implement minimal plugin package with:
     - Setup.py/pyproject.toml with entrypoint
     - Simple custom adapter implementation
     - README with usage instructions

5. **Add Documentation**
   - Document plugin interface contract
   - Provide developer guide for creating plugins
   - Add troubleshooting section

6. **Testing**
   - Unit tests for plugin discovery
   - Mock importlib.metadata for testing
   - Test plugin load failures
   - Test registry resilience

### Files to be affected

**Core Implementation:**
- `src/shoemaker-elves/planners/registry.py` - Add plugin loading
- `src/shoemaker-elves/planners/base.py` - May need plugin interface docs

**Example Plugin:**
- `examples/planner_plugin_example/pyproject.toml`
- `examples/planner_plugin_example/src/example_planner/__init__.py`
- `examples/planner_plugin_example/src/example_planner/adapter.py`
- `examples/planner_plugin_example/README.md`

**Tests:**
- `tests/test_planner_registry.py` - Add plugin loading tests

**Documentation:**
- `docs/planners/plugin-system.md` - This file (pre/post work)
- `docs/planners/plugin-development-guide.md` - Developer guide

### Dependencies

- `importlib.metadata` (stdlib in Python 3.8+)
- No new external dependencies required

### Assumptions

1. Plugins will follow the same `PlannerAdapter` interface as built-in providers
2. Plugins register themselves via a `register(registry)` function
3. Plugin failures should be non-fatal (warn and continue)
4. Built-in providers always take precedence over plugins with the same name
5. Plugins are installed as separate Python packages with entrypoints
6. Users installing plugins are comfortable with pip/poetry

---

## Post-work

**Completed**: 2026-02-04
**Status**: Completed

### Changes Made

Successfully implemented a complete plugin system for custom planner providers with the following features:

1. **Automatic Plugin Discovery**: Plugins are discovered via `importlib.metadata` entrypoints from the `gpt_orch.planners` group
2. **Graceful Error Handling**: Plugin load failures are logged as warnings but don't crash the application
3. **Built-in Protection**: Plugins cannot override built-in providers (openai, anthropic, azure_openai, deepseek, openai_compatible)
4. **Python 3.9+ Compatibility**: Supports both old (dict) and new (SelectableGroups) entrypoint APIs
5. **Complete Documentation**: Developer guide with examples, best practices, and troubleshooting
6. **Working Example**: Fully functional example plugin package demonstrating the interface

### Files Modified

**Core Implementation:**
- `src/shoemaker-elves/planners/registry.py`
  - Added `load_plugins()` function for entrypoint discovery
  - Added `_create_plugin_registrar()` helper that prevents built-in overrides
  - Added logging for plugin load success/failure
  - Plugins loaded automatically on module import
  - Handles both Python 3.9 (dict) and 3.10+ (SelectableGroups) entrypoint APIs

**Documentation:**
- `docs/planners/plugin-system.md`
  - Pre-work and post-work documentation (this file)

- `docs/planners/plugin-development-guide.md` (new)
  - Complete plugin development guide
  - Interface documentation with correct TaskSpec/ReviewSpec field names
  - Full working example with code samples
  - Best practices for error handling, logging, testing
  - Troubleshooting section

**Example Plugin:**
- `examples/planner_plugin_example/pyproject.toml` (new)
  - Package configuration with entrypoint registration
  - Minimal dependencies (just gpt-agent-orchestrator)

- `examples/planner_plugin_example/src/example_planner/__init__.py` (new)
  - Registration function with lazy adapter import
  - Factory function demonstrating parameter handling

- `examples/planner_plugin_example/src/example_planner/adapter.py` (new)
  - Complete ExampleAdapter implementation
  - Implements PlannerAdapter protocol
  - Mock implementation with extensive comments
  - Demonstrates plan_batch and review_batch methods

- `examples/planner_plugin_example/README.md` (new)
  - Installation and usage instructions
  - How it works explanation
  - Testing guidance

**Tests:**
- `tests/test_planner_registry.py`
  - Added 6 new test functions for plugin system:
    - `test_load_plugins_with_mock_entrypoint` - Basic plugin loading
    - `test_plugin_cannot_override_builtin` - Protection mechanism
    - `test_plugin_load_failure_is_non_fatal` - Error handling
    - `test_plugin_load_failure_missing_module` - Missing module handling
    - `test_entrypoint_discovery_failure` - Discovery failure handling
    - `test_plugin_with_python39_entrypoints_api` - Python 3.9 compatibility
  - All 18 tests pass (12 original + 6 new)

### Key Decisions

1. **Function-based Registration**: Chose `register(registry_func)` pattern over class-based approach for simplicity
   - Easier for plugin authors to understand
   - More flexible (can register multiple providers in one plugin)

2. **Entrypoint Group Naming**: Used `gpt_orch.planners` to match project name
   - Clear namespace
   - Follows Python packaging conventions

3. **Built-in Protection**: Plugins cannot override built-ins
   - Prevents breaking core functionality
   - Clear error message if attempted
   - Logged at INFO level when plugin registers successfully

4. **Non-fatal Loading**: Plugin failures only log warnings
   - Application remains usable with built-in providers
   - Failures are visible in logs for debugging
   - Prevents user-installed plugins from breaking the tool

5. **Lazy Import in Example**: Used lazy import to avoid circular dependencies
   - Factory function imports adapter only when called
   - Prevents module-level import issues

6. **Python 3.9 Compatibility**: Support both entrypoint APIs
   - Check for `select()` method (3.10+)
   - Fall back to dict-style access (3.9)
   - Ensures broad compatibility

### Issues & Resolutions

1. **Issue**: Initial example plugin had circular import error
   - **Symptom**: `partially initialized module 'example_planner' has no attribute 'register'`
   - **Cause**: Top-level import of adapter in `__init__.py`
   - **Resolution**: Moved adapter import inside factory function (lazy import)

2. **Issue**: Example plugin used wrong TaskSpec field names
   - **Symptom**: `TypeError: TaskSpec.__init__() got an unexpected keyword argument 'task'`
   - **Cause**: Documentation and example used old field names (task, rationale, status, new_summary)
   - **Resolution**: Updated to correct fields (title, prompt, cumulative_summary, batch_assessment, project_complete)

3. **Issue**: Example plugin initially used PlanResult/ReviewResult instead of TaskSpec/ReviewSpec
   - **Cause**: Confusion about return types (PlanResult is wrapper, TaskSpec is what adapters return)
   - **Resolution**: Clarified that adapters return list[TaskSpec] and ReviewSpec directly, not wrapped versions

### Verification

1. ✅ Plugin loads successfully: `python -c "from src.shoemaker-elves.planners.registry import get_available_providers; print(get_available_providers())"`
   - Output includes 'example' provider along with built-ins

2. ✅ Plugin adapter works: Created and tested example adapter
   - plan_batch returns TaskSpec list
   - review_batch returns ReviewSpec
   - All fields populated correctly

3. ✅ All tests pass: `pytest tests/test_planner_registry.py -v`
   - 18/18 tests pass (including 6 new plugin tests)

4. ✅ Plugin can be installed: `pip install -e examples/planner_plugin_example`
   - No errors during installation
   - Entrypoint registered correctly

### Acceptance Criteria Status

✅ **If a plugin is installed, `--planner-provider my_provider` works**
   - Example plugin registers as "example" provider
   - Can be used via `--planner-provider example`

✅ **If plugin load fails, CLI still runs and prints a warning (not crash)**
   - Tested with broken plugins (RuntimeError, ImportError)
   - Warnings logged, application continues
   - Built-in providers remain available

✅ **Unit test registry plugin discovery using importlib.metadata mocks**
   - 6 comprehensive plugin tests added
   - Mock both Python 3.9 and 3.10+ APIs
   - Test success and failure scenarios

### Future Enhancements

Possible improvements for future iterations:

1. Plugin health checks or validation on load
2. Plugin versioning and compatibility checks
3. Plugin configuration file support
4. Plugin marketplace or registry
5. Hot-reload capability for plugins during development
6. More example plugins (OpenRouter, LocalAI, Ollama)
