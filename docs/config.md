# Configuration Guide

This guide covers all configuration options for the GPT Agent Orchestrator.

## Table of Contents

- [Configuration Methods](#configuration-methods)
- [Configuration File](#configuration-file)
- [Environment Variables](#environment-variables)
- [CLI Flags](#cli-flags)
- [Priority Chain](#priority-chain)
- [Provider-Specific Configuration](#provider-specific-configuration)
- [Managing Configuration](#managing-configuration)
- [Advanced Configuration](#advanced-configuration)

## Configuration Methods

The orchestrator supports three configuration methods:

1. **Configuration file** (`~/.config/chainsmith/config.toml`)
2. **Environment variables** (`CHAINSMITH_*`)
3. **CLI flags** (`--planner-model`, etc.)

## Configuration File

### Location

- **Linux/macOS**: `~/.config/chainsmith/config.toml`
- **Windows**: `%APPDATA%\chainsmith\config.toml`

### Creating a Config File

**Interactive setup (recommended)**:
```bash
chainsmith init
```

**Manual creation**:
```toml
[planner]
provider = "openai"
model = "gpt-4"
max_cost_usd = 50.0
# api_key = "sk-..."  # Optional: can use env vars instead

[agent]
model = "sonnet"

# Azure OpenAI specific (only if provider = "azure_openai")
[azure]
endpoint = "https://your-resource.openai.azure.com"
deployment = "your-deployment-name"
api_version = "2024-02-01"
```

### Full Configuration Schema

```toml
[planner]
# Provider selection
provider = "openai"  # openai | anthropic | azure_openai | deepseek | openai_compatible

# Model name (provider-specific)
model = "gpt-4"

# Cost ceiling in USD
max_cost_usd = 50.0

# API key (optional - can use environment variables)
api_key = "sk-..."

# Base URL for openai_compatible provider
base_url = "http://localhost:11434/v1"

[agent]
# Agent model (passed to --model flag of agent CLI)
model = "sonnet"  # sonnet | opus | haiku | etc.

[azure]
# Azure OpenAI endpoint
endpoint = "https://your-resource.openai.azure.com"

# Azure deployment name
deployment = "your-deployment-name"

# Azure API version
api_version = "2024-02-01"
```

## Environment Variables

Environment variables override config file values. All environment variables use the prefix `CHAINSMITH_`.

### General Settings

```bash
# Provider selection
export CHAINSMITH_PLANNER_PROVIDER=openai

# Model selection
export CHAINSMITH_PLANNER_MODEL=gpt-4

# Cost limit
export CHAINSMITH_MAX_COST_USD=100.0

# Agent model
export CHAINSMITH_AGENT_MODEL=sonnet
```

### API Keys (Provider-Specific)

```bash
# OpenAI
export CHAINSMITH_OPENAI_API_KEY=sk-...

# Anthropic
export CHAINSMITH_ANTHROPIC_API_KEY=sk-ant-...

# Azure OpenAI
export CHAINSMITH_AZURE_OPENAI_API_KEY=...

# DeepSeek
export CHAINSMITH_DEEPSEEK_API_KEY=...
```

### OpenAI-Compatible Providers

```bash
# Base URL for custom OpenAI-compatible API
export CHAINSMITH_PLANNER_BASE_URL=http://localhost:11434/v1
```

### Azure OpenAI Specific

```bash
export CHAINSMITH_AZURE_ENDPOINT=https://your-resource.openai.azure.com
export CHAINSMITH_AZURE_DEPLOYMENT=your-deployment-name
export CHAINSMITH_AZURE_API_VERSION=2024-02-01
```

## CLI Flags

CLI flags have the highest priority and override all other configuration sources.

### Provider and Model

```bash
--planner-provider openai
--planner-model gpt-4
--planner-base-url http://localhost:11434/v1
```

### Azure OpenAI

```bash
--azure-endpoint https://your-resource.openai.azure.com
--azure-deployment your-deployment-name
--azure-api-version 2024-02-01
```

### Agent and Cost Settings

```bash
--agent-model sonnet
--max-cost-usd 100.0
```

### Full Example

```bash
chainsmith ~/my-project \
  --gpt \
  -d "Build a web app" \
  --planner-provider openai \
  --planner-model gpt-4 \
  --agent-model sonnet \
  --max-cost-usd 75.0 \
  --max-batches 5 \
  --batch-size 4
```

## Priority Chain

Configuration values are resolved in this order (highest to lowest priority):

1. **CLI flags**
2. **Environment variables**
3. **Config file**
4. **Default values**

### Example

If you have:
- Config file: `model = "gpt-3.5-turbo"`
- Environment: `CHAINSMITH_PLANNER_MODEL=gpt-4`
- CLI flag: `--planner-model claude-sonnet-4-5`

The orchestrator will use `claude-sonnet-4-5` (CLI flag wins).

## Provider-Specific Configuration

### OpenAI

**Minimal config**:
```toml
[planner]
provider = "openai"
model = "gpt-4"
```

**Environment variables**:
```bash
export CHAINSMITH_OPENAI_API_KEY=sk-...
```

**Supported models**: `gpt-4`, `gpt-4-turbo`, `gpt-4o`, `gpt-3.5-turbo`, etc.

### Anthropic (Claude)

**Minimal config**:
```toml
[planner]
provider = "anthropic"
model = "claude-sonnet-4-5-20250929"
```

**Environment variables**:
```bash
export CHAINSMITH_ANTHROPIC_API_KEY=sk-ant-...
```

**Supported models**:
- `claude-3-opus-20240229`
- `claude-3-sonnet-20240229`
- `claude-3-haiku-20240307`
- `claude-sonnet-4-5-20250929`

### Azure OpenAI

**Minimal config**:
```toml
[planner]
provider = "azure_openai"
model = "gpt-4"  # Your deployment model

[azure]
endpoint = "https://your-resource.openai.azure.com"
deployment = "your-deployment-name"
api_version = "2024-02-01"
```

**Environment variables**:
```bash
export CHAINSMITH_AZURE_OPENAI_API_KEY=...
export CHAINSMITH_AZURE_ENDPOINT=https://your-resource.openai.azure.com
export CHAINSMITH_AZURE_DEPLOYMENT=your-deployment-name
```

### DeepSeek

**Minimal config**:
```toml
[planner]
provider = "deepseek"
model = "deepseek-chat"
```

**Environment variables**:
```bash
export CHAINSMITH_DEEPSEEK_API_KEY=...
```

**Optional custom base URL**:
```toml
[planner]
base_url = "https://api.deepseek.com"  # Default, can be overridden
```

### OpenAI-Compatible (Local Models)

**For Ollama**:
```toml
[planner]
provider = "openai_compatible"
model = "llama3"
base_url = "http://localhost:11434/v1"
```

**For LM Studio**:
```toml
[planner]
provider = "openai_compatible"
model = "local-model"
base_url = "http://localhost:1234/v1"
```

**For vLLM**:
```toml
[planner]
provider = "openai_compatible"
model = "your-model-name"
base_url = "http://localhost:8000/v1"
```

## Managing Configuration

### View Current Configuration

```bash
# View with secrets masked
chainsmith config show

# View unmasked (shows API keys)
chainsmith config show --no-mask
```

### Update Configuration

```bash
# Set provider
chainsmith config set planner.provider anthropic

# Set model
chainsmith config set planner.model gpt-4

# Set cost limit
chainsmith config set planner.max_cost_usd 100.0

# Set agent model
chainsmith config set agent.model opus

# Set Azure endpoint
chainsmith config set azure.endpoint https://your-resource.openai.azure.com
```

### Multiple Configurations

You can maintain multiple configurations by using environment variables or CLI flags to override the base config:

**Development**:
```bash
# Use cheaper model for testing
export CHAINSMITH_PLANNER_MODEL=gpt-3.5-turbo
export CHAINSMITH_MAX_COST_USD=10.0
```

**Production**:
```bash
# Use better model for production
export CHAINSMITH_PLANNER_MODEL=gpt-4
export CHAINSMITH_MAX_COST_USD=100.0
```

## Advanced Configuration

### API Key Storage

**Best practice**: Use environment variables for API keys instead of storing them in the config file.

```bash
# Add to your shell profile (~/.bashrc, ~/.zshrc, etc.)
export CHAINSMITH_OPENAI_API_KEY=sk-...
export CHAINSMITH_ANTHROPIC_API_KEY=sk-ant-...
```

**Alternative**: Use a `.env` file with a tool like `direnv` or `dotenv`.

### Cost Tracking

Cost is estimated from token counts in transcripts. Configure limits:

```toml
[planner]
max_cost_usd = 50.0  # Stops when this limit is reached
```

Override per-run:
```bash
chainsmith ~/project --gpt -d "..." --max-cost-usd 25.0
```

### Task Timeout

Configure how long a task can run before being marked as stalled:

```bash
chainsmith ~/project --task-timeout 900  # 15 minutes
```

Default: 600 seconds (10 minutes)

### Batch Configuration

```bash
# More, smaller batches (iterative)
chainsmith ~/project --gpt -d "..." --max-batches 10 --batch-size 3

# Fewer, larger batches (aggressive)
chainsmith ~/project --gpt -d "..." --max-batches 3 --batch-size 8
```

### Logging

```bash
# Verbose logging (disables rich UI)
chainsmith ~/project --verbose

# Standard (uses rich UI if available)
chainsmith ~/project
```

## Troubleshooting Configuration

### Check Current Effective Configuration

```bash
chainsmith config show
```

This shows the final resolved configuration after merging all sources.

### Verify API Key Is Set

```bash
chainsmith config show --no-mask | grep api_key
```

Or check environment:
```bash
env | grep GPT_ORCH
```

### Test Provider Connection

The orchestrator validates the API key and provider before starting. If there's an issue, you'll see an error immediately.

### Common Issues

**Issue**: "API key not found"
**Solution**: Set the appropriate environment variable or add to config file.

**Issue**: "Provider not recognized"
**Solution**: Use one of: `openai`, `anthropic`, `azure_openai`, `deepseek`, `openai_compatible`

**Issue**: Azure endpoint errors
**Solution**: Ensure `endpoint`, `deployment`, and `api_version` are all set for `azure_openai` provider.

## See Also

- [Provider Adapters](providers.md) - Detailed provider setup
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
- [CLI Reference](../README.md#cli-reference) - All CLI options
