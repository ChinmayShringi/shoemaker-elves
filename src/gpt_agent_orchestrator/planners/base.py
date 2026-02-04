"""
Base protocol for planner adapters.
Defines the interface that all planner implementations must follow.
"""

from typing import Protocol

from .types import ReviewSpec, TaskSpec


class PlannerAdapter(Protocol):
    """
    Protocol for planner adapters.

    All planner implementations must provide these methods to integrate
    with the orchestrator's GPT mode.
    """

    def plan_batch(
        self,
        project_description: str,
        repo_summary: str,
        batch_size: int,
    ) -> list[TaskSpec]:
        """
        Generate a batch of tasks based on project state.

        Args:
            project_description: High-level description of the project goals
            repo_summary: Cumulative summary of work done so far
            batch_size: Maximum number of tasks to generate

        Returns:
            List of TaskSpec objects. Empty list if project is complete.

        Raises:
            ValueError: If the LLM returns invalid or unparseable JSON
            RuntimeError: If the API call fails after retries
        """
        ...

    def review_batch(
        self,
        project_description: str,
        repo_summary: str,
        task_results: list[dict],
    ) -> ReviewSpec:
        """
        Assess batch results and produce cumulative summary.

        Args:
            project_description: High-level description of the project goals
            repo_summary: Previous cumulative summary
            task_results: List of task result dictionaries from the batch

        Returns:
            ReviewSpec object with assessment and updated summary

        Raises:
            ValueError: If the LLM returns invalid or unparseable JSON
            RuntimeError: If the API call fails after retries
        """
        ...
