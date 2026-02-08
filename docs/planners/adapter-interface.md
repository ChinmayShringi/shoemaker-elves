# Planner Adapter Interface

## Pre-work

**Date**: 2026-02-04
**Task**: Planner adapter interface (provider-agnostic) + OpenAI implementation

### Plan

1. Create `planners/types.py` with data classes:
   - `TaskSpec`: Represents a single task with title and prompt
   - `ReviewSpec`: Represents batch assessment results with summary, issues, and completion status

2. Create `planners/base.py` with Protocol:
   - `PlannerAdapter` protocol defining the interface for all planner implementations
   - Two main methods: `plan_batch()` and `review_batch()`

3. Create `planners/openai_adapter.py`:
   - Implement `OpenAIAdapter` class that conforms to the protocol
   - Support standard OpenAI API and OpenAI-compatible endpoints
   - Use official OpenAI Python SDK
   - Include JSON schema validation with clear error messages

4. Create `planners/registry.py`:
   - Provider registration system mapping provider strings to adapter factories
   - Support for `openai` and `openai_compatible` providers initially

5. Update configuration and CLI:
   - Add planner-related settings to config.py
   - Update cli.py to accept --planner-provider, --planner-model, --planner-base-url flags

6. Migrate existing code:
   - Refactor gpt_planner.py to use the new adapter pattern
   - Maintain backward compatibility with existing functionality

7. Write comprehensive unit tests:
   - Mock OpenAI client responses
   - Test JSON parsing and validation
   - Test error handling for malformed responses

### Files to be affected

- `src/shoemaker-elves/planners/__init__.py` (new)
- `src/shoemaker-elves/planners/types.py` (new)
- `src/shoemaker-elves/planners/base.py` (new)
- `src/shoemaker-elves/planners/openai_adapter.py` (new)
- `src/shoemaker-elves/planners/registry.py` (new)
- `src/shoemaker-elves/gpt_planner.py` (modify)
- `src/shoemaker-elves/config.py` (modify)
- `src/shoemaker-elves/cli.py` (modify)
- `tests/test_openai_adapter.py` (new)

### Dependencies

- `openai` - Official OpenAI Python SDK (already in use)
- `typing` - For Protocol and type hints
- `dataclasses` - For TaskSpec and ReviewSpec
- `json` - For parsing and validating structured outputs

### Assumptions

1. The OpenAI SDK is already installed and available
2. Existing prompt templates in `templates.py` will be reused
3. The adapter pattern allows for future provider additions (Anthropic, etc.) without breaking changes
4. JSON schema validation will use prompt-based instructions rather than function calling
5. All adapters should return structured data that can be validated consistently
6. Error handling should provide actionable feedback to users when LLM responses are malformed

## Post-work

**Completed**: 2026-02-04
**Status**: Completed

### Changes Made

Successfully implemented a clean provider-agnostic planner adapter system for the GPT Agent Orchestrator:

1. **Created planner adapter infrastructure**:
   - Defined `TaskSpec` and `ReviewSpec` dataclasses for structured data exchange
   - Created `PlannerAdapter` protocol defining the interface all planners must implement
   - Built a registry system for registering and creating planner instances

2. **Implemented OpenAI adapter**:
   - Full support for standard OpenAI API (api.openai.com)
   - Support for OpenAI-compatible endpoints via configurable `base_url`
   - Comprehensive JSON validation with clear, actionable error messages
   - Retry logic for rate limits and transient API errors

3. **Updated CLI and configuration**:
   - Added new CLI flags: `--planner-provider`, `--planner-model`, `--planner-base-url`
   - Maintained backward compatibility with legacy flags (`--gpt-model`, `--provider`, `--base-url`)
   - Config system already had planner settings, no changes needed

4. **Migrated existing code**:
   - Updated `gpt_planner.py` to use adapter system for `openai` and `openai_compatible` providers
   - Maintained full backward compatibility with legacy direct client initialization
   - Preserved support for Azure OpenAI, Anthropic, and DeepSeek providers using legacy code path

5. **Comprehensive test coverage**:
   - 34 unit tests total across 3 test modules
   - Mock-based testing of OpenAI client interactions
   - Validation of JSON parsing, error handling, and retry logic
   - Tests for registry, types, and adapter functionality
   - All tests passing

### Files Modified

- `src/shoemaker-elves/planners/__init__.py` — Package initialization, exports adapter interface
- `src/shoemaker-elves/planners/types.py` — TaskSpec and ReviewSpec dataclasses with serialization
- `src/shoemaker-elves/planners/base.py` — PlannerAdapter protocol definition
- `src/shoemaker-elves/planners/openai_adapter.py` — OpenAI adapter implementation with validation
- `src/shoemaker-elves/planners/registry.py` — Provider registration and factory system
- `src/shoemaker-elves/gpt_planner.py` — Updated to use adapter pattern while maintaining backward compatibility
- `src/shoemaker-elves/cli.py` — Added new planner CLI flags with legacy flag support
- `tests/test_openai_adapter.py` — 16 tests covering OpenAI adapter functionality
- `tests/test_planner_registry.py` — 6 tests for registry and provider management
- `tests/test_planner_types.py` — 12 tests for data type serialization
- `docs/planners/adapter-interface.md` — Documentation for the adapter system

### Key Decisions

1. **Protocol-based interface**: Used Python's `Protocol` type for `PlannerAdapter` to enable structural subtyping. This allows any class implementing the required methods to be treated as a planner, without requiring explicit inheritance.

2. **Backward compatibility strategy**: The `GPTPlanner` class now attempts to use the adapter system first for supported providers (`openai`, `openai_compatible`), but falls back to legacy initialization if that fails or for unsupported providers. This ensures existing code continues to work.

3. **Simplified adapter interface**: The adapter methods (`plan_batch`, `review_batch`) use a simpler signature than the legacy `GPTPlanner` methods. The adapter handles building prompts internally using the existing template system, abstracting batch numbers and other internal details.

4. **Structured error messages**: All validation errors include specific details about what went wrong and what was expected, making debugging much easier when LLMs return malformed JSON.

5. **Factory pattern for registration**: The registry uses factory functions rather than direct class references, allowing for configuration and initialization logic to be encapsulated at the provider level.

6. **Graceful degradation in review_batch**: While `plan_batch` raises exceptions on validation errors (to prevent bad tasks from being executed), `review_batch` returns a basic ReviewSpec on parse errors, as assessments are less critical and we want to preserve cumulative progress.

### Issues & Resolutions

**Issue**: The existing `build_planning_prompt` and `build_assessment_prompt` functions expect specific parameters like `batch_num` and `max_batches` that aren't available in the simpler adapter interface.

**Resolution**: The OpenAI adapter sets reasonable defaults for these parameters internally. For `batch_num`, it uses a simplified approach (1 if no repo_summary, 2 otherwise). This works because the adapter is designed to be stateless and the orchestrator maintains the actual batch tracking. Future adapters could take different approaches.

**Issue**: Need to ensure the adapter is only created for supported providers to avoid breaking legacy functionality.

**Resolution**: The `GPTPlanner.__init__` method explicitly checks if the provider is in the supported list (`openai`, `openai_compatible`) before attempting to create an adapter. If adapter creation fails for any reason, it gracefully falls back to legacy initialization with a warning.

**Issue**: Tests need to mock the OpenAI client without pulling in the actual SDK.

**Resolution**: Used `unittest.mock.patch` to mock the `OpenAI` class import in the adapter module. This allows testing all adapter logic including API calls, retry logic, and error handling without making real network requests.

### Acceptance Criteria Verification

All acceptance criteria from the task specification have been met:

✅ GPT mode can run using `--planner-provider openai --planner-model <model>` and API key
✅ GPT mode can run using `--planner-provider openai_compatible --planner-base-url http://localhost:...`
✅ Bad JSON from model fails with actionable error messages
✅ Unit tests mock OpenAI client and validate parsing and schema enforcement
✅ All tests passing (34/34)

### Future Enhancements

The adapter system is designed to be extensible. Future providers can be added by:

1. Creating a new adapter class implementing the `PlannerAdapter` protocol
2. Registering it in `registry.py` with `register_planner(provider_name, factory_func)`
3. No changes needed to CLI or orchestrator code

Potential future providers:
- Anthropic Claude (direct API, not via OpenAI compatibility)
- Google Gemini
- Local models via llama.cpp or similar
- Azure OpenAI (migrate from legacy implementation)
