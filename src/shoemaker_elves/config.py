"""
Configuration system for Shoemaker Elves.

Supports TOML config files with environment variable overrides.
Config file locations:
  - Linux/macOS: ~/.config/shoemaker-elves/config.toml
  - Windows: %APPDATA%\\shoemaker-elves\\config.toml
"""

import os
import sys
from pathlib import Path
from typing import Any

# Python 3.11+ has tomllib built-in for reading TOML
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

# For writing TOML, we need tomli_w
try:
    import tomli_w
except ImportError:
    tomli_w = None


def get_config_dir() -> Path:
    """Get the platform-specific config directory."""
    if sys.platform == "win32":
        # Windows: %APPDATA%\shoemaker-elves
        appdata = os.environ.get("APPDATA")
        if not appdata:
            raise RuntimeError("APPDATA environment variable not found")
        return Path(appdata) / "shoemaker-elves"
    else:
        # Linux/macOS: ~/.config/shoemaker-elves
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            return Path(xdg_config) / "shoemaker-elves"
        return Path.home() / ".config" / "shoemaker-elves"


def get_config_path() -> Path:
    """Get the full path to the config file."""
    return get_config_dir() / "config.toml"


# Environment variable mapping
ENV_VAR_MAP = {
    "planner.provider": "SHOEMAKER_ELVES_PLANNER_PROVIDER",
    "planner.model": "SHOEMAKER_ELVES_PLANNER_MODEL",
    "planner.api_key": "SHOEMAKER_ELVES_OPENAI_API_KEY",  # Default for openai
    "planner.base_url": "SHOEMAKER_ELVES_PLANNER_BASE_URL",
    "planner.max_cost_usd": "SHOEMAKER_ELVES_MAX_COST_USD",
    "azure.endpoint": "SHOEMAKER_ELVES_AZURE_ENDPOINT",
    "azure.deployment": "SHOEMAKER_ELVES_AZURE_DEPLOYMENT",
    "azure.api_version": "SHOEMAKER_ELVES_AZURE_API_VERSION",
    "azure.api_key": "SHOEMAKER_ELVES_AZURE_OPENAI_API_KEY",
    "agent.model": "SHOEMAKER_ELVES_AGENT_MODEL",
}

# Provider-specific API key env vars
PROVIDER_API_KEY_ENV_VARS = {
    "openai": "SHOEMAKER_ELVES_OPENAI_API_KEY",
    "anthropic": "SHOEMAKER_ELVES_ANTHROPIC_API_KEY",
    "azure_openai": "SHOEMAKER_ELVES_AZURE_OPENAI_API_KEY",
    "deepseek": "SHOEMAKER_ELVES_DEEPSEEK_API_KEY",
    "openai_compatible": "SHOEMAKER_ELVES_OPENAI_API_KEY",
}

# Default config schema
DEFAULT_CONFIG = {
    "planner": {
        "provider": "openai",
        "model": "gpt-5.2",
        "max_cost_usd": 50.0,
    },
    "azure": {
        "api_version": "2024-02-01",
    },
    "agent": {
        "model": "sonnet",
    },
}


def load_config() -> dict[str, Any]:
    """Load config from file, or return default config if file doesn't exist.

    Returns:
        Config dictionary with sections: planner, azure, agent
    """
    config_path = get_config_path()

    if not config_path.exists():
        return _deep_copy_dict(DEFAULT_CONFIG)

    if tomllib is None:
        print("Warning: TOML support not available. Install tomli for Python < 3.11.")
        return _deep_copy_dict(DEFAULT_CONFIG)

    try:
        with open(config_path, "rb") as f:
            loaded = tomllib.load(f)

        # Merge with defaults (in case new keys were added)
        config = _deep_copy_dict(DEFAULT_CONFIG)
        _deep_merge(config, loaded)
        return config

    except Exception as e:
        print(f"Warning: Failed to load config from {config_path}: {e}")
        return _deep_copy_dict(DEFAULT_CONFIG)


def save_config(config: dict[str, Any]) -> None:
    """Save config to file.

    Args:
        config: Config dictionary to save
    """
    if tomli_w is None:
        raise RuntimeError(
            "TOML write support not available. Install tomli-w: pip install tomli-w"
        )

    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "wb") as f:
        tomli_w.dump(config, f)


def merge_env_overrides(config: dict[str, Any]) -> dict[str, Any]:
    """Merge environment variable overrides into config.

    Environment variables take precedence over config file values.

    Args:
        config: Base config dictionary

    Returns:
        Config with environment overrides applied
    """
    result = _deep_copy_dict(config)

    # Apply standard env var mappings
    for dot_path, env_var in ENV_VAR_MAP.items():
        value = os.environ.get(env_var)
        if value is not None:
            _set_nested(result, dot_path, _parse_env_value(value))

    # Apply provider-specific API key if provider is set
    provider = result.get("planner", {}).get("provider", "openai")
    api_key_env = PROVIDER_API_KEY_ENV_VARS.get(provider)
    if api_key_env:
        api_key = os.environ.get(api_key_env)
        if api_key:
            _set_nested(result, "planner.api_key", api_key)

    # Apply provider-specific defaults
    _apply_provider_defaults(result, provider)

    return result


def _apply_provider_defaults(config: dict[str, Any], provider: str) -> None:
    """Apply provider-specific defaults if not already set.

    Args:
        config: Config dictionary to modify in place
        provider: Provider identifier
    """
    # DeepSeek: set default base_url if not provided
    if provider == "deepseek":
        planner = config.get("planner", {})
        if "base_url" not in planner or not planner["base_url"]:
            _set_nested(config, "planner.base_url", "https://api.deepseek.com")


def mask_secrets(config: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of config with secrets masked.

    Args:
        config: Config dictionary

    Returns:
        Config with secrets replaced by "***"
    """
    result = _deep_copy_dict(config)

    # Keys to mask
    secret_keys = {"api_key", "token", "password", "secret"}

    def mask_dict(d: dict) -> None:
        for key, value in d.items():
            if isinstance(value, dict):
                mask_dict(value)
            elif key in secret_keys and value:
                d[key] = "***"

    mask_dict(result)
    return result


def set_config_value(config: dict[str, Any], dot_path: str, value: str) -> dict[str, Any]:
    """Set a config value using dot-path notation.

    Args:
        config: Config dictionary
        dot_path: Dot-separated path (e.g., "planner.model")
        value: String value to set

    Returns:
        Updated config dictionary
    """
    result = _deep_copy_dict(config)
    _set_nested(result, dot_path, _parse_env_value(value))
    return result


def get_config_value(config: dict[str, Any], dot_path: str) -> Any:
    """Get a config value using dot-path notation.

    Args:
        config: Config dictionary
        dot_path: Dot-separated path (e.g., "planner.model")

    Returns:
        Value at the path, or None if not found
    """
    parts = dot_path.split(".")
    current = config

    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]

    return current


# ─────────────────────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────────────────────


def _deep_copy_dict(d: dict) -> dict:
    """Deep copy a dictionary."""
    result = {}
    for key, value in d.items():
        if isinstance(value, dict):
            result[key] = _deep_copy_dict(value)
        else:
            result[key] = value
    return result


def _deep_merge(target: dict, source: dict) -> None:
    """Deep merge source into target (mutates target)."""
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            _deep_merge(target[key], value)
        else:
            target[key] = value


def _set_nested(d: dict, dot_path: str, value: Any) -> None:
    """Set a nested value using dot-path notation (mutates d)."""
    parts = dot_path.split(".")
    current = d

    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]

    current[parts[-1]] = value


def _parse_env_value(value: str) -> Any:
    """Parse environment variable value to appropriate type."""
    # Try to parse as number
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        pass

    # Try to parse as boolean
    if value.lower() in ("true", "yes", "1"):
        return True
    if value.lower() in ("false", "no", "0"):
        return False

    # Return as string
    return value
