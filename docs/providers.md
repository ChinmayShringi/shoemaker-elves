# Provider Adapters

This guide covers all supported planner providers and their setup.

## Table of Contents

- [Overview](#overview)
- [Provider Comparison](#provider-comparison)
- [OpenAI](#openai)
- [Anthropic (Claude)](#anthropic-claude)
- [Azure OpenAI](#azure-openai)
- [DeepSeek](#deepseek)
- [OpenAI-Compatible](#openai-compatible)
- [Custom Providers](#custom-providers)

## Overview

The orchestrator uses a **provider adapter** system to support multiple LLM providers for task planning (GPT mode). Each provider adapter implements a common interface for:

- Generating batches of tasks
- Assessing task completion
- Tracking costs
- Error handling and retries

The agent that executes tasks (currently Claude Code) is independent of the planner provider.

```
┌─────────────────┐
│  Planner (LLM)  │  ← Provider adapter (OpenAI, Claude, etc.)
│                 │     Generates and reviews tasks
└────────┬────────┘
         │
         │ Tasks
         ↓
┌─────────────────┐
│  Agent (Claude) │  ← Executes tasks (independent of planner)
│                 │
└─────────────────┘
```

## Provider Comparison

| Provider | Strengths | Cost | Notes |
|----------|-----------|------|-------|
| **OpenAI** | Strong reasoning, fast, reliable | $$ | Best for GPT-4, good default choice |
| **Anthropic** | Excellent coding, context handling | $$ | Great for complex projects |
| **Azure OpenAI** | Enterprise support, compliance | $$$ | Requires Azure subscription |
| **DeepSeek** | Low cost, good performance | $ | Open-source models |
| **OpenAI-Compatible** | Full control, privacy | Free/$ | Local models (Ollama, LM Studio) |

### Recommended Models

| Provider | Model | Use Case |
|----------|-------|----------|
| **OpenAI** | `gpt-4` | Production, complex projects |
| **OpenAI** | `gpt-4-turbo` | Faster, cost-effective |
| **OpenAI** | `gpt-3.5-turbo` | Testing, simple projects |
| **Anthropic** | `claude-sonnet-4-5-20250929` | Latest, best performance |
| **Anthropic** | `claude-3-opus-20240229` | Maximum capability |
| **Anthropic** | `claude-3-sonnet-20240229` | Balanced cost/performance |
| **Azure OpenAI** | `gpt-4` | Enterprise deployment |
| **DeepSeek** | `deepseek-chat` | Cost-effective alternative |
| **OpenAI-Compatible** | `llama3` (Ollama) | Local, private |

## OpenAI

### Quick Setup

```bash
# Set API key
export GPT_ORCH_OPENAI_API_KEY=sk-...

# Configure
gpt-orch config set planner.provider openai
gpt-orch config set planner.model gpt-4

# Or use init wizard
gpt-orch init
```

### Configuration

**Via config file**:
```toml
[planner]
provider = "openai"
model = "gpt-4"
# api_key = "sk-..."  # Optional: can use env var
```

**Via environment**:
```bash
export GPT_ORCH_PLANNER_PROVIDER=openai
export GPT_ORCH_PLANNER_MODEL=gpt-4
export GPT_ORCH_OPENAI_API_KEY=sk-...
```

**Via CLI**:
```bash
gpt-orch ~/project \
  --gpt \
  -d "Build a web app" \
  --planner-provider openai \
  --planner-model gpt-4
```

### Supported Models

- `gpt-4` - Most capable, best for complex reasoning
- `gpt-4-turbo` - Faster and cheaper than gpt-4
- `gpt-4o` - Optimized for speed and cost
- `gpt-3.5-turbo` - Fast and cheap, good for simple tasks
- Any other OpenAI model via API

### Cost Tracking

OpenAI costs are estimated from token counts:
- Input tokens: ~$0.03/1K (varies by model)
- Output tokens: ~$0.06/1K (varies by model)

Cost limit:
```bash
gpt-orch ~/project --gpt -d "..." --max-cost-usd 50.0
```

## Anthropic (Claude)

### Quick Setup

```bash
# Set API key
export GPT_ORCH_ANTHROPIC_API_KEY=sk-ant-...

# Configure
gpt-orch config set planner.provider anthropic
gpt-orch config set planner.model claude-sonnet-4-5-20250929

# Or use init wizard
gpt-orch init
```

### Configuration

**Via config file**:
```toml
[planner]
provider = "anthropic"
model = "claude-sonnet-4-5-20250929"
# api_key = "sk-ant-..."  # Optional: can use env var
```

**Via environment**:
```bash
export GPT_ORCH_PLANNER_PROVIDER=anthropic
export GPT_ORCH_PLANNER_MODEL=claude-sonnet-4-5-20250929
export GPT_ORCH_ANTHROPIC_API_KEY=sk-ant-...
```

**Via CLI**:
```bash
gpt-orch ~/project \
  --gpt \
  -d "Build a REST API" \
  --planner-provider anthropic \
  --planner-model claude-sonnet-4-5-20250929
```

### Supported Models

- `claude-sonnet-4-5-20250929` - Latest Sonnet 4.5 (recommended)
- `claude-3-opus-20240229` - Most capable Claude 3
- `claude-3-sonnet-20240229` - Balanced Claude 3
- `claude-3-haiku-20240307` - Fastest, most economical

### Features

- **Extended context**: 200K token context window
- **Code generation**: Excellent at writing and reviewing code
- **Structured output**: Reliable JSON formatting for task planning
- **Tool use**: Native support for structured responses

### Cost Tracking

Claude costs are estimated from token counts:
- Sonnet 4.5: ~$0.003/1K input, ~$0.015/1K output
- Opus: ~$0.015/1K input, ~$0.075/1K output
- Sonnet 3: ~$0.003/1K input, ~$0.015/1K output

## Azure OpenAI

### Quick Setup

```bash
# Set API key and endpoint
export GPT_ORCH_AZURE_OPENAI_API_KEY=...
export GPT_ORCH_AZURE_ENDPOINT=https://your-resource.openai.azure.com
export GPT_ORCH_AZURE_DEPLOYMENT=your-deployment-name

# Configure
gpt-orch init
```

### Configuration

**Via config file**:
```toml
[planner]
provider = "azure_openai"
model = "gpt-4"  # Your deployment's model

[azure]
endpoint = "https://your-resource.openai.azure.com"
deployment = "your-deployment-name"
api_version = "2024-02-01"
```

**Via environment**:
```bash
export GPT_ORCH_PLANNER_PROVIDER=azure_openai
export GPT_ORCH_AZURE_OPENAI_API_KEY=...
export GPT_ORCH_AZURE_ENDPOINT=https://your-resource.openai.azure.com
export GPT_ORCH_AZURE_DEPLOYMENT=your-deployment-name
export GPT_ORCH_AZURE_API_VERSION=2024-02-01
```

**Via CLI**:
```bash
gpt-orch ~/project \
  --gpt \
  -d "Build a web app" \
  --planner-provider azure_openai \
  --planner-model gpt-4 \
  --azure-endpoint https://your-resource.openai.azure.com \
  --azure-deployment your-deployment-name
```

### Required Settings

Azure OpenAI requires three additional settings:

1. **Endpoint**: Your Azure OpenAI resource URL
2. **Deployment**: The deployment name (not the model name)
3. **API Version**: Azure API version (default: `2024-02-01`)

### Finding Your Settings

In Azure Portal:
1. Navigate to your Azure OpenAI resource
2. Go to "Keys and Endpoint"
3. Copy the **Endpoint** URL
4. Copy one of the **Keys**
5. Go to "Model deployments" to find your **Deployment name**

### Supported Models

Any model deployed in your Azure OpenAI resource:
- `gpt-4`
- `gpt-4-turbo`
- `gpt-35-turbo`
- Custom deployments

**Note**: Use the deployment name, not the base model name.

## DeepSeek

### Quick Setup

```bash
# Set API key
export GPT_ORCH_DEEPSEEK_API_KEY=...

# Configure
gpt-orch config set planner.provider deepseek
gpt-orch config set planner.model deepseek-chat

# Or use init wizard
gpt-orch init
```

### Configuration

**Via config file**:
```toml
[planner]
provider = "deepseek"
model = "deepseek-chat"
# api_key = "..."  # Optional: can use env var
# base_url = "https://api.deepseek.com"  # Optional: uses default
```

**Via environment**:
```bash
export GPT_ORCH_PLANNER_PROVIDER=deepseek
export GPT_ORCH_PLANNER_MODEL=deepseek-chat
export GPT_ORCH_DEEPSEEK_API_KEY=...
```

**Via CLI**:
```bash
gpt-orch ~/project \
  --gpt \
  -d "Build a data pipeline" \
  --planner-provider deepseek \
  --planner-model deepseek-chat
```

### Supported Models

- `deepseek-chat` - General-purpose conversational model
- `deepseek-coder` - Specialized for coding tasks

### Features

- **Cost-effective**: Significantly cheaper than GPT-4/Claude
- **Open-source**: Transparent model architecture
- **Code-focused**: Strong coding performance (especially `deepseek-coder`)

### Custom Base URL

If using a self-hosted DeepSeek instance:
```toml
[planner]
provider = "deepseek"
base_url = "https://your-custom-endpoint.com"
```

## OpenAI-Compatible

Use this provider for local models or any API that implements the OpenAI chat completions format.

### Quick Setup

```bash
# For Ollama
gpt-orch config set planner.provider openai_compatible
gpt-orch config set planner.model llama3
gpt-orch config set planner.base_url http://localhost:11434/v1
```

### Configuration

**Via config file**:
```toml
[planner]
provider = "openai_compatible"
model = "llama3"  # Model name from your local API
base_url = "http://localhost:11434/v1"
# api_key = "not-needed"  # Some APIs don't require a key
```

**Via environment**:
```bash
export GPT_ORCH_PLANNER_PROVIDER=openai_compatible
export GPT_ORCH_PLANNER_MODEL=llama3
export GPT_ORCH_PLANNER_BASE_URL=http://localhost:11434/v1
```

**Via CLI**:
```bash
gpt-orch ~/project \
  --gpt \
  -d "Build a chatbot" \
  --planner-provider openai_compatible \
  --planner-model llama3 \
  --planner-base-url http://localhost:11434/v1
```

### Supported Platforms

#### Ollama

```bash
# Install Ollama: https://ollama.ai
ollama pull llama3

# Configure orchestrator
gpt-orch config set planner.provider openai_compatible
gpt-orch config set planner.model llama3
gpt-orch config set planner.base_url http://localhost:11434/v1
```

#### LM Studio

```bash
# Start LM Studio server on port 1234
# Load a model

# Configure orchestrator
gpt-orch config set planner.provider openai_compatible
gpt-orch config set planner.model local-model
gpt-orch config set planner.base_url http://localhost:1234/v1
```

#### vLLM

```bash
# Start vLLM server
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Llama-2-7b-hf \
  --port 8000

# Configure orchestrator
gpt-orch config set planner.provider openai_compatible
gpt-orch config set planner.model Llama-2-7b-hf
gpt-orch config set planner.base_url http://localhost:8000/v1
```

#### Text Generation WebUI (oobabooga)

```bash
# Enable OpenAI extension in webui

# Configure orchestrator
gpt-orch config set planner.provider openai_compatible
gpt-orch config set planner.model your-model-name
gpt-orch config set planner.base_url http://localhost:5000/v1
```

### Model Recommendations

For best results with task planning:

- **Llama 3 70B**: Excellent reasoning, good for production
- **Llama 3 8B**: Fast, good for testing
- **Mistral 7B**: Balanced performance
- **CodeLlama**: Specialized for coding tasks
- **Mixtral 8x7B**: Strong reasoning with MoE architecture

### Limitations

- Local models may not be as reliable at following structured output formats
- Smaller models (<7B parameters) may struggle with complex planning
- No built-in cost tracking (runs free locally)

### Tips

1. **Use larger models** (≥13B) for complex projects
2. **Test task generation** before running full orchestration
3. **Adjust batch sizes** - smaller batches work better with local models
4. **Monitor quality** - review generated tasks before execution

## Custom Providers

You can create custom planner providers via the plugin system.

See [Plugin Development Guide](plugin-planners.md) for details.

**Example use cases**:
- Proprietary LLM APIs
- Custom prompt engineering
- Specialized task planning logic
- Integration with company-specific tools

## Provider Selection Guide

### Choose **OpenAI** if:
- You want the best out-of-box experience
- You need reliable, fast task planning
- Cost is not the primary concern
- You're using GPT-4 or newer models

### Choose **Anthropic** if:
- You're doing complex coding projects
- You need excellent code review and generation
- You value extended context (200K tokens)
- You prefer Claude's output style

### Choose **Azure OpenAI** if:
- You're in an enterprise environment
- You need compliance and data residency
- You already have an Azure subscription
- You need enterprise support

### Choose **DeepSeek** if:
- You want to minimize costs
- You're comfortable with open-source models
- You're doing coding-focused work
- You value transparency

### Choose **OpenAI-Compatible** if:
- You want full data privacy (local execution)
- You want to avoid API costs
- You have GPU resources available
- You want to experiment with different models

## Troubleshooting

### Provider Not Found

**Error**: `Unknown provider: xyz`

**Solution**: Use one of: `openai`, `anthropic`, `azure_openai`, `deepseek`, `openai_compatible`

### API Key Issues

**Error**: `API key not found`

**Solution**: Set the appropriate environment variable:
```bash
export GPT_ORCH_OPENAI_API_KEY=sk-...
export GPT_ORCH_ANTHROPIC_API_KEY=sk-ant-...
export GPT_ORCH_AZURE_OPENAI_API_KEY=...
export GPT_ORCH_DEEPSEEK_API_KEY=...
```

### Azure Endpoint Errors

**Error**: `Azure endpoint/deployment not configured`

**Solution**: Set all three required values:
```bash
export GPT_ORCH_AZURE_ENDPOINT=https://...
export GPT_ORCH_AZURE_DEPLOYMENT=...
export GPT_ORCH_AZURE_API_VERSION=2024-02-01
```

### OpenAI-Compatible Connection Failed

**Error**: `Failed to connect to base_url`

**Solution**:
1. Verify the server is running
2. Check the port and URL
3. Test with curl:
   ```bash
   curl http://localhost:11434/v1/models
   ```

### Model Not Available

**Error**: `Model not found: xyz`

**Solution**:
- For OpenAI/Anthropic: Check model name spelling
- For Azure: Use deployment name, not model name
- For local: Ensure model is loaded (e.g., `ollama list`)

## See Also

- [Configuration Guide](config.md) - Detailed configuration
- [Troubleshooting](troubleshooting.md) - Common issues
- [Plugin Development](plugin-planners.md) - Custom providers
