# Anthropic Planner Adapter

## Pre-work

**Date**: 2026-02-04
**Task**: Add Anthropic (Claude) adapter for planner mode

### Plan
1. Examine existing OpenAI adapter to understand patterns and requirements
2. Add `anthropic` Python SDK as optional dependency in pyproject.toml
3. Create `src/gpt_agent_orchestrator/planners/anthropic_adapter.py`:
   - Implement `AnthropicAdapter` class following the `PlannerAdapter` protocol
   - Use Anthropic Messages API
   - Support api_key and model parameters
   - Implement `plan_batch()` method for generating tasks
   - Implement `review_batch()` method for assessing results
   - Include retry logic similar to OpenAI adapter
4. Update `src/gpt_agent_orchestrator/planners/registry.py`:
   - Register `anthropic` provider
5. Update `src/gpt_agent_orchestrator/config.py`:
   - Add support for `GPT_ORCH_ANTHROPIC_API_KEY` environment variable
6. Update `src/gpt_agent_orchestrator/cli.py`:
   - Allow selecting `anthropic` as planner provider
7. Write comprehensive tests for the new adapter:
   - Mock Anthropic client behavior
   - Test successful plan_batch execution
   - Test successful review_batch execution
   - Test error handling (authentication, rate limits, API errors)
   - Test JSON parsing edge cases
8. Run all tests to verify implementation

### Files to be affected
- `pyproject.toml` - Add anthropic dependency
- `src/gpt_agent_orchestrator/planners/anthropic_adapter.py` (new) - Main adapter implementation
- `src/gpt_agent_orchestrator/planners/registry.py` - Register anthropic provider
- `src/gpt_agent_orchestrator/config.py` - Add anthropic API key support
- `src/gpt_agent_orchestrator/cli.py` - Add anthropic provider option
- `tests/test_anthropic_adapter.py` (new) - Unit tests for adapter

### Dependencies
- `anthropic` Python SDK (new, optional dependency)
- Existing project dependencies: dataclasses, json, time

### Assumptions
- The Anthropic Messages API will be used (similar to OpenAI Chat Completions)
- JSON mode can be achieved through system prompts (Anthropic doesn't have explicit JSON mode like OpenAI)
- The existing template system (TASK_PLANNING_SYSTEM_PROMPT, ASSESSMENT_SYSTEM_PROMPT) will work with Claude
- Error handling patterns from OpenAI adapter are applicable to Anthropic
- Claude models will follow the same JSON output contract as OpenAI (TaskSpec and ReviewSpec)
- Default model will be "claude-sonnet-4-5-20250929" (current latest Sonnet)

## Post-work

**Completed**: 2026-02-04
**Status**: Completed

### Changes Made
- Implemented `AnthropicAdapter` class in `src/gpt_agent_orchestrator/planners/anthropic_adapter.py`
- Registered `anthropic` provider in the planner registry
- Updated CLI to support selecting Anthropic as planner provider
- Added comprehensive test suite with 19 test cases covering all functionality
- Updated registry tests to verify Anthropic provider registration
- Confirmed config system already supported `GPT_ORCH_ANTHROPIC_API_KEY` environment variable
- Confirmed pyproject.toml already had anthropic dependency as optional extra

### Files Modified
- `src/gpt_agent_orchestrator/planners/anthropic_adapter.py` (created) — Main Anthropic adapter implementation with plan_batch and review_batch methods
- `src/gpt_agent_orchestrator/planners/registry.py` — Added import for AnthropicAdapter and registered `anthropic` provider with factory function
- `src/gpt_agent_orchestrator/cli.py` — Updated `--planner-provider` help text to include `anthropic` and set default model to `claude-sonnet-4-5-20250929`
- `tests/test_anthropic_adapter.py` (created) — Comprehensive test suite with 19 tests covering initialization, plan_batch, review_batch, and error handling
- `tests/test_planner_registry.py` — Added test for creating Anthropic planner and updated provider list assertion
- `docs/planners/anthropic-adapter.md` (created) — Pre-work and post-work documentation

### Key Decisions
1. **JSON Output Strategy**: Enhanced system prompt with explicit JSON instruction since Anthropic doesn't have OpenAI's `response_format` parameter. Added note: "You must respond with valid JSON only. Do not include any text before or after the JSON object."

2. **Response Content Handling**: Anthropic Messages API returns content as an array of text blocks. Implemented logic to concatenate all text blocks with `text` attribute to handle potential multi-block responses.

3. **Model Default**: Selected `claude-sonnet-4-5-20250929` as default model (current latest Sonnet 4.5) to match modern Claude capabilities.

4. **Error Handling**: Mirrored OpenAI adapter's retry logic with 3 max retries, exponential backoff for API errors, and 30-second wait for rate limits.

5. **Test Coverage**: Included edge case test for empty response content and multiple text blocks to ensure robust content extraction.

### Issues & Resolutions
- **Issue**: Anthropic doesn't have explicit JSON mode like OpenAI's `response_format: {"type": "json_object"}`
  - **Resolution**: Enhanced system prompt with explicit JSON instructions to guide Claude to output valid JSON

- **Issue**: Anthropic response structure differs from OpenAI (content is array of blocks vs single string)
  - **Resolution**: Implemented content extraction logic that iterates through all content blocks and concatenates text

- **Issue**: Initially unclear what default model name to use for Anthropic
  - **Resolution**: Used official model ID `claude-sonnet-4-5-20250929` from Anthropic's latest Sonnet 4.5 release

### Verification
- All 64 tests pass (19 new Anthropic adapter tests + existing tests)
- Anthropic provider successfully registered and discoverable via `get_available_providers()`
- CLI properly supports `--planner-provider anthropic` argument
- Config system correctly reads `GPT_ORCH_ANTHROPIC_API_KEY` environment variable
- Optional dependency structure allows installation with `pip install gpt-agent-orchestrator[anthropic]`

### Usage Example
```bash
# Using environment variable for API key
export GPT_ORCH_ANTHROPIC_API_KEY=your-api-key-here
gpt-orch ~/project --gpt --planner-provider anthropic --planner-model claude-sonnet-4-5-20250929 -d "Build a REST API"

# Using init command to configure
gpt-orch init
# Select option 2 for Anthropic
# Model: claude-sonnet-4-5-20250929
# API key: Set via environment variable GPT_ORCH_ANTHROPIC_API_KEY
```
