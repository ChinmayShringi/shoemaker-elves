"""
GPT integration for the orchestrator.
Only used when --gpt mode is enabled.
Handles task planning (batch generation) and batch assessment.

All providers now use the planner adapter system for provider-agnostic LLM support.
"""

from pathlib import Path

from .planners import create_planner


class GPTPlanner:
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        provider: str = "openai",
        base_url: str | None = None,
        azure_endpoint: str | None = None,
        azure_deployment: str | None = None,
        azure_api_version: str = "2024-02-01",
    ):
        """
        Initialize GPT Planner.

        Args:
            api_key: API key for the provider
            model: Model name (provider-specific)
            provider: Provider name (openai, anthropic, azure_openai, openai_compatible, deepseek)
            base_url: Base URL for OpenAI-compatible providers
            azure_endpoint: Azure OpenAI endpoint (for Azure provider)
            azure_deployment: Azure OpenAI deployment name (for Azure provider)
            azure_api_version: Azure OpenAI API version
        """
        self.model = model
        self.provider = provider

        # Build adapter configuration
        adapter_kwargs = {
            "provider": provider,
            "api_key": api_key,
        }

        # Add provider-specific parameters
        if provider == "azure_openai":
            if not azure_endpoint or not azure_deployment:
                raise ValueError("azure_endpoint and azure_deployment required for azure_openai provider")
            adapter_kwargs.update({
                "endpoint": azure_endpoint,
                "deployment": azure_deployment,
                "api_version": azure_api_version,
            })
        elif provider in ("openai", "openai_compatible"):
            adapter_kwargs["model"] = model
            if base_url:
                adapter_kwargs["base_url"] = base_url
        elif provider == "deepseek":
            # DeepSeek uses OpenAI-compatible API
            adapter_kwargs["provider"] = "openai_compatible"
            adapter_kwargs["model"] = model
            adapter_kwargs["base_url"] = "https://api.deepseek.com"
        elif provider == "anthropic":
            adapter_kwargs["model"] = model
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        # Create planner adapter
        try:
            self.adapter = create_planner(**adapter_kwargs)
        except Exception as e:
            raise RuntimeError(f"Failed to create planner adapter for {provider}: {e}")

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
        try:
            task_specs = self.adapter.plan_batch(
                project_description=description,
                repo_summary=cumulative_summary,
                batch_size=batch_size,
            )
            # Convert TaskSpec objects to dicts
            return [task.to_dict() for task in task_specs]
        except ValueError as e:
            print(f"  Error: {e}")
            return []
        except RuntimeError as e:
            print(f"  Error: {e}")
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
        try:
            review_spec = self.adapter.review_batch(
                project_description=description,
                repo_summary=previous_summary,
                task_results=batch_results,
            )
            # Convert ReviewSpec to dict
            return review_spec.to_dict()
        except ValueError as e:
            print(f"  Warning: {e}")
            # Return basic assessment on error
            return {
                "cumulative_summary": previous_summary + f"\n\nBatch {batch_num} completed (assessment error).",
                "batch_assessment": "Could not complete assessment",
                "issues": [str(e)],
                "project_complete": False,
                "completion_percentage": 0,
                "recommendations": "Retry assessment",
            }
        except RuntimeError as e:
            print(f"  Error: {e}")
            # Return basic assessment on error
            return {
                "cumulative_summary": previous_summary + f"\n\nBatch {batch_num} completed (assessment error).",
                "batch_assessment": "Could not complete assessment",
                "issues": [str(e)],
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
