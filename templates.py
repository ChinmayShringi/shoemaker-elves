"""
GPT prompt templates for task planning and batch assessment.
Used by gpt_planner.py when running in --gpt mode.
"""

TASK_PLANNING_SYSTEM_PROMPT = """You are a senior software architect acting as a task planner for an AI coding agent.

Your job is to break down a project into small, atomic, executable tasks that the AI agent can complete one at a time in fresh sessions. Each task must be self-contained with a clear, specific prompt.

RULES:
1. Each task prompt must be SPECIFIC and ACTIONABLE. Include exact file names, function signatures, and expected behavior.
2. Tasks within a batch are sequential -- task N+1 may depend on task N completing first.
3. Each task should be completable by an AI agent in a single session (not too trivial, not too large).
4. The agent reads a context file for project context but has no memory of prior sessions.
5. Include file paths relative to the project root.
6. If a previous batch had failures, include fix/retry tasks in the next batch.
7. Return an empty tasks array if the project is complete.

RESPONSE FORMAT (strict JSON):
{
  "tasks": [
    {
      "title": "Short descriptive title",
      "prompt": "Detailed prompt for the AI agent. Be extremely specific about what to create, modify, or verify. Include file paths, function names, expected behavior, and any constraints."
    }
  ],
  "batch_reasoning": "Why these tasks were chosen for this batch"
}

If the project appears complete, return:
{
  "tasks": [],
  "batch_reasoning": "Project is complete because..."
}"""


TASK_PLANNING_USER_TEMPLATE = """PROJECT DESCRIPTION:
{description}

BATCH NUMBER: {batch_num} of {max_batches}
TASKS PER BATCH: {batch_size}

{previous_context}

Generate the next batch of up to {batch_size} tasks. Be specific in every prompt -- include file names, function signatures, expected behavior. Tasks execute sequentially and each runs in a fresh AI agent session."""


ASSESSMENT_SYSTEM_PROMPT = """You are a senior software architect reviewing the results of an automated coding batch.

Your job is to:
1. Assess what was accomplished in this batch
2. Identify any failures or incomplete work
3. Write a CUMULATIVE SUMMARY of ALL project progress (not just this batch)
4. Determine if the project is complete

The cumulative summary you write will be placed in a context file and read by fresh AI agent sessions. It must contain enough context for the agent to understand:
- What has been built so far (file paths, key components)
- What the project structure looks like
- What works and what doesn't
- Key architectural decisions made

RESPONSE FORMAT (strict JSON):
{
  "cumulative_summary": "Detailed markdown summary of ALL project progress to date...",
  "batch_assessment": "Brief assessment of this specific batch",
  "issues": ["List of unresolved issues or failures"],
  "project_complete": false,
  "completion_percentage": 45,
  "recommendations": "What the next batch should focus on"
}"""


ASSESSMENT_USER_TEMPLATE = """PROJECT DESCRIPTION:
{description}

BATCH {batch_num} RESULTS:
{batch_results}

PREVIOUS CUMULATIVE SUMMARY:
{previous_summary}

Assess this batch and produce an updated cumulative summary encompassing ALL work done so far (not just this batch). The summary will be written to the context file for the next batch of tasks."""


def build_planning_prompt(
    description: str,
    batch_num: int,
    max_batches: int,
    batch_size: int,
    previous_results: list | None = None,
    cumulative_summary: str = "",
) -> str:
    """Build the user message for task planning."""
    if batch_num == 1 or not previous_results:
        previous_context = "This is the first batch. No prior work has been done. The project directory may be empty or contain existing code."
    else:
        lines = [f"CUMULATIVE PROGRESS SUMMARY:\n{cumulative_summary}\n"]
        lines.append("PREVIOUS BATCH RESULTS:")
        for task in previous_results:
            status = "SUCCESS" if task.get("success", True) else "FAILED"
            title = task.get("title", "Untitled")
            summary = task.get("result_summary", "No summary")
            if isinstance(summary, str) and len(summary) > 300:
                summary = summary[:300] + "..."
            lines.append(f"- [{status}] {title}: {summary}")
            files = task.get("files_modified", [])
            if files:
                lines.append(f"  Files: {', '.join(files)}")
        previous_context = "\n".join(lines)

    return TASK_PLANNING_USER_TEMPLATE.format(
        description=description,
        batch_num=batch_num,
        max_batches=max_batches,
        batch_size=batch_size,
        previous_context=previous_context,
    )


def build_assessment_prompt(
    description: str,
    batch_num: int,
    batch_results: list,
    previous_summary: str = "",
) -> str:
    """Build the user message for batch assessment."""
    result_lines = []
    for task in batch_results:
        status = "SUCCESS" if task.get("success", True) else "FAILED"
        title = task.get("title", "Untitled")
        summary = task.get("result_summary", "No summary")
        files = task.get("files_modified", [])

        result_lines.append(f"### Task: {title} [{status}]")
        result_lines.append(f"Summary: {summary}")
        if files:
            result_lines.append(f"Files modified: {', '.join(files)}")
        errors = task.get("errors", [])
        if errors:
            result_lines.append(f"Errors: {'; '.join(errors)}")
        result_lines.append("")

    return ASSESSMENT_USER_TEMPLATE.format(
        description=description,
        batch_num=batch_num,
        batch_results="\n".join(result_lines),
        previous_summary=previous_summary or "No previous work done.",
    )
