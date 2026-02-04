# GPT Agent Orchestrator

A standalone CLI tool that uses GPT as an orchestrator to break down large projects into tasks, then runs each task through an AI coding agent automatically using a hook-driven chain.

## How It Works

1. You provide a big project description (or pre-written task files)
2. GPT breaks it into small, atomic tasks
3. The orchestrator runs each task through the AI agent one by one
4. After each task completes, a SessionEnd hook fires and automatically starts the next task
5. After a batch of tasks completes, GPT reviews the results and plans the next batch
6. This loop continues until the project is done or the batch limit is reached

```
  GPT (planner)          Orchestrator            AI Agent
       |                      |                      |
       |-- batch of tasks --> |                      |
       |                      |-- task 1 ----------->|
       |                      |                  [executes]
       |                      |   <-- hook fires ----|
       |                      |-- task 2 ----------->|
       |                      |                  [executes]
       |                      |   <-- hook fires ----|
       |                      |-- task N ----------->|
       |                      |                  [executes]
       |                      |                      |
       |<-- results --------- |                      |
       |-- next batch ------> |                      |
       |                      |       ...            |
```

## Two Modes

### Manual Mode (default)

Create numbered markdown files in the `tasks/` directory and the orchestrator runs them in order. No GPT needed.

```bash
python3 orchestrator.py /path/to/your/project
```

### GPT Mode

GPT generates batches of tasks, the agent executes them, and GPT reviews results before planning the next batch.

```bash
python3 orchestrator.py /path/to/your/project --gpt -d "Build a REST API with auth"
```

## Setup

### Prerequisites

- Python 3.10+
- `openai` Python package (only needed for GPT mode)
- AI agent CLI installed and authenticated

### Install

```bash
git clone git@github.com:ChinmayShringi/gpt-claude-orchestrator.git
cd gpt-claude-orchestrator
pip3 install openai  # only needed for --gpt mode
```

### Set your OpenAI API key (for GPT mode)

```bash
export OPENAI_API_KEY="sk-..."
```

## Usage

### Manual Mode -- Pre-written Tasks

Create your task files as numbered markdown files:

```bash
# tasks/1.md
# Initialize project

Create a new Express.js project with TypeScript support.
Set up the directory structure with src/, tests/, config/.
Create a basic src/app.ts with a health check endpoint.
```

```bash
# tasks/2.md
# Add user model

Create src/models/user.ts with email and password fields.
Use Mongoose for MongoDB integration.
```

```bash
# tasks/3.md
# Add auth endpoints

Create POST /register and POST /login endpoints in src/routes/auth.ts.
Use JWT for token generation.
```

Then run:

```bash
python3 orchestrator.py ~/projects/my-api
```

The orchestrator will:
1. Discover all `tasks/*.md` files sorted numerically
2. Install a SessionEnd hook in your project
3. Run task 1 through the agent
4. When task 1 finishes, the hook automatically starts task 2
5. Continue until all tasks are done
6. Print a summary and clean up

### GPT Mode -- Automated Task Generation

```bash
python3 orchestrator.py ~/projects/my-api \
  --gpt \
  -d "Build a REST API for a todo app with JWT auth, CRUD endpoints, and tests" \
  --max-batches 3 \
  --batch-size 4
```

You can also pass a file path as the description:

```bash
python3 orchestrator.py ~/projects/my-api --gpt -d ./project-spec.md
```

### Resume After Interruption

If you Ctrl+C or the process is interrupted, you can resume:

```bash
python3 orchestrator.py ~/projects/my-api --resume
```

## CLI Reference

```
python3 orchestrator.py <project_dir> [options]

Arguments:
  project_dir                Path to the target project directory

Options:
  --gpt                      Enable GPT orchestration mode
  -d, --description TEXT     Project description (required with --gpt)
  --gpt-model MODEL          GPT model (default: gpt-5.2)
  --max-batches N            Max GPT planning rounds (default: 5)
  --batch-size N             Tasks per batch (default: 5)
  --agent-model MODEL        AI agent model (default: sonnet)
  --max-cost-usd AMOUNT      Cost ceiling in USD (default: 50.0)
  --task-timeout SECS        Max seconds per task before stall detection (default: 600)
  --resume                   Resume from existing state
  --verbose                  Detailed logging
  --openai-api-key KEY       OpenAI API key (or use OPENAI_API_KEY env)
```

## How the Hook Chain Works

The orchestrator uses a SessionEnd hook to create a self-perpetuating task chain:

1. **orchestrator.py** installs a hook into `{project}/.claude/settings.local.json`
2. When the agent finishes a task, the SessionEnd hook fires
3. **hook_handler.py** is invoked -- it reads the session transcript, updates `state.json`, and spawns the next agent task as a detached process
4. The orchestrator polls `state.json` to track progress
5. When all tasks in a batch complete, the orchestrator takes over (GPT assessment, next batch planning, etc.)

## File Structure

```
gpt-claude-orchestrator/
  orchestrator.py          -- CLI entry point and main loop
  hook_handler.py          -- SessionEnd hook (the core engine)
  state.py                 -- Shared state with file locking
  transcript_parser.py     -- Parse JSONL transcripts
  gpt_planner.py           -- GPT API integration (--gpt mode)
  templates.py             -- GPT prompt templates
  tasks/                   -- Task files (manual or GPT-generated)
    1.md
    2.md
    ...
  state.json               -- Runtime state (generated)
```

## Safety Limits

| Safeguard       | Default | Flag               |
|-----------------|---------|--------------------|
| Max cost        | $50     | --max-cost-usd     |
| Task timeout    | 600s    | --task-timeout     |
| Max batches     | 5       | --max-batches      |
| Hook timeout    | 30s     | (in settings.json) |

## Context Between Tasks

Each task runs in a fresh agent session with no memory of prior work. To maintain context:

- The orchestrator writes a `CLAUDE.md` file in the project root before each task
- After each task completes, the hook appends a summary of what was done
- Between batches (GPT mode), GPT writes a comprehensive cumulative summary
- The original `CLAUDE.md` is backed up and restored after orchestration

## License

MIT
