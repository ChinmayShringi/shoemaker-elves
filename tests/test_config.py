"""
Unit tests for the configuration system.
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from shoemaker_elves.config import (
    load_config,
    save_config,
    merge_env_overrides,
    mask_secrets,
    set_config_value,
    get_config_value,
    DEFAULT_CONFIG,
)


@pytest.fixture
def temp_config_dir(monkeypatch):
    """Create a temporary config directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock the config directory
        monkeypatch.setattr(
            "shoemaker_elves.config.get_config_dir",
            lambda: Path(tmpdir)
        )
        yield Path(tmpdir)


def test_load_default_config():
    """Test loading default config when no file exists."""
    config = load_config()
    assert config["planner"]["provider"] == "openai"
    assert config["planner"]["model"] == "gpt-5.2"
    assert config["planner"]["max_cost_usd"] == 50.0
    assert config["agent"]["model"] == "sonnet"


def test_save_and_load_config(temp_config_dir):
    """Test saving and loading config."""
    config = DEFAULT_CONFIG.copy()
    config["planner"]["model"] = "gpt-4"
    config["planner"]["api_key"] = "test-key"

    save_config(config)

    # Verify file was created
    config_path = temp_config_dir / "config.toml"
    assert config_path.exists()

    # Load and verify
    loaded = load_config()
    assert loaded["planner"]["model"] == "gpt-4"
    assert loaded["planner"]["api_key"] == "test-key"


def test_merge_env_overrides(monkeypatch):
    """Test environment variable overrides."""
    config = DEFAULT_CONFIG.copy()

    # Set env vars
    monkeypatch.setenv("SHOEMAKER_ELVES_PLANNER_PROVIDER", "anthropic")
    monkeypatch.setenv("SHOEMAKER_ELVES_PLANNER_MODEL", "claude-3-opus")
    monkeypatch.setenv("SHOEMAKER_ELVES_MAX_COST_USD", "100.0")

    merged = merge_env_overrides(config)

    assert merged["planner"]["provider"] == "anthropic"
    assert merged["planner"]["model"] == "claude-3-opus"
    assert merged["planner"]["max_cost_usd"] == 100.0


def test_merge_env_overrides_provider_api_key(monkeypatch):
    """Test provider-specific API key env vars."""
    config = DEFAULT_CONFIG.copy()
    config["planner"]["provider"] = "anthropic"

    monkeypatch.setenv("SHOEMAKER_ELVES_ANTHROPIC_API_KEY", "anthropic-key")

    merged = merge_env_overrides(config)

    assert merged["planner"]["api_key"] == "anthropic-key"


def test_merge_env_overrides_deepseek_api_key(monkeypatch):
    """Test DeepSeek-specific API key env var."""
    config = DEFAULT_CONFIG.copy()
    config["planner"]["provider"] = "deepseek"

    monkeypatch.setenv("SHOEMAKER_ELVES_DEEPSEEK_API_KEY", "deepseek-key")

    merged = merge_env_overrides(config)

    assert merged["planner"]["api_key"] == "deepseek-key"


def test_deepseek_default_base_url(monkeypatch):
    """Test DeepSeek default base_url is applied."""
    config = DEFAULT_CONFIG.copy()
    config["planner"]["provider"] = "deepseek"

    merged = merge_env_overrides(config)

    assert merged["planner"]["base_url"] == "https://api.deepseek.com"


def test_deepseek_custom_base_url(monkeypatch):
    """Test DeepSeek custom base_url is not overridden."""
    config = DEFAULT_CONFIG.copy()
    config["planner"]["provider"] = "deepseek"
    config["planner"]["base_url"] = "https://custom.deepseek.endpoint/v1"

    merged = merge_env_overrides(config)

    assert merged["planner"]["base_url"] == "https://custom.deepseek.endpoint/v1"


def test_mask_secrets():
    """Test secret masking."""
    config = {
        "planner": {
            "provider": "openai",
            "model": "gpt-4",
            "api_key": "sk-1234567890",
        },
        "azure": {
            "api_key": "azure-key-123",
            "endpoint": "https://example.azure.com",
        },
    }

    masked = mask_secrets(config)

    assert masked["planner"]["api_key"] == "***"
    assert masked["azure"]["api_key"] == "***"
    assert masked["planner"]["model"] == "gpt-4"  # Non-secret unchanged
    assert masked["azure"]["endpoint"] == "https://example.azure.com"  # Non-secret unchanged


def test_set_config_value():
    """Test setting config values with dot notation."""
    config = DEFAULT_CONFIG.copy()

    config = set_config_value(config, "planner.model", "gpt-4")
    assert config["planner"]["model"] == "gpt-4"

    config = set_config_value(config, "planner.max_cost_usd", "75.5")
    assert config["planner"]["max_cost_usd"] == 75.5

    config = set_config_value(config, "azure.endpoint", "https://test.com")
    assert config["azure"]["endpoint"] == "https://test.com"


def test_get_config_value():
    """Test getting config values with dot notation."""
    config = {
        "planner": {
            "provider": "openai",
            "model": "gpt-4",
        },
        "azure": {
            "endpoint": "https://test.com",
        },
    }

    assert get_config_value(config, "planner.model") == "gpt-4"
    assert get_config_value(config, "planner.provider") == "openai"
    assert get_config_value(config, "azure.endpoint") == "https://test.com"
    assert get_config_value(config, "nonexistent.key") is None


def test_parse_env_value_types():
    """Test parsing environment variable values to appropriate types."""
    from shoemaker_elves.config import _parse_env_value

    assert _parse_env_value("42") == 42
    assert _parse_env_value("3.14") == 3.14
    assert _parse_env_value("true") is True
    assert _parse_env_value("false") is False
    assert _parse_env_value("yes") is True
    assert _parse_env_value("no") is False
    assert _parse_env_value("some-string") == "some-string"


def test_env_override_priority(temp_config_dir, monkeypatch):
    """Test that env vars override config file values."""
    # Save config with one value
    config = DEFAULT_CONFIG.copy()
    config["planner"]["model"] = "gpt-3.5-turbo"
    save_config(config)

    # Set env var with different value
    monkeypatch.setenv("SHOEMAKER_ELVES_PLANNER_MODEL", "gpt-4")

    # Load and merge
    loaded = load_config()
    merged = merge_env_overrides(loaded)

    # Env var should win
    assert merged["planner"]["model"] == "gpt-4"


def test_config_preserves_new_keys():
    """Test that loading config preserves new keys added to defaults."""
    # Simulate loading an old config file that's missing new keys
    old_config = {
        "planner": {
            "provider": "openai",
            "model": "gpt-3.5-turbo",
        }
    }

    # Deep merge with defaults
    from shoemaker_elves.config import _deep_merge, _deep_copy_dict

    result = _deep_copy_dict(DEFAULT_CONFIG)
    _deep_merge(result, old_config)

    # New keys from defaults should be preserved
    assert "max_cost_usd" in result["planner"]
    assert "agent" in result

    # Old values should override defaults
    assert result["planner"]["model"] == "gpt-3.5-turbo"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
