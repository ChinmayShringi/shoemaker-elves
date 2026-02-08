# Configuration System with Init UX

## Pre-work

**Date**: 2026-02-04
**Task**: Robust config system + "init" UX (tokens, models, provider selection)

### Plan
1. Create `src/shoemaker-elves/config.py` with TOML-based config system
   - Define config file location based on OS (Linux/macOS: `~/.config/shoemaker-elves/config.toml`, Windows: `%APPDATA%\shoemaker-elves\config.toml`)
   - Implement `load_config()`, `save_config()`, and `merge_env_overrides()` functions
   - Define config schema with sections for planner, azure, and agent settings

2. Add CLI subcommands for configuration management
   - `shoemaker-elves init` - Interactive setup wizard
   - `shoemaker-elves config show` - Display effective config (masking secrets)
   - `shoemaker-elves config set <key> <value>` - Update config values using dot-path notation

3. Implement environment variable override support
   - Define env var names for all config options
   - Ensure env vars take precedence over file config
   - Flags override everything

4. Integrate config loading into existing CLI
   - Update `parse_args()` to use config defaults
   - Maintain backward compatibility with existing flags
   - Ensure flags override config values

5. Add unit tests for config system
   - Test config load/merge logic
   - Test secret masking
   - Test environment variable overrides
   - Test priority chain (flags > env > config > defaults)

### Files to be affected
- `src/shoemaker-elves/config.py` (new) - Core config system
- `src/shoemaker-elves/cli.py` - Integration with CLI, new subcommands
- `src/shoemaker-elves/gpt_planner.py` - Support for multiple providers
- `tests/test_config.py` (new) - Unit tests
- `pyproject.toml` - Add toml dependency if needed
- `README.md` - Update with config documentation

### Dependencies
- `tomli` / `tomli-w` libraries for TOML parsing (Python 3.11+ has tomllib built-in for reading)
- OpenAI SDK (already present)
- Anthropic SDK (for anthropic provider)
- Azure OpenAI SDK (for azure provider)

### Assumptions
- Config file location follows XDG Base Directory spec on Linux/macOS
- TOML format is preferred over JSON
- Existing CLI flags take highest precedence
- API keys can be stored in config file OR environment variables (user choice)
- Multiple provider support (OpenAI, Anthropic, Azure OpenAI, DeepSeek, OpenAI-compatible)
- Default behavior remains unchanged unless config file exists

---

## Post-work

**Completed**: 2026-02-04
**Status**: Completed

### Changes Made
- Created comprehensive TOML-based configuration system with support for multiple LLM providers
- Implemented interactive `shoemaker-elves init` wizard for easy setup
- Added `shoemaker-elves config show` and `shoemaker-elves config set` commands for configuration management
- Integrated config system into existing CLI with proper priority chain (flags > env > config > defaults)
- Added environment variable override support for all configuration options
- Implemented secret masking for API keys and sensitive data
- Created 10 unit tests covering all config functionality
- Updated README with comprehensive configuration documentation

### Files Modified
- `src/shoemaker-elves/config.py` (new) — Core configuration system with TOML support
  - Implements load_config(), save_config(), merge_env_overrides()
  - Handles platform-specific config directories
  - Provides secret masking and dot-path value access
  - Supports type conversion for env vars (int, float, bool, string)

- `src/shoemaker-elves/cli.py` — Integrated config system
  - Added import statements for config functions
  - Refactored parse_args() to use subparsers for init/config/run commands
  - Added cmd_init() for interactive configuration wizard
  - Added cmd_config_show() and cmd_config_set() for config management
  - Modified Orchestrator class to load and merge config
  - Added _apply_flag_overrides() to implement priority chain
  - Updated validate() to use config-based API keys and provider settings
  - Updated all references to self.args to use self.config where appropriate

- `src/shoemaker-elves/gpt_planner.py` — Multi-provider support
  - Extended GPTPlanner.__init__() to accept provider-specific parameters
  - Added support for Azure OpenAI, Anthropic, DeepSeek, and OpenAI-compatible APIs
  - Implemented _call_anthropic() for Anthropic-specific API calls
  - Updated _call_gpt() to route calls based on provider

- `pyproject.toml` — Added dependencies
  - Added tomli>=2.0.0 for Python < 3.11 (TOML reading)
  - Added tomli-w>=1.0.0 (TOML writing)
  - Added optional [anthropic] dependency group
  - Added [all] dependency group for all providers

- `tests/test_config.py` (new) — Comprehensive unit tests
  - test_load_default_config — Tests default config loading
  - test_save_and_load_config — Tests config persistence
  - test_merge_env_overrides — Tests environment variable merging
  - test_merge_env_overrides_provider_api_key — Tests provider-specific API keys
  - test_mask_secrets — Tests secret masking functionality
  - test_set_config_value — Tests dot-path value setting
  - test_get_config_value — Tests dot-path value retrieval
  - test_parse_env_value_types — Tests type conversion
  - test_env_override_priority — Tests override priority
  - test_config_preserves_new_keys — Tests backward compatibility

- `README.md` — Updated documentation
  - Added comprehensive Configuration section
  - Documented shoemaker-elves init wizard
  - Documented config file format and locations
  - Listed all environment variables
  - Explained priority chain
  - Listed supported providers
  - Updated CLI reference with new commands
  - Updated installation instructions for provider-specific dependencies

### Key Decisions
1. **TOML over JSON**: TOML is more human-friendly for configuration files, with better comment support. Used tomli/tomli-w for compatibility across Python versions.

2. **XDG Base Directory compliance**: Following platform conventions makes the tool feel native on Linux/macOS, while using appropriate locations on Windows.

3. **Three-tier priority system**: Flags > Env Vars > Config File ensures maximum flexibility while maintaining predictability.

4. **Provider abstraction**: GPTPlanner now supports multiple providers through a unified interface, making it easy to switch between OpenAI, Anthropic, Azure, etc.

5. **Interactive wizard**: The `init` command provides a user-friendly onboarding experience, reducing the barrier to entry.

6. **Secret masking by default**: API keys are masked in `config show` by default, with an explicit `--no-mask` flag for when needed.

7. **Backward compatibility**: Existing flags and behavior are preserved. Config only applies when the config file exists or is explicitly created.

8. **Separate optional dependencies**: Users only install SDKs for the providers they need, reducing dependency bloat.

### Issues & Resolutions
- **Issue**: Initially forgot to handle the case where tomli-w is not installed
  - **Resolution**: Added error message in save_config() directing users to install tomli-w

- **Issue**: CLI argument parsing became complex with subcommands
  - **Resolution**: Used argparse subparsers with fallback logic to maintain backward compatibility with positional project_dir argument

- **Issue**: Anthropic API has different structure than OpenAI
  - **Resolution**: Created separate _call_anthropic() method that handles Anthropic's messages API structure

### Testing Results

All acceptance criteria met:

✅ `shoemaker-elves init` creates a config file at the correct platform-specific location
✅ `shoemaker-elves config show` displays effective config with secrets masked
✅ `shoemaker-elves config show --no-mask` displays secrets unmasked
✅ `shoemaker-elves config set` updates config values successfully
✅ Environment variable overrides work correctly (tested with SHOEMAKER_ELVES_PLANNER_MODEL and SHOEMAKER_ELVES_PLANNER_PROVIDER)
✅ All 10 unit tests pass
✅ Existing CLI flags still work (backward compatibility maintained)
✅ Config priority chain works correctly: flags > env > config > defaults

### Additional Notes
- Config system is fully functional for all documented providers
- Provider-specific API key environment variables work correctly
- The system gracefully handles missing config files (falls back to defaults)
- Secret masking protects against accidental exposure of credentials
- The interactive wizard makes setup accessible to non-technical users
