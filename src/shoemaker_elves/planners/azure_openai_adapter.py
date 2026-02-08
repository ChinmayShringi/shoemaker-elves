"""
Azure OpenAI adapter for planner interface.
Supports Azure OpenAI Service endpoints.
"""

import json
import time

from openai import APIError, AuthenticationError, AzureOpenAI, RateLimitError

from ..prompt_validator import PromptValidator, ValidationError
from ..templates import (
    ASSESSMENT_SYSTEM_PROMPT,
    TASK_PLANNING_SYSTEM_PROMPT,
    build_assessment_prompt,
    build_planning_prompt,
)
from .types import ReviewSpec, TaskSpec, UsageMetrics


class AzureOpenAIAdapter:
    """
    Azure OpenAI planner adapter.

    Supports Azure OpenAI Service with deployment-based models.
    """

    def __init__(
        self,
        api_key: str,
        endpoint: str,
        deployment: str,
        api_version: str = "2024-02-01",
    ):
        """
        Initialize Azure OpenAI adapter.

        Args:
            api_key: Azure OpenAI API key
            endpoint: Azure OpenAI endpoint URL (e.g., "https://your-resource.openai.azure.com/")
            deployment: Deployment name (e.g., "gpt-4o")
            api_version: API version (e.g., "2024-02-01")
        """
        self.deployment = deployment
        self.endpoint = endpoint
        self.api_version = api_version

        # Initialize Azure OpenAI client
        self.client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version=api_version,
        )

    def plan_batch(
        self,
        project_description: str,
        repo_summary: str,
        batch_size: int,
    ) -> list[TaskSpec]:
        """
        Generate a batch of tasks using Azure OpenAI.

        Args:
            project_description: High-level project description
            repo_summary: Cumulative summary of work done so far
            batch_size: Maximum number of tasks to generate

        Returns:
            List of TaskSpec objects. Empty list if project is complete.

        Raises:
            ValueError: If LLM returns invalid JSON
            RuntimeError: If API call fails after retries
        """
        # Build the prompt using existing template system
        # For the first batch, repo_summary will be empty
        batch_num = 1 if not repo_summary else 2  # Simplified for adapter
        max_batches = 10  # Default value

        # Parse previous results from repo_summary if available
        previous_results = None
        if repo_summary and "PREVIOUS BATCH RESULTS:" in repo_summary:
            # Summary contains previous batch info
            previous_results = []  # Simplified - could parse if needed

        user_prompt = build_planning_prompt(
            description=project_description,
            batch_num=batch_num,
            max_batches=max_batches,
            batch_size=batch_size,
            previous_results=previous_results,
            cumulative_summary=repo_summary,
        )

        # Call Azure OpenAI API with retry
        response_text, usage = self._call_api_with_retry(
            system_prompt=TASK_PLANNING_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        # Parse and validate response (with JSON repair if needed)
        parsed = self._parse_json_with_repair(
            response_text=response_text,
            system_prompt=TASK_PLANNING_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            operation="plan_batch"
        )

        # Validate with PromptValidator
        try:
            PromptValidator.validate_and_raise(
                parsed,
                operation="plan_batch",
                batch_size=batch_size
            )
        except ValidationError as e:
            # Trigger repair mechanism if validation fails
            print(f"  Validation failed, attempting repair: {e}")
            raise ValueError(f"Response validation failed: {e}")

        # Extract tasks
        tasks_data = parsed["tasks"]

        # Convert to TaskSpec objects
        tasks = []
        for task_data in tasks_data:
            tasks.append(TaskSpec.from_dict(task_data))

        # Log reasoning if provided
        if "batch_reasoning" in parsed and parsed["batch_reasoning"]:
            print(f"  Azure OpenAI reasoning: {parsed['batch_reasoning']}")

        return tasks

    def review_batch(
        self,
        project_description: str,
        repo_summary: str,
        task_results: list[dict],
    ) -> ReviewSpec:
        """
        Assess batch results using Azure OpenAI.

        Args:
            project_description: High-level project description
            repo_summary: Previous cumulative summary
            task_results: List of task result dictionaries

        Returns:
            ReviewSpec object with assessment and updated summary

        Raises:
            ValueError: If LLM returns invalid JSON
            RuntimeError: If API call fails after retries
        """
        batch_num = 1  # Simplified for adapter
        user_prompt = build_assessment_prompt(
            description=project_description,
            batch_num=batch_num,
            batch_results=task_results,
            previous_summary=repo_summary,
        )

        # Call Azure OpenAI API with retry
        response_text, usage = self._call_api_with_retry(
            system_prompt=ASSESSMENT_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        # Parse and validate response (with JSON repair if needed)
        try:
            parsed = self._parse_json_with_repair(
                response_text=response_text,
                system_prompt=ASSESSMENT_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                operation="review_batch"
            )
        except (json.JSONDecodeError, ValueError) as e:
            # Return a basic assessment if parsing fails completely
            print(f"  Warning: Failed to parse review after repair attempt: {e}")
            return ReviewSpec(
                cumulative_summary=f"{repo_summary}\n\nBatch completed (assessment parse error).",
                batch_assessment="Could not parse Azure OpenAI assessment",
                issues=[f"Azure OpenAI assessment response was not valid JSON: {e}"],
                project_complete=False,
                completion_percentage=0,
                recommendations="Retry assessment with clearer instructions",
            )

        # Validate with PromptValidator
        try:
            PromptValidator.validate_and_raise(parsed, operation="review_batch")
        except ValidationError as e:
            # Trigger repair mechanism if validation fails
            print(f"  Validation failed, attempting repair: {e}")
            raise ValueError(f"Response validation failed: {e}")

        return ReviewSpec.from_dict(parsed)

    def _call_api_with_retry(
        self, system_prompt: str, user_prompt: str
    ) -> tuple[str, UsageMetrics]:
        """
        Call Azure OpenAI API with retry logic and usage tracking.

        Args:
            system_prompt: System message
            user_prompt: User message

        Returns:
            Tuple of (response text, usage metrics)

        Raises:
            RuntimeError: If all retries fail
        """
        max_retries = 3

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.deployment,  # In Azure, this is the deployment name
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.2,
                )

                # Extract usage metrics
                usage = UsageMetrics()
                if hasattr(response, "usage") and response.usage:
                    prompt_tok = response.usage.prompt_tokens
                    completion_tok = response.usage.completion_tokens
                    total_tok = response.usage.total_tokens
                    try:
                        usage.prompt_tokens = int(prompt_tok) if prompt_tok else 0
                        usage.completion_tokens = int(completion_tok) if completion_tok else 0
                        usage.total_tokens = int(total_tok) if total_tok else 0
                    except (TypeError, ValueError):
                        # Handle Mock objects gracefully
                        usage.prompt_tokens = 0
                        usage.completion_tokens = 0
                        usage.total_tokens = 0
                    # Approximate cost calculation (Azure pricing may differ)
                    usage.cost_usd = self._estimate_cost(usage, self.deployment)

                return response.choices[0].message.content, usage

            except AuthenticationError:
                raise RuntimeError(
                    "Azure OpenAI authentication failed. Check your API key and endpoint."
                )

            except RateLimitError:
                if attempt == max_retries - 1:
                    raise RuntimeError("Rate limit exceeded after all retries")
                wait = 30 * (attempt + 1)
                print(f"  Rate limited, waiting {wait}s...")
                time.sleep(wait)

            except APIError as e:
                if attempt == max_retries - 1:
                    raise RuntimeError(f"API error after {max_retries} retries: {e}")
                wait = 2 ** (attempt + 1)
                print(f"  API error, retrying in {wait}s: {e}")
                time.sleep(wait)

        raise RuntimeError("API call failed after all retries")

    def _parse_json_with_repair(
        self,
        response_text: str,
        system_prompt: str,
        user_prompt: str,
        operation: str,
    ) -> dict:
        """
        Parse JSON response with one repair attempt on failure.

        Args:
            response_text: The response text to parse
            system_prompt: Original system prompt (for repair)
            user_prompt: Original user prompt (for repair)
            operation: Operation name for logging

        Returns:
            Parsed JSON dict

        Raises:
            ValueError: If JSON is invalid even after repair attempt
        """
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"  Warning: JSON parse error in {operation}: {e}")
            print(f"  Response excerpt: {response_text[:200]}...")
            print("  Attempting JSON repair...")

            # Make one repair attempt with explicit JSON-only instruction
            repair_prompt = (
                "Your previous response was not valid JSON. "
                "Please output ONLY valid JSON with no other text, markdown, or formatting. "
                "Do not include any explanation before or after the JSON."
            )

            try:
                repaired_text, repair_usage = self._call_api_with_retry(
                    system_prompt=system_prompt,
                    user_prompt=f"{user_prompt}\n\n{repair_prompt}",
                )
                parsed = json.loads(repaired_text)
                print("  JSON repair successful!")
                return parsed
            except json.JSONDecodeError as repair_error:
                print(f"  JSON repair failed: {repair_error}")
                raise ValueError(
                    f"Azure OpenAI returned invalid JSON even after repair. "
                    f"Original error: {e}, Repair error: {repair_error}"
                )

    def _estimate_cost(self, usage: UsageMetrics, deployment: str) -> float:
        """
        Estimate cost in USD based on token usage and deployment.

        Args:
            usage: Usage metrics with token counts
            deployment: Deployment name (often indicates model type)

        Returns:
            Estimated cost in USD
        """
        # Handle missing or invalid token counts gracefully
        try:
            prompt_tokens = int(usage.prompt_tokens) if usage.prompt_tokens else 0
            completion_tokens = int(usage.completion_tokens) if usage.completion_tokens else 0
        except (TypeError, ValueError):
            # If tokens are not convertible (e.g., Mock objects), return 0
            return 0.0

        # Azure pricing (per 1M tokens) - similar to OpenAI but can vary by region
        # These are approximate and should be updated with actual pricing
        pricing = {
            "gpt-4": {"prompt": 30.0, "completion": 60.0},
            "gpt-4-turbo": {"prompt": 10.0, "completion": 30.0},
            "gpt-4o": {"prompt": 5.0, "completion": 15.0},
            "gpt-35-turbo": {"prompt": 0.5, "completion": 1.5},
        }

        # Default pricing for unknown deployments
        default_pricing = {"prompt": 10.0, "completion": 30.0}

        # Find matching pricing based on deployment name
        model_pricing = default_pricing
        deployment_lower = deployment.lower()
        for known_model, prices in pricing.items():
            if known_model in deployment_lower:
                model_pricing = prices
                break

        prompt_cost = (prompt_tokens / 1_000_000) * model_pricing["prompt"]
        completion_cost = (completion_tokens / 1_000_000) * model_pricing["completion"]

        return prompt_cost + completion_cost
