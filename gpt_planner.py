"""
GPT integration for the orchestrator.
Only used when --gpt mode is enabled.
Handles task planning (batch generation) and batch assessment.
"""

import json
import time
from pathlib import Path

from openai import APIError, AuthenticationError, OpenAI, RateLimitError

from templates import (
    ASSESSMENT_SYSTEM_PROMPT,
    TASK_PLANNING_SYSTEM_PROMPT,
    build_assessment_prompt,
    build_planning_prompt,
)


class GPTPlanner:
    def __init__(self, api_key: str, model: str = "gpt-5.2"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def plan_batch(
        self,
        description: str,
        batch_num: int,
        max_batches: int,
        batch_size: int,
        previous_results: list | None = None,
        cumulative_summary: str = "",
    ) -> list[dict]:
        """Ask GPT to generate the next batch of tasks.

        Returns a list of task dicts with 'title' and 'prompt' keys.
        Returns empty list if GPT says the project is complete.
        """
        user_prompt = build_planning_prompt(
            description=description,
            batch_num=batch_num,
            max_batches=max_batches,
            batch_size=batch_size,
            previous_results=previous_results,
            cumulative_summary=cumulative_summary,
        )

        response = self._call_gpt(
            system_prompt=TASK_PLANNING_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        try:
            parsed = json.loads(response)
            tasks = parsed.get("tasks", [])
            reasoning = parsed.get("batch_reasoning", "")
            if reasoning:
                print(f"  GPT reasoning: {reasoning}")
            return tasks
        except json.JSONDecodeError:
            print(f"  Warning: GPT returned non-JSON response, attempting to extract tasks")
            return []

    def assess_batch(
        self,
        description: str,
        batch_num: int,
        batch_results: list,
        previous_summary: str = "",
    ) -> dict:
        """Ask GPT to assess batch results and produce a cumulative summary.

        Returns a dict with 'cumulative_summary', 'project_complete', etc.
        """
        user_prompt = build_assessment_prompt(
            description=description,
            batch_num=batch_num,
            batch_results=batch_results,
            previous_summary=previous_summary,
        )

        response = self._call_gpt(
            system_prompt=ASSESSMENT_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        try:
            parsed = json.loads(response)
            return parsed
        except json.JSONDecodeError:
            # Return a basic assessment if JSON parsing fails
            return {
                "cumulative_summary": previous_summary + f"\n\nBatch {batch_num} completed (assessment parse error).",
                "batch_assessment": "Could not parse GPT assessment",
                "issues": ["GPT assessment response was not valid JSON"],
                "project_complete": False,
                "completion_percentage": 0,
                "recommendations": "Retry assessment",
            }

    def write_tasks_to_files(
        self, tasks: list[dict], orchestrator_dir: str, start_index: int = 0
    ) -> list[dict]:
        """Write GPT-generated tasks to markdown files in the tasks/ directory.

        Returns task entries suitable for the state file.
        """
        tasks_dir = Path(orchestrator_dir) / "tasks"
        tasks_dir.mkdir(exist_ok=True)

        task_entries = []
        for i, task in enumerate(tasks):
            file_num = start_index + i + 1
            filename = f"tasks/{file_num}.md"
            filepath = tasks_dir / f"{file_num}.md"

            # Write task prompt to markdown file
            content = f"# {task.get('title', f'Task {file_num}')}\n\n{task['prompt']}"
            filepath.write_text(content)

            task_entries.append(
                {
                    "title": task.get("title", f"Task {file_num}"),
                    "file": filename,
                }
            )

        return task_entries

    def _call_gpt(self, system_prompt: str, user_prompt: str) -> str:
        """Call GPT with retry logic."""
        max_retries = 3

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.2,
                )
                return response.choices[0].message.content

            except AuthenticationError:
                raise RuntimeError(
                    "OpenAI authentication failed. Check your OPENAI_API_KEY."
                )
            except RateLimitError:
                wait = 30 * (attempt + 1)
                print(f"  Rate limited, waiting {wait}s...")
                time.sleep(wait)
            except APIError as e:
                if attempt == max_retries - 1:
                    raise RuntimeError(f"OpenAI API error after {max_retries} retries: {e}")
                wait = 2 ** (attempt + 1)
                print(f"  API error, retrying in {wait}s: {e}")
                time.sleep(wait)

        raise RuntimeError("GPT call failed after all retries")
