# DeepSeek Adapter (Planner Mode)

## Pre-work

**Date**: 2026-02-04
**Task**: Add DeepSeek support as a planner provider

### Plan

1. Update planner registry to add `deepseek` provider using OpenAIAdapter
2. Add config defaults:
   - Default base_url to `https://api.deepseek.com` when provider is `deepseek`
   - Map `CHAINSMITH_DEEPSEEK_API_KEY` environment variable to api_key
3. Update config.py to handle DeepSeek-specific defaults
4. Write tests to verify:
   - Provider selection uses correct base_url
   - API key mapping works correctly
   - User can override base_url
5. Verify acceptance criteria

### Files to be affected

- `src/chainsmith/planners/registry.py` - Add deepseek provider mapping
- `src/chainsmith/config.py` - Add DeepSeek defaults and env var mapping
- `tests/test_planner_registry.py` - Add tests for deepseek provider
- `tests/test_config.py` - Add tests for DeepSeek configuration

### Dependencies

- OpenAI SDK (already in use via openai_adapter.py)
- DeepSeek API (OpenAI-compatible endpoint at api.deepseek.com)

### Assumptions

- DeepSeek API is fully OpenAI-compatible
- No special DeepSeek-specific adapter code needed
- DeepSeek uses similar model naming conventions to OpenAI
- Default model for DeepSeek will be handled by existing model selection logic

## Post-work

**Completed**: 2026-02-04
**Status**: Completed

### Changes Made

1. Added DeepSeek provider to the planner registry using OpenAIAdapter
2. Implemented automatic default base_url (`https://api.deepseek.com`) for DeepSeek provider
3. Added `CHAINSMITH_DEEPSEEK_API_KEY` environment variable support in config system
4. Created `_apply_provider_defaults()` helper function in config.py to handle provider-specific defaults
5. Updated CLI help text to include DeepSeek in provider lists
6. Enhanced init command to support DeepSeek with optional custom base_url
7. Wrote comprehensive tests for DeepSeek configuration and registry

### Files Modified

- `src/chainsmith/planners/registry.py` — Added `_deepseek_factory()` and registered "deepseek" provider
- `src/chainsmith/config.py` — Added "deepseek" to `PROVIDER_API_KEY_ENV_VARS` and implemented `_apply_provider_defaults()` function
- `src/chainsmith/cli.py` — Updated provider help text and added DeepSeek base_url prompt in init command
- `tests/test_planner_registry.py` — Added `test_create_deepseek_planner()` and `test_create_deepseek_planner_custom_base_url()` tests
- `tests/test_config.py` — Added `test_merge_env_overrides_deepseek_api_key()`, `test_deepseek_default_base_url()`, and `test_deepseek_custom_base_url()` tests

### Key Decisions

1. **Reuse OpenAIAdapter**: DeepSeek API is OpenAI-compatible, so we use the existing OpenAIAdapter rather than creating a new adapter class
2. **Default base_url**: Automatically set base_url to `https://api.deepseek.com` when provider is "deepseek" and no base_url is provided
3. **Provider-specific defaults pattern**: Created `_apply_provider_defaults()` helper to centralize provider-specific default logic, making it easy to add more providers in the future
4. **User override support**: Users can still provide custom base_url via config file, CLI args, or environment variables, which will override the default
5. **Default model**: Set "deepseek-chat" as the default model for DeepSeek in the init command

### Issues & Resolutions

- No issues encountered. Implementation was straightforward due to DeepSeek's OpenAI compatibility.

### Acceptance Criteria Verification

All acceptance criteria met:

✅ `--planner-provider deepseek` uses the DeepSeek API key from `CHAINSMITH_DEEPSEEK_API_KEY`
✅ Default base_url is automatically set to `https://api.deepseek.com`
✅ Users can override base_url via `--planner-base-url` flag or config
✅ All 90 tests pass (including 5 new DeepSeek-specific tests)
