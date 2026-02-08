# Custom Planner Plugin Development

Guide to creating custom planner providers for the GPT Agent Orchestrator.

## Table of Contents

- [Overview](#overview)
- [Plugin System Architecture](#plugin-system-architecture)
- [Quick Start](#quick-start)
- [Plugin Interface](#plugin-interface)
- [Implementation Guide](#implementation-guide)
- [Registration](#registration)
- [Testing](#testing)
- [Distribution](#distribution)
- [Examples](#examples)

## Overview

The orchestrator's plugin system allows you to create custom planner providers without modifying the core codebase. This enables:

- **Custom LLM integrations**: Connect to proprietary or specialized models
- **Custom prompting**: Implement specialized task planning logic
- **Custom workflows**: Add domain-specific planning strategies
- **Enterprise integrations**: Connect to internal APIs or tools

## Plugin System Architecture

```
┌──────────────────────────────────────┐
│  Orchestrator (Core)                 │
├──────────────────────────────────────┤
│  Plugin Registry                     │
│  - Discovers plugins via entry points│
│  - Loads adapter classes             │
│  - Validates interface compliance    │
└──────────────┬───────────────────────┘
               │
               ├─ Built-in Adapters
               │  ├─ OpenAI
               │  ├─ Anthropic
               │  ├─ Azure OpenAI
               │  └─ DeepSeek
               │
               └─ Custom Plugins (via setup.py entry points)
                  ├─ Your Custom Provider
                  ├─ Another Plugin
                  └─ ...
```

## Quick Start

### 1. Create Plugin Package

```bash
mkdir my-planner-plugin
cd my-planner-plugin

# Create directory structure
mkdir -p src/my_planner
touch src/my_planner/__init__.py
touch src/my_planner/adapter.py
touch pyproject.toml
touch README.md
```

### 2. Implement Adapter

```python
# src/my_planner/adapter.py
from chainsmith.planners.base import PlannerAdapter
from chainsmith.planners.types import (
    PlannerResponse,
    AssessmentResponse,
    TaskItem,
)

class MyPlannerAdapter(PlannerAdapter):
    """Custom planner adapter for My LLM."""

    def __init__(self, api_key: str, model: str, **kwargs):
        self.api_key = api_key
        self.model = model
        # Initialize your client here
        self.client = MyLLMClient(api_key=api_key)

    def plan_batch(
        self,
        description: str,
        batch_num: int,
        max_batches: int,
        batch_size: int,
        previous_results: list = None,
        cumulative_summary: str = "",
    ) -> PlannerResponse:
        """Generate a batch of tasks."""
        # Build your prompt
        prompt = self._build_planning_prompt(
            description, batch_num, max_batches, batch_size,
            previous_results, cumulative_summary
        )

        # Call your LLM
        response = self.client.complete(
            model=self.model,
            prompt=prompt,
        )

        # Parse response into tasks
        tasks = self._parse_tasks(response.content)

        # Return structured response
        return PlannerResponse(
            tasks=tasks,
            thinking=response.thinking,
            cost_usd=self._estimate_cost(response),
        )

    def assess_batch(
        self,
        description: str,
        batch_num: int,
        batch_results: list,
        previous_summary: str = "",
    ) -> AssessmentResponse:
        """Assess batch completion and plan next steps."""
        # Build assessment prompt
        prompt = self._build_assessment_prompt(
            description, batch_num, batch_results, previous_summary
        )

        # Call your LLM
        response = self.client.complete(
            model=self.model,
            prompt=prompt,
        )

        # Parse assessment
        assessment = self._parse_assessment(response.content)

        # Return structured response
        return AssessmentResponse(
            cumulative_summary=assessment["summary"],
            completion_percentage=assessment["completion"],
            project_complete=assessment["is_complete"],
            issues=assessment.get("issues", []),
            cost_usd=self._estimate_cost(response),
        )

    def _build_planning_prompt(self, ...):
        # Implement your custom prompt logic
        pass

    def _parse_tasks(self, content):
        # Parse LLM response into list of TaskItem
        pass

    def _estimate_cost(self, response):
        # Calculate cost from token usage
        pass
```

### 3. Configure Package

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "my-planner-plugin"
version = "0.1.0"
description = "Custom planner adapter for GPT Agent Orchestrator"
requires-python = ">=3.10"
dependencies = [
    "gpt-agent-orchestrator>=0.1.0",
    # Your LLM client dependencies
    "my-llm-sdk>=1.0.0",
]

[project.entry-points."chainsmith.planners"]
my_provider = "my_planner.adapter:MyPlannerAdapter"
```

### 4. Install Plugin

```bash
# Install in development mode
pip install -e .

# Or build and install
pip install .
```

### 5. Use Plugin

```bash
# Configure to use your provider
chainsmith config set planner.provider my_provider
chainsmith config set planner.model my-model-name

# Set API key
export CHAINSMITH_MY_PROVIDER_API_KEY=...

# Run orchestration
chainsmith ~/project --gpt -d "Build something"
```

## Plugin Interface

### Required Methods

All planner adapters must implement `PlannerAdapter` interface:

```python
from abc import ABC, abstractmethod
from chainsmith.planners.types import (
    PlannerResponse,
    AssessmentResponse,
)

class PlannerAdapter(ABC):
    @abstractmethod
    def plan_batch(
        self,
        description: str,
        batch_num: int,
        max_batches: int,
        batch_size: int,
        previous_results: list = None,
        cumulative_summary: str = "",
    ) -> PlannerResponse:
        """Generate a batch of tasks based on project description."""
        pass

    @abstractmethod
    def assess_batch(
        self,
        description: str,
        batch_num: int,
        batch_results: list,
        previous_summary: str = "",
    ) -> AssessmentResponse:
        """Assess completed batch and determine next steps."""
        pass
```

### Response Types

```python
from dataclasses import dataclass

@dataclass
class TaskItem:
    title: str          # Short task title
    prompt: str         # Full task prompt for agent
    acceptance: str     # Acceptance criteria (optional)

@dataclass
class PlannerResponse:
    tasks: list[TaskItem]   # Generated tasks
    thinking: str           # LLM reasoning (optional)
    cost_usd: float         # Estimated cost

@dataclass
class AssessmentResponse:
    cumulative_summary: str      # Summary of all work done
    completion_percentage: int   # 0-100
    project_complete: bool       # True if done
    issues: list[str]            # Problems found (optional)
    cost_usd: float              # Estimated cost
```

## Implementation Guide

### Step 1: Set Up Project Structure

```
my-planner-plugin/
├── src/
│   └── my_planner/
│       ├── __init__.py
│       ├── adapter.py      # Main adapter class
│       ├── client.py       # LLM client wrapper (optional)
│       └── prompts.py      # Prompt templates (optional)
├── tests/
│   ├── __init__.py
│   └── test_adapter.py
├── pyproject.toml
├── README.md
└── LICENSE
```

### Step 2: Implement Adapter Class

```python
# src/my_planner/adapter.py
from chainsmith.planners.base import PlannerAdapter
from chainsmith.planners.types import (
    PlannerResponse,
    AssessmentResponse,
    TaskItem,
)

class MyPlannerAdapter(PlannerAdapter):
    """Custom planner adapter."""

    def __init__(self, api_key: str, model: str, **kwargs):
        """Initialize adapter.

        Args:
            api_key: API key for your LLM service
            model: Model name
            **kwargs: Additional provider-specific settings
        """
        self.api_key = api_key
        self.model = model
        self.base_url = kwargs.get("base_url")

        # Initialize your client
        from .client import MyLLMClient
        self.client = MyLLMClient(
            api_key=api_key,
            base_url=self.base_url,
        )

    def plan_batch(self, description, batch_num, max_batches,
                   batch_size, previous_results=None,
                   cumulative_summary="") -> PlannerResponse:
        """Generate tasks for a batch."""

        # 1. Build prompt
        from .prompts import build_planning_prompt
        prompt = build_planning_prompt(
            description=description,
            batch_num=batch_num,
            max_batches=max_batches,
            batch_size=batch_size,
            previous_results=previous_results or [],
            cumulative_summary=cumulative_summary,
        )

        # 2. Call LLM
        try:
            response = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
        except Exception as e:
            raise RuntimeError(f"LLM API call failed: {e}")

        # 3. Parse response
        content = response.choices[0].message.content
        tasks = self._parse_task_list(content)

        # 4. Calculate cost
        cost = self._calculate_cost(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )

        # 5. Return structured response
        return PlannerResponse(
            tasks=tasks,
            thinking=content,  # Or extract thinking section
            cost_usd=cost,
        )

    def assess_batch(self, description, batch_num, batch_results,
                     previous_summary="") -> AssessmentResponse:
        """Assess batch and determine next steps."""

        # Similar structure to plan_batch
        from .prompts import build_assessment_prompt
        prompt = build_assessment_prompt(
            description=description,
            batch_num=batch_num,
            batch_results=batch_results,
            previous_summary=previous_summary,
        )

        response = self.client.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

        content = response.choices[0].message.content
        assessment = self._parse_assessment(content)

        cost = self._calculate_cost(
            response.usage.input_tokens,
            response.usage.output_tokens,
        )

        return AssessmentResponse(
            cumulative_summary=assessment["summary"],
            completion_percentage=assessment["completion"],
            project_complete=assessment["complete"],
            issues=assessment.get("issues", []),
            cost_usd=cost,
        )

    def _parse_task_list(self, content: str) -> list[TaskItem]:
        """Parse LLM response into tasks."""
        import json

        # Example: Expect JSON array
        try:
            data = json.loads(content)
            tasks = []
            for item in data.get("tasks", []):
                tasks.append(TaskItem(
                    title=item["title"],
                    prompt=item["prompt"],
                    acceptance=item.get("acceptance", ""),
                ))
            return tasks
        except json.JSONDecodeError:
            # Fallback: parse markdown or other format
            pass

    def _parse_assessment(self, content: str) -> dict:
        """Parse assessment response."""
        import json

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Fallback parsing
            pass

    def _calculate_cost(self, input_tokens: int,
                       output_tokens: int) -> float:
        """Calculate cost based on token usage."""
        # Your provider's pricing
        INPUT_COST_PER_1K = 0.01  # Example
        OUTPUT_COST_PER_1K = 0.03

        cost = (
            (input_tokens / 1000) * INPUT_COST_PER_1K +
            (output_tokens / 1000) * OUTPUT_COST_PER_1K
        )
        return round(cost, 4)
```

### Step 3: Create Prompt Templates

```python
# src/my_planner/prompts.py

PLANNING_SYSTEM_PROMPT = """You are a software project planner..."""

def build_planning_prompt(description, batch_num, max_batches,
                         batch_size, previous_results,
                         cumulative_summary):
    """Build prompt for task planning."""

    prompt = f"""# Project Planning

## Project Description
{description}

## Batch Information
- Current batch: {batch_num}/{max_batches}
- Tasks per batch: {batch_size}

"""

    if cumulative_summary:
        prompt += f"""## Work Completed So Far
{cumulative_summary}

"""

    if previous_results:
        prompt += """## Previous Batch Results
"""
        for result in previous_results:
            status = "✓" if result["success"] else "✗"
            prompt += f"- {status} {result['title']}\n"
        prompt += "\n"

    prompt += """## Task
Generate the next batch of tasks. Return JSON:

{
  "tasks": [
    {
      "title": "Short task name",
      "prompt": "Detailed instructions for agent",
      "acceptance": "How to verify completion"
    }
  ]
}
"""

    return prompt

def build_assessment_prompt(description, batch_num, batch_results,
                           previous_summary):
    """Build prompt for batch assessment."""
    # Similar structure
    pass
```

### Step 4: Package Configuration

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "my-planner-plugin"
version = "0.1.0"
description = "Custom planner for GPT Agent Orchestrator"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "you@example.com"}
]
dependencies = [
    "gpt-agent-orchestrator>=0.1.0",
    "requests>=2.28.0",  # Or your LLM SDK
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
]

# CRITICAL: Entry point registration
[project.entry-points."chainsmith.planners"]
my_provider = "my_planner.adapter:MyPlannerAdapter"
```

**Entry point format**:
- Key (`my_provider`): Provider name used in config
- Value (`my_planner.adapter:MyPlannerAdapter`): Import path to adapter class

## Registration

The orchestrator discovers plugins via Python entry points.

### How It Works

1. Plugin declares entry point in `pyproject.toml`
2. On installation, entry point is registered
3. Orchestrator's registry scans for `chainsmith.planners` entry points
4. Adapters are loaded dynamically

### Entry Point Naming

```toml
[project.entry-points."chainsmith.planners"]
my_provider = "my_planner.adapter:MyPlannerAdapter"
company_llm = "company_planner.adapter:CompanyAdapter"
```

**Use in config**:
```bash
chainsmith config set planner.provider my_provider
# or
chainsmith config set planner.provider company_llm
```

## Testing

### Unit Tests

```python
# tests/test_adapter.py
import pytest
from my_planner.adapter import MyPlannerAdapter

def test_plan_batch():
    """Test task planning."""
    adapter = MyPlannerAdapter(
        api_key="test-key",
        model="test-model",
    )

    response = adapter.plan_batch(
        description="Build a web app",
        batch_num=1,
        max_batches=3,
        batch_size=5,
    )

    assert len(response.tasks) > 0
    assert response.tasks[0].title
    assert response.tasks[0].prompt
    assert response.cost_usd >= 0

def test_assess_batch():
    """Test batch assessment."""
    adapter = MyPlannerAdapter(
        api_key="test-key",
        model="test-model",
    )

    batch_results = [
        {"title": "Task 1", "success": True, "result_summary": "Done"}
    ]

    response = adapter.assess_batch(
        description="Build a web app",
        batch_num=1,
        batch_results=batch_results,
    )

    assert response.cumulative_summary
    assert 0 <= response.completion_percentage <= 100
    assert isinstance(response.project_complete, bool)
```

### Integration Test

```bash
# Test with orchestrator
pip install -e .

chainsmith config set planner.provider my_provider
export CHAINSMITH_MY_PROVIDER_API_KEY=...

# Run small test
chainsmith ~/test-project --gpt -d "Create a hello world file" --max-batches 1
```

## Distribution

### Publish to PyPI

```bash
# Build package
python -m build

# Upload to PyPI
python -m twine upload dist/*
```

### Installation by Users

```bash
# Install your plugin
pip install my-planner-plugin

# Will automatically register with orchestrator
chainsmith config set planner.provider my_provider
```

## Examples

See the included example plugin:
- `examples/planner_plugin_example/` - Complete working example
- Implements a simple echo adapter for testing

## Best Practices

1. **Error handling**: Wrap LLM API calls with try/except
2. **Cost tracking**: Accurately calculate costs from token usage
3. **Structured output**: Use JSON for reliable parsing
4. **Validation**: Validate LLM responses before returning
5. **Documentation**: Document your prompts and configuration
6. **Testing**: Include unit and integration tests
7. **Versioning**: Use semantic versioning

## See Also

- [Provider Adapters](providers.md) - Built-in provider details
- [Plugin System Documentation](planners/plugin-system.md) - Architecture details
- [Example Plugin](../examples/planner_plugin_example/) - Working reference implementation
