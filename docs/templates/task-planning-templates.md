# Task Planning Templates

## Pre-work

**Date**: 2026-02-04
**Task**: Upgrade templates for amazing task planning with atomic tasks and acceptance criteria

## Post-work

**Completed**: 2026-02-04
**Status**: Completed

### Changes Made

1. **Enhanced TaskSpec Data Model** (`src/chainsmith/planners/types.py`)
   - Added new fields to TaskSpec: `id`, `summary`, `steps`, `files`, `acceptance_checks`, `risks`, `constraints`
   - Updated `to_dict()` and `from_dict()` methods to support new fields
   - All fields are optional except `title` and `prompt` for backward compatibility

2. **Enhanced ReviewSpec Data Model** (`src/chainsmith/planners/types.py`)
   - Added `next_tasks` field to ReviewSpec for structured next-step planning
   - Updated serialization/deserialization methods

3. **Upgraded Planning Prompt** (`src/chainsmith/templates.py`)
   - Rewrote TASK_PLANNING_SYSTEM_PROMPT with enhanced structure and guards
   - Added task quality standards (atomic, specific files, clear steps, acceptance checks, risk awareness, constraints)
   - Added output constraints (JSON-only output, batch size enforcement, strict schema)
   - Included comprehensive example of a well-formed task
   - Enforces minimal diffs and incremental builds

4. **Upgraded Review Prompt** (`src/chainsmith/templates.py`)
   - Rewrote ASSESSMENT_SYSTEM_PROMPT with structured output requirements
   - Added next-task generation capability
   - Added detection of missing requirements
   - Included comprehensive example output

5. **Prompt Validator Utility** (`src/chainsmith/prompt_validator.py`)
   - Created PromptValidator class with comprehensive validation
   - Validates planning responses (tasks structure, batch size, field presence)
   - Validates review responses (all required fields, next_tasks structure)
   - Validates individual tasks (required fields, types, quality checks)
   - Provides detailed error messages for repair mechanism
   - `ValidationError` exception for validation failures

6. **Adapter Integration**
   - Updated OpenAI adapter (`src/chainsmith/planners/openai_adapter.py`)
   - Updated Anthropic adapter (`src/chainsmith/planners/anthropic_adapter.py`)
   - Updated Azure OpenAI adapter (`src/chainsmith/planners/azure_openai_adapter.py`)
   - All adapters now use PromptValidator before processing responses
   - Validation failures trigger existing repair mechanism

7. **Comprehensive Test Coverage**
   - Updated existing tests in `tests/test_planner_types.py` for enhanced fields
   - Created `tests/test_prompt_validator.py` with 42 test cases
   - All 141 tests passing

### Files Modified

- `src/chainsmith/planners/types.py` — Enhanced TaskSpec and ReviewSpec dataclasses
- `src/chainsmith/templates.py` — Rewrote planning and review prompts
- `src/chainsmith/prompt_validator.py` — New validation utility (created)
- `src/chainsmith/planners/openai_adapter.py` — Integrated validator
- `src/chainsmith/planners/anthropic_adapter.py` — Integrated validator
- `src/chainsmith/planners/azure_openai_adapter.py` — Integrated validator
- `tests/test_planner_types.py` — Updated and expanded tests
- `tests/test_prompt_validator.py` — New comprehensive test suite (created)
- `tests/test_azure_openai_adapter.py` — Updated assertion to match new validation
- `docs/templates/task-planning-templates.md` — Documentation (this file)

### Key Decisions

1. **Backward Compatibility**: All new TaskSpec fields are optional to maintain compatibility with existing code
2. **Provider-Agnostic Validation**: Validator works across all providers (OpenAI, Anthropic, Azure)
3. **Repair Integration**: Validation failures raise ValueError to trigger existing repair mechanism
4. **Progressive Enhancement**: Old code continues to work; new features available when populated
5. **Quality Focus**: Prompts emphasize atomic tasks, specific files, clear acceptance criteria, and constraints

### Issues & Resolutions

- **Issue**: Type check bug when title is not a string (validator tried to check length of non-string)
  - **Resolution**: Added isinstance check before length validation

- **Issue**: Test failures due to error message format changes
  - **Resolution**: Updated error messages to be backward compatible with existing tests

### Status

✅ All acceptance checks passed:
- Planner produces tasks with acceptance checks and file lists
- Review produces structured next steps and cumulative summary
- All 141 tests passing
- Validator enforces JSON structure
- Repair mechanism triggered on validation failures

### Plan

1. **Analyze Current State**
   - Review existing `templates.py` structure
   - Understand current JSON format for tasks and assessments
   - Identify gaps in atomic task specification

2. **Design Enhanced JSON Schema**
   - Add fields: `id`, `summary`, `steps`, `files`, `acceptance_checks`, `risks`
   - Add "do not do" constraints field
   - Design structured review output with next-step plans

3. **Rewrite Planning Prompt**
   - Force structured JSON output with all new fields
   - Add prompt guards (no prose outside JSON, respect batch_size)
   - Include examples of well-formed tasks
   - Add constraints for minimal diffs and incremental builds

4. **Rewrite Review Prompt**
   - Structured output for changes summary
   - Detection of missing requirements
   - Next batch task generation if needed
   - Clear completion criteria

5. **Implement Prompt Validator**
   - JSON schema validation for required fields
   - Non-empty field checks
   - Integration with repair mechanism (from task 7)
   - Clear error messages for validation failures

6. **Testing**
   - Unit tests for validator
   - Integration test with sample project
   - Verify JSON parsing and validation flow

### Files to be affected

- `src/chainsmith/templates.py` — Update prompts with new structure
- `src/chainsmith/gpt_planner.py` — Add validator integration
- `tests/test_templates.py` — New test file for template validation
- `tests/test_prompt_validator.py` — New test file for validator

### Dependencies

- Existing repair mechanism from task 7 (error recovery in `gpt_planner.py`)
- Python's `json` module for validation
- Pydantic (optional, for stronger schema validation)

### Assumptions

- Current task execution flow in `gpt_planner.py` can accommodate new JSON fields
- The repair mechanism from task 7 is compatible with validation errors
- Planners will respect the new JSON structure and produce valid output
- Files modified tracking in task results is already captured correctly
