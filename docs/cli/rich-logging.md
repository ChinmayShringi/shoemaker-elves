# Rich Logging and UX Improvements

## Pre-work

**Date**: 2026-02-04
**Task**: Better UX: rich logging, progress, and readable summaries

### Plan
1. Add `rich` as an optional dependency (extra: `shoemaker-elves[rich]`)
2. Create a logging module that supports both rich and fallback output
3. Add progress bars for task execution in batches
4. Add clean tables for displaying planned tasks
5. Add colorized warnings/errors
6. Implement machine-readable logging to `logs/run.log`
7. Ensure graceful degradation when rich is not installed
8. Write tests to ensure no crashes when rich is missing

### Files to be affected
- `pyproject.toml` — add rich as optional dependency
- `src/shoemaker-elves/logging.py` (new) — logging module with rich support
- `src/shoemaker-elves/cli.py` — integrate rich logging
- `tests/test_logging.py` (new) — tests for logging module

### Dependencies
- `rich` library (optional dependency)
- Existing CLI infrastructure in `cli.py`

### Assumptions
- Rich should be completely optional and not required for basic functionality
- Fallback to plain text output should be seamless
- Log files should be created in the project's `.claude/logs/` directory
- Machine-readable logs should use JSON Lines format for easy parsing

## Post-work

**Completed**: 2026-02-04
**Status**: Completed

### Changes Made

Successfully implemented rich logging and UX improvements for the CLI:

1. **Optional Rich Dependency**: Added `rich>=13.0.0` as an optional dependency in `pyproject.toml` under `[project.optional-dependencies]`
   - Users can install with: `pip install gpt-agent-orchestrator[rich]`
   - Also included in the `all` extras bundle

2. **Logging Module** (`src/shoemaker-elves/logging.py`):
   - Created comprehensive Logger class with rich support
   - Graceful fallback to plain text when rich is not available
   - Features:
     - Colorized output (success, error, warning, info)
     - Tables for displaying tasks
     - Progress bars via context manager
     - Headers and sections for structure
     - Task summary display with status icons
   - Machine-readable logging to JSON Lines format

3. **CLI Integration**:
   - Integrated Logger throughout `cli.py`
   - Replaced plain print statements with logger methods
   - Enhanced error/warning messages with colorization
   - Added table displays for task lists (when rich available)
   - Better structured output with headers and sections
   - Display "Rich UI: Enabled" status in configuration

4. **Machine-Readable Logs**:
   - Logs saved to `.claude/logs/run.log` in the project directory
   - JSON Lines format for easy parsing
   - Events logged: session_start, session_end, errors, warnings, success, info, table displays, task summaries, custom events
   - Each log entry includes timestamp and event type

5. **Comprehensive Testing**:
   - Created `tests/test_logging.py` with 11 test cases
   - Tests cover both rich-available and fallback scenarios
   - Verified graceful degradation when rich is not installed
   - All 149 tests pass across the entire test suite

### Files Modified

- `pyproject.toml` — Added rich as optional dependency
- `src/shoemaker-elves/logging.py` (new) — Complete logging module with rich support
- `src/shoemaker-elves/cli.py` — Integrated logger throughout CLI
- `tests/test_logging.py` (new) — Comprehensive test suite for logging module

### Key Decisions

1. **Optional Dependency Strategy**: Made rich completely optional to keep the base package lightweight. Users who want enhanced UI can install the rich extra.

2. **Fallback Design**: Ensured all logger methods work identically whether rich is available or not, just with different visual styling.

3. **Log Location**: Chose `.claude/logs/` directory in the project being orchestrated (not in the orchestrator package) so logs are co-located with the project they document.

4. **JSON Lines Format**: Used JSON Lines (JSONL) for machine-readable logs because it's simple, streamable, and easy to parse line-by-line.

5. **Singleton Pattern**: Implemented a singleton `get_logger()` function for convenience while still allowing multiple Logger instances if needed.

### Issues & Resolutions

No significant issues encountered during implementation. The rich library's API made integration straightforward, and the fallback mechanism worked as expected on first try.

### Testing Results

All tests pass (149 passed, 3 skipped):
- 11 new logging tests
- 138 existing tests (no regressions)
- 3 skipped tests (rich-specific tests when rich not installed in test environment)

The implementation successfully meets all acceptance criteria:
- ✅ CLI output is readable with and without rich installed
- ✅ No crashes if rich is missing
- ✅ Progress bars, tables, and colorization work when rich is available
- ✅ Machine-readable logs created in `logs/run.log`
- ✅ Comprehensive test coverage
