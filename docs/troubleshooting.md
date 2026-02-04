# Troubleshooting Guide

Common issues and solutions for the GPT Agent Orchestrator.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Configuration Issues](#configuration-issues)
- [Provider Issues](#provider-issues)
- [Task Execution Issues](#task-execution-issues)
- [Performance Issues](#performance-issues)
- [State and Resume Issues](#state-and-resume-issues)
- [Cost and Limits](#cost-and-limits)
- [Hook Issues](#hook-issues)

## Installation Issues

### pip install fails

**Error**: `Could not find a version that satisfies the requirement`

**Solution**:
```bash
# Ensure you're using Python 3.10+
python --version

# Upgrade pip
pip install --upgrade pip

# Try installing with verbose output
pip install -v gpt-agent-orchestrator
```

### Import errors after installation

**Error**: `ModuleNotFoundError: No module named 'gpt_agent_orchestrator'`

**Solution**:
```bash
# Ensure package is installed
pip list | grep gpt-agent

# If using virtual environment, activate it first
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Reinstall
pip install --force-reinstall gpt-agent-orchestrator
```

### `gpt-orch` command not found

**Solution**:
```bash
# Ensure pip's bin directory is in PATH
python -m gpt_agent_orchestrator --help

# Or use pipx (recommended)
pipx install gpt-agent-orchestrator

# Or add pip's bin to PATH
export PATH="$HOME/.local/bin:$PATH"  # Linux/macOS
```

### Claude CLI not found

**Error**: `AI agent CLI not found`

**Solution**:
```bash
# Install Claude CLI
npm install -g @anthropics/claude-cli

# Or follow official installation guide
# https://github.com/anthropics/claude-code

# Verify installation
claude --version
```

## Configuration Issues

### API key not found

**Error**: `API key not found in config or environment`

**Solution**:
```bash
# Option 1: Use environment variable (recommended)
export GPT_ORCH_OPENAI_API_KEY=sk-...

# Option 2: Use config file
gpt-orch init

# Option 3: Set via config command
gpt-orch config set planner.api_key sk-...

# Verify
gpt-orch config show --no-mask
```

### Config file not loaded

**Error**: Configuration seems ignored

**Solution**:
```bash
# Check config file location
gpt-orch config show

# Ensure config file exists
ls -la ~/.config/gpt-orch/config.toml  # Linux/macOS
dir %APPDATA%\gpt-orch\config.toml     # Windows

# Verify config syntax (TOML)
cat ~/.config/gpt-orch/config.toml

# Recreate config
gpt-orch init
```

### Wrong provider selected

**Error**: Using unexpected provider

**Solution**:
```bash
# Check effective configuration
gpt-orch config show

# Remember priority: CLI flags > env vars > config file
# Unset env vars if needed
unset GPT_ORCH_PLANNER_PROVIDER

# Or explicitly set via CLI
gpt-orch ~/project --gpt -d "..." --planner-provider openai
```

## Provider Issues

### OpenAI API errors

**Error**: `OpenAI API request failed`

**Solutions**:

1. **Invalid API key**:
   ```bash
   # Test your key
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $GPT_ORCH_OPENAI_API_KEY"

   # Regenerate key at https://platform.openai.com/api-keys
   ```

2. **Rate limit exceeded**:
   ```bash
   # Reduce batch size
   gpt-orch ~/project --gpt -d "..." --batch-size 3

   # Wait and retry
   gpt-orch ~/project --resume
   ```

3. **Insufficient quota**:
   - Check your OpenAI account billing
   - Add credits at https://platform.openai.com/account/billing

### Anthropic API errors

**Error**: `Anthropic API request failed`

**Solutions**:

1. **Invalid API key**:
   ```bash
   # Verify key format (should start with sk-ant-)
   echo $GPT_ORCH_ANTHROPIC_API_KEY

   # Get new key at https://console.anthropic.com/
   ```

2. **Model not available**:
   ```bash
   # Use exact model name
   gpt-orch config set planner.model claude-sonnet-4-5-20250929
   ```

### Azure OpenAI errors

**Error**: `Azure OpenAI configuration error`

**Solutions**:

1. **Missing configuration**:
   ```bash
   # All three required
   export GPT_ORCH_AZURE_ENDPOINT=https://your-resource.openai.azure.com
   export GPT_ORCH_AZURE_DEPLOYMENT=your-deployment-name
   export GPT_ORCH_AZURE_API_VERSION=2024-02-01
   ```

2. **Wrong deployment name**:
   - Use deployment name, not model name
   - Check in Azure Portal → Your Resource → Model deployments

3. **Regional issues**:
   - Ensure your deployment is in an available region
   - Check Azure OpenAI service status

### DeepSeek connection issues

**Error**: `Failed to connect to DeepSeek API`

**Solutions**:
```bash
# Verify API key
echo $GPT_ORCH_DEEPSEEK_API_KEY

# Test connection
curl https://api.deepseek.com/v1/models \
  -H "Authorization: Bearer $GPT_ORCH_DEEPSEEK_API_KEY"

# Try custom base URL if needed
gpt-orch config set planner.base_url https://api.deepseek.com
```

### Local model (OpenAI-compatible) issues

**Error**: `Failed to connect to base_url`

**Solutions**:

1. **Server not running**:
   ```bash
   # For Ollama
   ollama serve

   # Verify
   curl http://localhost:11434/v1/models
   ```

2. **Wrong port/URL**:
   ```bash
   # Check server logs for correct port
   # Update config
   gpt-orch config set planner.base_url http://localhost:11434/v1
   ```

3. **Model not loaded**:
   ```bash
   # For Ollama
   ollama list
   ollama pull llama3
   ```

## Task Execution Issues

### Tasks not starting

**Issue**: Orchestrator hangs, no tasks execute

**Solutions**:

1. **Check agent CLI**:
   ```bash
   # Verify Claude CLI works
   claude --version

   # Test manually
   cd ~/your-project
   claude -p "Write hello world"
   ```

2. **Check hook installation**:
   ```bash
   # Verify hook exists
   cat ~/your-project/.claude/settings.local.json

   # Should contain SessionEnd hook
   # Reinstall if needed
   rm ~/your-project/.claude/settings.local.json
   gpt-orch ~/your-project  # Reinstalls hook
   ```

3. **Check permissions**:
   ```bash
   # Ensure orchestrator can write to project
   ls -la ~/your-project/.claude/
   ```

### Tasks fail immediately

**Issue**: All tasks marked as failed

**Solutions**:

1. **Check task content**:
   ```bash
   # View generated tasks
   cat src/gpt_agent_orchestrator/tasks/1.md

   # Ensure tasks are well-formed
   ```

2. **Check agent logs**:
   ```bash
   # Agent logs in project .claude/ directory
   ls ~/your-project/.claude/logs/
   ```

3. **Run task manually**:
   ```bash
   cd ~/your-project
   claude -p "$(cat path/to/task.md)"
   ```

### Tasks get stuck

**Issue**: Task runs forever, never completes

**Solutions**:

1. **Stall detection will trigger**:
   ```bash
   # Default timeout: 600s (10 minutes)
   # Adjust if needed
   gpt-orch ~/project --task-timeout 1200  # 20 minutes
   ```

2. **Resume after timeout**:
   ```bash
   # Wait for timeout, then
   gpt-orch ~/project --resume
   ```

3. **Check agent process**:
   ```bash
   # Find stuck process
   ps aux | grep claude

   # Kill if needed
   kill <PID>
   ```

### Wrong files modified

**Issue**: Agent modifies unexpected files

**Solutions**:

1. **Improve task descriptions**:
   - Be more specific about file paths
   - Explicitly list files to modify
   - Add constraints ("DO NOT modify...")

2. **Use manual mode**:
   - Pre-write tasks with exact instructions
   - Review before execution

3. **Monitor with verbose mode**:
   ```bash
   gpt-orch ~/project --verbose
   ```

## Performance Issues

### Slow task generation

**Issue**: GPT takes too long to plan tasks

**Solutions**:

1. **Use faster model**:
   ```bash
   gpt-orch config set planner.model gpt-4-turbo
   ```

2. **Reduce batch size**:
   ```bash
   gpt-orch ~/project --gpt -d "..." --batch-size 3
   ```

3. **Simplify description**:
   - Provide more focused, specific requirements
   - Break large projects into multiple runs

### High costs

**Issue**: Exceeding budget quickly

**Solutions**:

1. **Set cost limits**:
   ```bash
   gpt-orch config set planner.max_cost_usd 25.0
   ```

2. **Use cheaper model**:
   ```bash
   # OpenAI
   gpt-orch config set planner.model gpt-3.5-turbo

   # Anthropic
   gpt-orch config set planner.model claude-3-haiku-20240307

   # DeepSeek
   gpt-orch config set planner.provider deepseek
   ```

3. **Reduce batches**:
   ```bash
   gpt-orch ~/project --gpt -d "..." --max-batches 3
   ```

4. **Use manual mode**:
   - Write tasks yourself (no LLM costs for planning)
   - Only pay for agent execution

### Memory issues

**Issue**: Orchestrator uses too much memory

**Solutions**:

1. **Reduce batch sizes**:
   ```bash
   --batch-size 3 --max-batches 10
   ```

2. **Clear old state files**:
   ```bash
   rm src/gpt_agent_orchestrator/state.json
   ```

3. **Use manual mode** for large projects

## State and Resume Issues

### Resume fails

**Error**: `No state file found`

**Solution**:
```bash
# Ensure state file exists
ls src/gpt_agent_orchestrator/state.json

# If missing, cannot resume - start fresh
gpt-orch ~/project --gpt -d "..."
```

### Stale state

**Issue**: Resume starts from wrong task

**Solution**:
```bash
# Manually inspect state
cat src/gpt_agent_orchestrator/state.json | jq .

# Delete stale state to restart
rm src/gpt_agent_orchestrator/state.json
```

### State corruption

**Error**: `Failed to parse state file`

**Solution**:
```bash
# Validate JSON
cat src/gpt_agent_orchestrator/state.json | jq .

# If corrupted, delete and restart
rm src/gpt_agent_orchestrator/state.json
gpt-orch ~/project --gpt -d "..."
```

### Lock file issues

**Error**: `Failed to acquire state lock`

**Solution**:
```bash
# Another orchestrator process may be running
ps aux | grep gpt-orch

# Kill other processes
kill <PID>

# Remove lock file
rm src/gpt_agent_orchestrator/state.json.lock

# Retry
gpt-orch ~/project --resume
```

## Cost and Limits

### Cost limit reached prematurely

**Issue**: Stops before project complete

**Solutions**:

1. **Increase limit**:
   ```bash
   gpt-orch config set planner.max_cost_usd 100.0
   ```

2. **Resume with new limit**:
   ```bash
   gpt-orch ~/project --resume --max-cost-usd 75.0
   ```

3. **Check cost tracking accuracy**:
   ```bash
   # View state
   cat src/gpt_agent_orchestrator/state.json | jq .total_cost_usd

   # Costs are estimates; actual may vary
   ```

### Inaccurate cost estimates

**Issue**: Reported costs don't match actual

**Explanation**:
- Costs are estimated from token counts in transcripts
- Actual costs may vary based on:
  - API pricing changes
  - Prompt caching
  - Batch processing discounts
- Estimates are typically within 10-20% of actual

**Solution**:
- Use as a guide, not exact billing
- Check provider's usage dashboard for actual costs

## Hook Issues

### Hook not firing

**Issue**: Tasks don't auto-advance

**Solutions**:

1. **Check hook installation**:
   ```bash
   cat ~/your-project/.claude/settings.local.json

   # Should have SessionEnd hook
   ```

2. **Reinstall hook**:
   ```bash
   rm ~/your-project/.claude/settings.local.json
   gpt-orch ~/project --resume
   ```

3. **Check agent permissions**:
   ```bash
   # Hook needs permission to execute
   # Check .claude/settings.local.json permissions array
   ```

### Hook timeout

**Error**: `Hook execution timed out`

**Solution**:
```bash
# Increase timeout in settings.local.json
# Edit manually:
{
  "hooks": {
    "SessionEnd": [{
      "hooks": [{
        "type": "command",
        "command": "path/to/hook_handler.py",
        "timeout": 60  # Increase from 30
      }]
    }]
  }
}
```

### Hook errors

**Issue**: Hook fails, tasks don't continue

**Solutions**:

1. **Check hook logs**:
   ```bash
   # Logs should appear in agent output
   # Or check .claude/logs/
   ```

2. **Test hook manually**:
   ```bash
   # Simulate hook execution
   python src/gpt_agent_orchestrator/hook_handler.py ~/your-project
   ```

3. **Verify Python path**:
   ```bash
   # Hook must find Python
   which python3

   # Ensure shebang is correct in hook_handler.py
   head -1 src/gpt_agent_orchestrator/hook_handler.py
   ```

## Getting Help

If you can't resolve your issue:

1. **Check existing issues**: https://github.com/ChinmayShringi/gpt-claude-orchestrator/issues
2. **Create a new issue** with:
   - Error messages
   - Configuration (`gpt-orch config show`)
   - Steps to reproduce
   - Environment (OS, Python version, etc.)
3. **Enable verbose logging**:
   ```bash
   gpt-orch ~/project --verbose
   ```

## See Also

- [Configuration Guide](config.md) - Detailed configuration
- [Provider Adapters](providers.md) - Provider-specific setup
- [CLI Reference](../README.md#cli-reference) - All commands and options
