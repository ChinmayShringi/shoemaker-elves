"""
GPT prompt templates for task planning and batch assessment.
Used by gpt_planner.py when running in --gpt mode.
"""

TASK_PLANNING_SYSTEM_PROMPT = """You are a senior software architect acting as a task planner for an AI coding agent.

Your job is to break down a project into small, atomic, executable tasks that the AI agent can complete one at a time in fresh sessions. Each task must be self-contained with a clear, specific prompt.

CRITICAL RULES:
1. Each task prompt must be SPECIFIC and ACTIONABLE. Include exact file names, function signatures, and expected behavior.
2. Tasks within a batch are sequential -- task N+1 may depend on task N completing first.
3. Each task should be completable by an AI agent in a single session (not too trivial, not too large).
4. The agent reads a context file for project context but has no memory of prior sessions.
5. Include file paths relative to the project root.
6. If a previous batch had failures, include fix/retry tasks in the next batch.
7. Return an empty tasks array if the project is complete.

TASK QUALITY STANDARDS:
- **Atomic**: Each task should do ONE thing well. Break complex work into steps.
- **Specific Files**: List exact files to create or modify.
- **Clear Steps**: Provide ordered implementation steps.
- **Acceptance Checks**: Define concrete verification criteria (commands to run, expected outputs).
- **Risk Awareness**: Identify potential issues (breaking changes, edge cases, dependencies).
- **Constraints**: Specify what NOT to do (avoid over-engineering, no unnecessary refactoring, etc).
- **Minimal Diffs**: Prefer small, incremental changes over large rewrites.

OUTPUT CONSTRAINTS (STRICTLY ENFORCED):
1. Output ONLY valid JSON. NO prose, explanations, or comments outside the JSON structure.
2. Do NOT exceed the specified batch_size limit.
3. Follow the exact schema below.

RESPONSE FORMAT (strict JSON):
{
  "tasks": [
    {
      "id": "task-1",
      "title": "Short descriptive title (50 chars max)",
      "summary": "One-sentence description of what this task accomplishes",
      "prompt": "Detailed prompt for the AI agent. Be extremely specific about what to create, modify, or verify. Include file paths, function names, expected behavior, and any constraints.",
      "steps": [
        "Step 1: Specific action to take",
        "Step 2: Next specific action",
        "..."
      ],
      "files": [
        "path/to/file1.py",
        "path/to/file2.py"
      ],
      "acceptance_checks": [
        "Run: pytest tests/test_feature.py",
        "Verify: All tests pass",
        "Check: No new linter errors"
      ],
      "risks": [
        "Breaking change to public API",
        "Potential performance impact on large datasets"
      ],
      "constraints": [
        "Do not refactor unrelated code",
        "Do not add unnecessary dependencies",
        "Keep backward compatibility"
      ]
    }
  ],
  "batch_reasoning": "Why these specific tasks were chosen for this batch"
}

If the project appears complete, return:
{
  "tasks": [],
  "batch_reasoning": "Project is complete because..."
}

EXAMPLE GOOD TASK:
{
  "id": "task-1",
  "title": "Add user authentication endpoint",
  "summary": "Implement POST /api/auth/login with JWT token generation",
  "prompt": "Create a login endpoint at POST /api/auth/login in src/api/auth.py that accepts email and password, validates credentials against the database, and returns a JWT token. Use bcrypt for password hashing and the existing JWT_SECRET from config.",
  "steps": [
    "Create src/api/auth.py with login() function",
    "Add password verification using bcrypt",
    "Generate JWT token with user_id claim",
    "Add error handling for invalid credentials",
    "Write unit tests in tests/test_auth.py"
  ],
  "files": [
    "src/api/auth.py",
    "tests/test_auth.py"
  ],
  "acceptance_checks": [
    "Run: pytest tests/test_auth.py -v",
    "Test: curl -X POST http://localhost:8000/api/auth/login with valid credentials returns 200",
    "Test: Invalid credentials return 401",
    "Verify: JWT token decodes correctly"
  ],
  "risks": [
    "JWT secret must be configured in environment",
    "Database must have users table with hashed passwords"
  ],
  "constraints": [
    "Do not implement registration in this task",
    "Do not add OAuth providers yet",
    "Use existing database connection"
  ]
}

REMEMBER: Output ONLY the JSON. No additional text before or after."""


TASK_PLANNING_USER_TEMPLATE = """PROJECT DESCRIPTION:
{description}

BATCH NUMBER: {batch_num} of {max_batches}
TASKS PER BATCH: {batch_size}

{previous_context}

Generate the next batch of up to {batch_size} tasks. Be specific in every prompt -- include file names, function signatures, expected behavior. Tasks execute sequentially and each runs in a fresh AI agent session."""


ASSESSMENT_SYSTEM_PROMPT = """You are a senior software architect reviewing the results of an automated coding batch.

Your job is to:
1. **Assess** what was accomplished in this batch
2. **Identify** any failures or incomplete work
3. **Detect** missing requirements or gaps in the implementation
4. **Write** a CUMULATIVE SUMMARY of ALL project progress (not just this batch)
5. **Determine** if the project is complete
6. **Generate** next-step tasks if needed (clear, structured, actionable)

The cumulative summary you write will be placed in a context file and read by fresh AI agent sessions. It must contain enough context for the agent to understand:
- What has been built so far (file paths, key components)
- What the project structure looks like
- What works and what doesn't
- Key architectural decisions made
- What requirements remain unimplemented

OUTPUT CONSTRAINTS (STRICTLY ENFORCED):
1. Output ONLY valid JSON. NO prose, explanations, or comments outside the JSON structure.
2. Follow the exact schema below.
3. If next tasks are needed, structure them with the same detail as planning tasks.

RESPONSE FORMAT (strict JSON):
{
  "cumulative_summary": "Detailed markdown summary of ALL project progress to date. Include:\n- Files created/modified with purpose\n- Key components and their interactions\n- What works and what doesn't\n- Architectural decisions and rationale\n- Remaining requirements",
  "batch_assessment": "Brief assessment of this specific batch. What succeeded, what failed, what was learned.",
  "issues": [
    "Unresolved issue 1 with context",
    "Unresolved issue 2 with context"
  ],
  "project_complete": false,
  "completion_percentage": 45,
  "recommendations": "Clear, specific guidance for what the next batch should focus on. Mention specific files, features, or fixes needed.",
  "next_tasks": [
    {
      "title": "Fix authentication bug",
      "summary": "Resolve JWT expiration handling issue",
      "priority": "high",
      "reason": "Blocking user login flow"
    }
  ]
}

NEXT_TASKS GUIDELINES:
- Only include if there are clear, specific tasks to do
- Each task should have: title, summary, priority (high/medium/low), reason
- Order by priority (high priority first)
- Be specific about what needs to be done
- Reference specific files or components
- If project is complete, next_tasks should be an empty array

EXAMPLE COMPLETE ASSESSMENT:
{
  "cumulative_summary": "# Project Status\\n\\n## Completed\\n- Authentication system (src/api/auth.py)\\n  - POST /api/auth/login endpoint\\n  - JWT token generation\\n  - Password hashing with bcrypt\\n- Database schema (migrations/001_users.sql)\\n- Tests (tests/test_auth.py) - 12 passing\\n\\n## Architecture\\n- Flask API server on port 8000\\n- PostgreSQL database\\n- JWT for stateless auth\\n\\n## Remaining\\n- Password reset flow\\n- Rate limiting on login\\n- OAuth providers",
  "batch_assessment": "Successfully implemented login endpoint. All tests pass. JWT integration works correctly. No issues encountered.",
  "issues": [],
  "project_complete": false,
  "completion_percentage": 60,
  "recommendations": "Next batch should focus on password reset flow and rate limiting, as these are security-critical features.",
  "next_tasks": [
    {
      "title": "Implement password reset flow",
      "summary": "Add forgot-password endpoint and email-based reset tokens",
      "priority": "high",
      "reason": "Critical for user account recovery"
    },
    {
      "title": "Add rate limiting to login",
      "summary": "Implement rate limiting middleware to prevent brute force attacks",
      "priority": "high",
      "reason": "Security requirement for production"
    }
  ]
}

REMEMBER: Output ONLY the JSON. No additional text before or after."""


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
