# GPT Agent Orchestrator

> An intelligent task orchestrator that breaks down large projects into atomic tasks and executes them through an AI coding agent automatically.

[![CI Status](https://github.com/ChinmayShringi/shoemaker-elves/actions/workflows/ci.yml/badge.svg)](https://github.com/ChinmayShringi/shoemaker-elves/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/shoemaker-elves.svg)](https://badge.fury.io/py/shoemaker-elves)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Table of Contents

- [How It Works](#how-it-works)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
- [CLI Reference](#cli-reference)
- [Examples](#examples)
- [Documentation](#documentation)
- [Development](#development)

## How It Works

The orchestrator uses a hook-driven chain to execute tasks sequentially through an AI agent. It supports two modes:

### Manual Mode
You create task files, and the orchestrator executes them in order.

### GPT Mode
An LLM (GPT, Claude, etc.) generates tasks, the agent executes them, and the LLM reviews results before planning the next batch.

```
┌─────────────┐
│   LLM       │  Generates batch of tasks
│  (Planner)  │
└──────┬──────┘
       │
       ├─ Task 1 ───> ┌──────────────┐
       │              │  AI Agent    │  Executes task
       │              └──────┬───────┘
       │                     │
       ├─ Task 2 ───>       │  SessionEnd hook fires
       │                     │  (auto-starts next task)
       │                     │
       ├─ Task N ───>       │
       │                     │
       └─ Reviews results <──┘
          Plans next batch
```

**Key Mechanism**: After each task completes, a `SessionEnd` hook automatically launches the next task as a detached process, creating a self-perpetuating chain.

## Features

- **Multi-provider support**: OpenAI, Anthropic (Claude), Azure OpenAI, DeepSeek, or any OpenAI-compatible API
- **Two execution modes**: Manual (pre-written tasks) or GPT (auto-generated tasks)
- **Batch planning**: LLM generates and reviews tasks in batches, adapting based on results
- **Resume capability**: Gracefully handles interruptions with stall detection
- **Cost controls**: Configurable spending limits and timeout protections
- **Plugin system**: Extend with custom planner providers
- **Rich logging**: Beautiful terminal UI with progress tracking
- **Context preservation**: Maintains project context across tasks via `CLAUDE.md`
- **Documentation tracking**: Automatic pre/post-work documentation workflow
- **Crash-safe state**: Cross-platform file locking prevents corruption

## Installation

### Via pip (PyPI)

```bash
# Core package (manual mode only)
pip install shoemaker-elves

# With OpenAI support (GPT mode)
pip install "shoemaker-elves[gpt]"

# With Anthropic support
pip install "shoemaker-elves[anthropic]"

# With all providers
pip install "shoemaker-elves[all]"
```

### Via pipx (Isolated Environment)

```bash
# Recommended for CLI tools
pipx install "shoemaker-elves[all]"
```

### From Source

```bash
git clone https://github.com/ChinmayShringi/shoemaker-elves.git
cd Chainsmith
pip install -e ".[all]"
```

### Prerequisites

- **Python 3.10+**
- **AI Agent CLI**: You need the `claude` CLI installed and authenticated
  ```bash
  # Install Claude CLI (example)
  npm install -g @anthropics/claude-cli

  # Or follow official instructions
  # https://github.com/anthropics/claude-code
  ```

## Quick Start

### 2-Minute Setup

1. **Install the orchestrator**:
   ```bash
   pip install "shoemaker-elves[all]"
   ```

2. **Configure your provider**:
   ```bash
   shoemaker-elves init
   ```
   This interactive wizard will guide you through selecting a provider, model, and API key setup.

3. **Run in Manual Mode** (using pre-written tasks):
   ```bash
   shoemaker-elves ~/my-project
   ```

4. **Or run in GPT Mode** (auto-generated tasks):
   ```bash
   shoemaker-elves ~/my-project --gpt -d "Build a REST API with user authentication"
   ```

### Manual Mode Example

Create task files in the orchestrator's `tasks/` directory:

```bash
# src/shoemaker-elves/tasks/1.md
# Initialize Express.js project

Create a new Express.js project with TypeScript support.
Set up directory structure: src/, tests/, config/.
Create a basic src/app.ts with a health check endpoint.
```

```bash
# src/shoemaker-elves/tasks/2.md
# Add user authentication

Implement JWT-based authentication with /register and /login endpoints.
Use bcrypt for password hashing.
Add middleware for protected routes.
```

Then run:
```bash
shoemaker-elves ~/my-project
```

### GPT Mode Example

Simply provide a project description:

```bash
shoemaker-elves ~/my-project \
  --gpt \
  -d "Build a todo app with REST API, SQLite database, and basic CRUD operations" \
  --max-batches 3 \
  --batch-size 5
```

Or use a spec file:

```bash
shoemaker-elves ~/my-project --gpt -d ./examples/project-spec.md
```

## Configuration

### Interactive Setup (Recommended)

```bash
shoemaker-elves init
```

This creates a configuration file at:
- **Linux/macOS**: `~/.config/shoemaker-elves/config.toml`
- **Windows**: `%APPDATA%\shoemaker-elves\config.toml`

### Manual Configuration

Create `~/.config/shoemaker-elves/config.toml`:

```toml
[planner]
provider = "openai"           # openai | anthropic | azure_openai | deepseek | openai_compatible
model = "gpt-4"
max_cost_usd = 50.0
# api_key = "sk-..."          # Optional: can use env vars instead

[agent]
model = "sonnet"              # Agent CLI model (e.g., sonnet, opus, haiku)

# Azure OpenAI specific (only needed if provider = "azure_openai")
[azure]
endpoint = "https://your-resource.openai.azure.com"
deployment = "your-deployment-name"
api_version = "2024-02-01"
```

### Environment Variables

Environment variables override config file values:

```bash
# Provider selection
export SHOEMAKER_ELVES_PLANNER_PROVIDER=openai

# Model selection
export SHOEMAKER_ELVES_PLANNER_MODEL=gpt-4

# API keys (provider-specific)
export SHOEMAKER_ELVES_OPENAI_API_KEY=sk-...
export SHOEMAKER_ELVES_ANTHROPIC_API_KEY=sk-ant-...
export SHOEMAKER_ELVES_AZURE_OPENAI_API_KEY=...
export SHOEMAKER_ELVES_DEEPSEEK_API_KEY=...

# OpenAI-compatible or DeepSeek custom base URL
export SHOEMAKER_ELVES_PLANNER_BASE_URL=https://api.example.com

# Azure OpenAI specific
export SHOEMAKER_ELVES_AZURE_ENDPOINT=https://...
export SHOEMAKER_ELVES_AZURE_DEPLOYMENT=...

# Cost and agent settings
export SHOEMAKER_ELVES_MAX_COST_USD=100.0
export SHOEMAKER_ELVES_AGENT_MODEL=sonnet
```

### Configuration Priority

Values are resolved in this order (highest to lowest):
1. **CLI flags** (`--planner-model gpt-4`)
2. **Environment variables** (`SHOEMAKER_ELVES_PLANNER_MODEL`)
3. **Config file** (`~/.config/shoemaker-elves/config.toml`)
4. **Default values**

### Managing Configuration

```bash
# View current config (secrets masked)
shoemaker-elves config show

# View unmasked config
shoemaker-elves config show --no-mask

# Update specific values
shoemaker-elves config set planner.model gpt-4
shoemaker-elves config set planner.max_cost_usd 100.0
```

## Usage

### Manual Mode

**Create task files** in `src/shoemaker-elves/tasks/`:
- `tasks/1.md` - First task
- `tasks/2.md` - Second task
- `tasks/3.md` - Third task
- ...

**Run orchestration**:
```bash
shoemaker-elves ~/my-project
```

**What happens**:
1. Orchestrator discovers all `tasks/*.md` files (sorted numerically)
2. Installs a `SessionEnd` hook in your project's `.claude/settings.local.json`
3. Launches task 1 through the AI agent
4. When task 1 completes, the hook automatically starts task 2
5. Process continues until all tasks are done
6. Prints summary and cleans up

### GPT Mode

**Basic usage**:
```bash
shoemaker-elves ~/my-project --gpt -d "Your project description here"
```

**With custom settings**:
```bash
shoemaker-elves ~/my-project \
  --gpt \
  -d "Build a web app with user auth and dashboard" \
  --planner-provider openai \
  --planner-model gpt-4 \
  --max-batches 5 \
  --batch-size 4 \
  --agent-model sonnet \
  --max-cost-usd 75.0
```

**Using a spec file**:
```bash
shoemaker-elves ~/my-project --gpt -d ./project-spec.md
```

**What happens**:
1. LLM plans the first batch of tasks based on your description
2. Tasks are written to files and executed sequentially via hooks
3. After batch completes, LLM reviews results and assesses progress
4. LLM generates next batch if needed (until project is complete or limits reached)
5. Summary and cleanup

### Provider-Specific Examples

#### OpenAI

```bash
shoemaker-elves ~/my-project \
  --gpt \
  -d "Build a CLI tool in Python" \
  --planner-provider openai \
  --planner-model gpt-4
```

#### Anthropic (Claude)

```bash
export SHOEMAKER_ELVES_ANTHROPIC_API_KEY=sk-ant-...

shoemaker-elves ~/my-project \
  --gpt \
  -d "Build a REST API" \
  --planner-provider anthropic \
  --planner-model claude-sonnet-4-5-20250929
```

#### Azure OpenAI

```bash
export SHOEMAKER_ELVES_AZURE_OPENAI_API_KEY=...

shoemaker-elves ~/my-project \
  --gpt \
  -d "Build a web app" \
  --planner-provider azure_openai \
  --planner-model gpt-4 \
  --azure-endpoint https://your-resource.openai.azure.com \
  --azure-deployment your-deployment-name
```

#### DeepSeek

```bash
export SHOEMAKER_ELVES_DEEPSEEK_API_KEY=...

shoemaker-elves ~/my-project \
  --gpt \
  -d "Build a data pipeline" \
  --planner-provider deepseek \
  --planner-model deepseek-chat
```

#### OpenAI-Compatible (Local Models)

```bash
# For example, using Ollama, LM Studio, or vLLM
shoemaker-elves ~/my-project \
  --gpt \
  -d "Build a chatbot" \
  --planner-provider openai_compatible \
  --planner-model llama3 \
  --planner-base-url http://localhost:11434/v1
```

### Resuming After Interruption

If you interrupt the orchestrator (Ctrl+C) or it crashes, you can resume:

```bash
shoemaker-elves ~/my-project --resume
```

**Stall detection**: Resume mode automatically detects and retries stalled tasks (tasks running longer than `--task-timeout` seconds).

## CLI Reference

### Commands

```bash
shoemaker-elves <project_dir> [options]    # Run orchestration (default command)
shoemaker-elves init                        # Interactive configuration setup
shoemaker-elves config show [--no-mask]    # Show current configuration
shoemaker-elves config set <key> <value>   # Set configuration value
```

### Orchestration Options

| Option | Description | Default |
|--------|-------------|---------|
| `project_dir` | Path to target project directory | **Required** |
| `--gpt` | Enable GPT orchestration mode | `false` (manual mode) |
| `-d, --description TEXT` | Project description (required with `--gpt`) | - |
| `--planner-provider PROVIDER` | Planner provider: `openai`, `anthropic`, `azure_openai`, `deepseek`, `openai_compatible` | `openai` |
| `--planner-model MODEL` | Planner model name | Provider-specific default |
| `--planner-base-url URL` | Base URL for `openai_compatible` or `deepseek` | - |
| `--azure-endpoint URL` | Azure OpenAI endpoint | - |
| `--azure-deployment NAME` | Azure OpenAI deployment name | - |
| `--azure-api-version VER` | Azure OpenAI API version | `2024-02-01` |
| `--max-batches N` | Maximum GPT planning rounds | `5` |
| `--batch-size N` | Tasks per batch | `5` |
| `--agent-model MODEL` | AI agent model (e.g., `sonnet`, `opus`) | `sonnet` |
| `--max-cost-usd AMOUNT` | Cost ceiling in USD | `50.0` |
| `--task-timeout SECS` | Max seconds per task before stall detection | `600` |
| `--resume` | Resume from existing state | `false` |
| `--verbose` | Detailed logging | `false` |

### Legacy Options

These flags are deprecated but still supported:

| Deprecated | Use Instead |
|------------|-------------|
| `--gpt-model` | `--planner-model` |
| `--provider` | `--planner-provider` |
| `--base-url` | `--planner-base-url` |
| `--openai-api-key` | Set via config or env var |

### Alternative Entry Points

```bash
# Via Python module
python -m shoemaker-elves <project_dir> [options]

# Legacy shim (backward compatibility)
python3 orchestrator.py <project_dir> [options]
```

## Examples

### Example 1: Manual Mode - Build a Web App

Create task files:

**tasks/1.md**:
```markdown
# Setup Next.js project

Initialize a new Next.js 14 project with TypeScript.
Use App Router.
Set up Tailwind CSS.
Create a basic layout and home page.
```

**tasks/2.md**:
```markdown
# Add authentication

Implement NextAuth.js with GitHub provider.
Create login/logout buttons.
Add protected route middleware.
Create a user profile page.
```

**tasks/3.md**:
```markdown
# Add database

Set up Prisma with SQLite.
Create User and Post models.
Add database migrations.
Implement basic CRUD operations.
```

Run:
```bash
shoemaker-elves ~/my-nextjs-app
```

### Example 2: GPT Mode - Build a CLI Tool

```bash
shoemaker-elves ~/my-cli-tool \
  --gpt \
  -d "Build a Python CLI tool that:
    - Fetches weather data from OpenWeather API
    - Supports multiple cities
    - Caches results for 1 hour
    - Uses typer for CLI framework
    - Includes tests with pytest
    - Has proper error handling" \
  --max-batches 4 \
  --batch-size 5
```

### Example 3: Using a Spec File

Create `project-spec.md`:
```markdown
# E-commerce API

## Overview
Build a RESTful API for an e-commerce platform.

## Requirements
- Node.js + Express + TypeScript
- PostgreSQL database
- JWT authentication
- Product catalog (CRUD)
- Shopping cart functionality
- Order management
- Payment integration (Stripe)
- Email notifications
- API documentation (Swagger)
- Unit and integration tests (Jest)

## Architecture
- Layered architecture (routes, controllers, services, repositories)
- Dependency injection
- Error handling middleware
- Request validation (Zod)
- Logging (Winston)

## Deliverables
- Fully functional API
- Database schema and migrations
- Test coverage > 80%
- README with API usage examples
- Docker setup
```

Run:
```bash
shoemaker-elves ~/ecommerce-api --gpt -d ./project-spec.md --max-batches 6
```

### Example 4: Resume After Interruption

```bash
# Start orchestration
shoemaker-elves ~/my-project --gpt -d "Build a dashboard"

# ... Ctrl+C to interrupt ...

# Resume later
shoemaker-elves ~/my-project --resume
```

## Documentation

### Core Documentation

- **[Configuration System](docs/config/configuration-system.md)** - Detailed config guide
- **[Provider Adapters](docs/providers.md)** - Provider comparison and setup
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions
- **[Plugin Development](docs/plugin-planners.md)** - Create custom planner providers

### Advanced Topics

- **[Planner Plugin System](docs/planners/plugin-system.md)** - Extend with custom providers
- **[State Management](docs/state/state-hardening.md)** - Crash safety and locking
- **[Rich Logging](docs/cli/rich-logging.md)** - Terminal UI features
- **[Task Templates](docs/templates/task-planning-templates.md)** - High-quality task generation
- **[Testing](docs/testing/test-suite-and-ci.md)** - Test suite and CI setup

### Packaging & Distribution

- **[PyInstaller Binaries](docs/packaging/pyinstaller-binaries.md)** - Standalone executables
- **[npm Wrapper](docs/packaging/npm-wrapper.md)** - npm distribution
- **[Release Process](docs/release/automated-release.md)** - Automated releases

## How the Hook Chain Works

The orchestrator uses a `SessionEnd` hook to create a self-perpetuating task chain:

1. **Hook Installation**: Orchestrator installs a hook in `.claude/settings.local.json`
2. **Task Execution**: AI agent executes a task
3. **Hook Triggers**: When task completes, `SessionEnd` hook fires
4. **Auto-Start**: Hook script (`hook_handler.py`) reads state, launches next task as detached process
5. **State Tracking**: Orchestrator polls `state.json` to monitor progress
6. **Batch Management**: After batch completes, LLM reviews and plans next batch (GPT mode)

### State File

State is tracked in `state.json` with cross-platform file locking for crash safety:

```json
{
  "status": "running",
  "mode": "gpt",
  "current_task_index": 2,
  "current_batch": 1,
  "tasks": [
    {
      "index": 0,
      "title": "Initialize project",
      "status": "completed",
      "started_at": "2026-02-04T10:00:00Z",
      "result_summary": "Created Express.js project with TypeScript",
      "files_modified": ["package.json", "tsconfig.json", "src/app.ts"],
      "cost_usd": 0.15
    }
  ],
  "batches": {
    "1": {
      "task_indices": [0, 1, 2, 3],
      "status": "running"
    }
  },
  "total_cost_usd": 0.45
}
```

### Context Management

Each task runs in a fresh agent session with no memory of prior work. Context is maintained via:

- **`CLAUDE.md`**: Written to project root before each task with:
  - Project description
  - Progress summary
  - Cumulative work done
  - Documentation requirements
- **Documentation tracking**: `prework.md` and `postwork.md` templates guide agents to document work
- **Cumulative summaries**: Between batches, LLM writes comprehensive summaries of all work done

## Safety Limits

| Safeguard | Default | Configuration |
|-----------|---------|---------------|
| Max cost | $50 USD | `--max-cost-usd` or config |
| Task timeout | 600s | `--task-timeout` |
| Max batches | 5 | `--max-batches` |
| Hook timeout | 30s | In `.claude/settings.local.json` |
| Batch size | 5 tasks | `--batch-size` |

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# With coverage
pytest --cov=src/shoemaker-elves --cov-report=html
```

### Building Documentation

Documentation is maintained in the `docs/` directory. To add new docs:

1. Create markdown file in appropriate subdirectory
2. Update this README to link to it
3. Ensure examples are tested and accurate

### Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### Release Process

See [Release Guide](docs/release/RELEASE_GUIDE.md) for detailed release instructions.

**Quick release**:
1. Update version in `pyproject.toml`
2. Run `python scripts/sync_version.py --sync`
3. Update `CHANGELOG.md`
4. Commit and tag: `git tag v1.2.3 && git push --tags`

## Project Structure

```
Chainsmith/
├── src/
│   └── shoemaker-elves/      # Main package
│       ├── __init__.py
│       ├── __main__.py              # Entry point for `python -m`
│       ├── cli.py                   # CLI implementation
│       ├── hook_handler.py          # SessionEnd hook (core engine)
│       ├── state.py                 # State management with locking
│       ├── config.py                # Configuration system
│       ├── gpt_planner.py           # GPT mode orchestration
│       ├── templates.py             # Prompt templates
│       ├── transcript_parser.py     # Parse agent transcripts
│       ├── logging.py               # Rich terminal UI
│       ├── prompt_validator.py      # Validate LLM outputs
│       ├── planners/                # Provider adapters
│       │   ├── base.py
│       │   ├── registry.py
│       │   ├── types.py
│       │   ├── openai_adapter.py
│       │   ├── anthropic_adapter.py
│       │   ├── azure_openai_adapter.py
│       │   └── deepseek_adapter.py (via openai_adapter)
│       └── tasks/                   # Task files (manual or GPT-generated)
├── docs/                            # Documentation
├── examples/                        # Example configurations
├── tests/                           # Test suite
├── packaging/                       # PyInstaller and npm builds
├── scripts/                         # Build and release scripts
├── pyproject.toml                   # Package metadata
└── orchestrator.py                  # Legacy shim
```

## Supported Providers

| Provider | Models | Notes |
|----------|--------|-------|
| **OpenAI** | gpt-4, gpt-4-turbo, gpt-3.5-turbo, etc. | Official OpenAI API |
| **Anthropic** | claude-3-opus, claude-3-sonnet, claude-3-haiku, claude-sonnet-4-5 | Official Anthropic API |
| **Azure OpenAI** | gpt-4, gpt-35-turbo (deployment-specific) | Requires endpoint + deployment |
| **DeepSeek** | deepseek-chat, deepseek-coder | Uses OpenAI-compatible adapter |
| **OpenAI-Compatible** | Any model | For local models (Ollama, LM Studio, vLLM, etc.) |

See [docs/providers.md](docs/providers.md) for detailed provider setup.

## FAQ

**Q: Can I use local models?**
A: Yes! Use `--planner-provider openai_compatible` and point `--planner-base-url` to your local API (e.g., Ollama, LM Studio).

**Q: How do I add a custom planner provider?**
A: See [Plugin Development Guide](docs/plugin-planners.md) for creating custom providers via the plugin system.

**Q: Can I run tasks in parallel?**
A: Not currently. Tasks run sequentially to maintain context and avoid conflicts.

**Q: What happens if a task fails?**
A: The orchestrator marks it as failed and continues. In GPT mode, the LLM receives failure info and can adapt.

**Q: How accurate is cost tracking?**
A: Cost is estimated from transcript token counts. Actual costs may vary based on caching, batching, and API pricing changes.

**Q: Can I customize the prompts sent to the LLM?**
A: Yes, modify `src/shoemaker-elves/templates.py` or create a custom planner plugin.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Built with [Anthropic's Claude](https://www.anthropic.com/claude)
- Inspired by agent-based development workflows
- Uses [Rich](https://github.com/Textualize/rich) for beautiful terminal output

---

**Built with ❤️ by the open source community**
