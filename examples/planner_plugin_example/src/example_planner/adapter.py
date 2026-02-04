"""
Example planner adapter implementation.

This is a minimal mock implementation that demonstrates the PlannerAdapter protocol.
In a real plugin, you would call an actual LLM API here.
"""

import logging
from typing import Any

from gpt_agent_orchestrator.planners.types import ReviewSpec, TaskSpec

logger = logging.getLogger(__name__)


class ExampleAdapter:
    """
    Example planner adapter for demonstration purposes.

    This adapter implements the PlannerAdapter protocol but returns
    mock/hardcoded responses instead of calling a real API. Use this
    as a template for implementing real provider adapters.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "example-model-v1",
        base_url: str | None = None,
        **kwargs: Any,
    ):
        """
        Initialize the example adapter.

        Args:
            api_key: API key for the provider
            model: Model identifier
            base_url: Optional base URL for the API endpoint
            **kwargs: Additional provider-specific parameters
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url or "https://api.example.com"
        self.extra_params = kwargs

        logger.info(
            f"ExampleAdapter initialized with model={model}, base_url={self.base_url}"
        )

    def plan_batch(
        self,
        project_description: str,
        repo_summary: str,
        batch_size: int,
    ) -> list[TaskSpec]:
        """
        Generate a batch of tasks based on project state.

        In a real implementation, this would:
        1. Construct a prompt from the inputs
        2. Call the LLM API
        3. Parse the JSON response
        4. Return a list of TaskSpec objects

        Args:
            project_description: High-level project goals
            repo_summary: Cumulative summary of work completed
            batch_size: Maximum number of tasks to generate

        Returns:
            List of TaskSpec objects, or empty list if project is complete
        """
        logger.info(
            f"Planning batch (size={batch_size}) for project: {project_description[:50]}..."
        )

        # Mock implementation: return a simple task
        # In a real implementation, you would:
        # 1. Build a prompt with the project description and summary
        # 2. Call your LLM API
        # 3. Parse the response (expecting JSON with task list)
        # 4. Convert to TaskSpec objects

        # Example: return empty list to signal completion
        # (in real use, you'd check if the project is actually done)
        if "already complete" in repo_summary.lower():
            logger.info("Project appears complete, returning empty task list")
            return []

        # Example: return a mock task
        return [
            TaskSpec(
                title="Example Task",
                prompt="This is an example task from the example planner plugin.\n"
                "In a real implementation, this would come from an LLM.\n\n"
                "Task: Demonstrates the plugin system working correctly.",
            )
        ]

    def review_batch(
        self,
        project_description: str,
        repo_summary: str,
        task_results: list[dict],
    ) -> ReviewSpec:
        """
        Assess batch results and produce a cumulative summary.

        In a real implementation, this would:
        1. Construct a prompt with project description, previous summary, and results
        2. Call the LLM API
        3. Parse the JSON response
        4. Return a ReviewSpec with status and updated summary

        Args:
            project_description: High-level project goals
            repo_summary: Previous cumulative summary
            task_results: List of task result dictionaries from the batch

        Returns:
            ReviewSpec with assessment and updated summary
        """
        logger.info(f"Reviewing batch of {len(task_results)} tasks")

        # Mock implementation: return a simple review
        # In a real implementation, you would:
        # 1. Build a prompt with the project description, previous summary, and results
        # 2. Call your LLM API
        # 3. Parse the response (expecting JSON with status and summary)
        # 4. Convert to ReviewSpec object

        # Example: check task results and determine status
        all_successful = all(
            result.get("completed", False) for result in task_results
        )
        status = "success" if all_successful else "failure"

        # Example: create updated summary
        cumulative_summary = (
            f"{repo_summary}\n\n"
            f"Batch completed with {len(task_results)} task(s). "
            f"Status: {status}. "
            "(Example plugin review)"
        )

        batch_assessment = f"Reviewed {len(task_results)} task(s). All tasks {status}."

        logger.info(f"Review completed with status={status}")

        return ReviewSpec(
            cumulative_summary=cumulative_summary,
            batch_assessment=batch_assessment,
            project_complete=(status == "success"),
        )
