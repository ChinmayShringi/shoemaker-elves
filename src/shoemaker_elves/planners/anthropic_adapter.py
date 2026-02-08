"""
Anthropic adapter for planner interface.
Supports Claude models via the Anthropic Messages API.
"""

import json
import time
from typing import Tuple

from anthropic import (
    APIError,
    AuthenticationError,
    Anthropic,
    RateLimitError,
)

from ..prompt_validator import PromptValidator, ValidationError
from ..templates import (
    ASSESSMENT_SYSTEM_PROMPT,
    TASK_PLANNING_SYSTEM_PROMPT,
    build_assessment_prompt,
    build_planning_prompt,
)
from .types import ReviewSpec, TaskSpec, UsageMetrics


class AnthropicAdapter:
    """
    Anthropic planner adapter.

    Supports Claude models via the Anthropic Messages API.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-5-20250929",
    ):
        """
        Initialize Anthropic adapter.

        Args:
            api_key: Anthropic API key
            model: Model name (e.g., "claude-sonnet-4-5-20250929", "claude-opus-4-5-20251101")
        """
        self.model = model
        self.client = Anthropic(api_key=api_key)

    def plan_batch(
        self,
        project_description: str,
        repo_summary: str,
        batch_size: int,
    ) -> list[TaskSpec]:
        """
        Generate a batch of tasks using Claude.

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
        batch_num = 1 if not repo_summary else 2  # Simplified for adapter
        max_batches = 10  # Default value

        # Parse previous results from repo_summary if available
        previous_results = None
        if repo_summary and "PREVIOUS BATCH RESULTS:" in repo_summary:
            previous_results = []  # Simplified - could parse if needed

        user_prompt = build_planning_prompt(
            description=project_description,
            batch_num=batch_num,
            max_batches=max_batches,
            batch_size=batch_size,
            previous_results=previous_results,
            cumulative_summary=repo_summary,
        )

        # Call Anthropic API with retry
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
            print(f"  Claude reasoning: {parsed['batch_reasoning']}")

        return tasks

    def review_batch(
        self,
        project_description: str,
        repo_summary: str,
        task_results: list[dict],
    ) -> ReviewSpec:
        """
        Assess batch results using Claude.

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

        # Call Anthropic API with retry
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
                batch_assessment="Could not parse Claude assessment",
                issues=[f"Claude assessment response was not valid JSON: {e}"],
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
    ) -> Tuple[str, UsageMetrics]:
        """
        Call Anthropic API with retry logic and usage tracking.

        Args:
            system_prompt: System message
            user_prompt: User message

        Returns:
            Tuple of (response text, usage metrics)

        Raises:
            RuntimeError: If all retries fail
        """
        max_retries = 3

        # Enhance system prompt to ensure JSON output
        json_instruction = (
            "\n\nYou must respond with valid JSON only. "
            "Do not include any text before or after the JSON object."
        )
        enhanced_system_prompt = system_prompt + json_instruction

        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    system=enhanced_system_prompt,
                    messages=[
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.2,
                )

                # Extract text from response
                if not response.content:
                    raise ValueError("Empty response from Anthropic API")

                # Get the text content from the first content block
                content_text = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        content_text += block.text

                # Extract usage metrics
                usage = UsageMetrics()
                if hasattr(response, "usage") and response.usage:
                    prompt_tok = getattr(response.usage, "input_tokens", 0)
                    completion_tok = getattr(response.usage, "output_tokens", 0)
                    try:
                        usage.prompt_tokens = int(prompt_tok) if prompt_tok else 0
                        usage.completion_tokens = int(completion_tok) if completion_tok else 0
                        usage.total_tokens = usage.prompt_tokens + usage.completion_tokens
                    except (TypeError, ValueError):
                        # Handle Mock objects gracefully
                        usage.prompt_tokens = 0
                        usage.completion_tokens = 0
                        usage.total_tokens = 0
                    usage.cost_usd = self._estimate_cost(usage, self.model)

                return content_text, usage

            except AuthenticationError:
                raise RuntimeError(
                    "Anthropic authentication failed. Check your API key."
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
            print(f"  Attempting JSON repair...")

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
                print(f"  JSON repair successful!")
                return parsed
            except json.JSONDecodeError as repair_error:
                print(f"  JSON repair failed: {repair_error}")
                raise ValueError(
                    f"Anthropic returned invalid JSON even after repair. "
                    f"Original error: {e}, Repair error: {repair_error}"
                )

    def _estimate_cost(self, usage: UsageMetrics, model: str) -> float:
        """
        Estimate cost in USD based on token usage and model.

        Args:
            usage: Usage metrics with token counts
            model: Model name

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

        # Pricing as of 2024 (per 1M tokens)
        # Anthropic pricing structure
        pricing = {
            "claude-opus": {"prompt": 15.0, "completion": 75.0},
            "claude-sonnet": {"prompt": 3.0, "completion": 15.0},
            "claude-haiku": {"prompt": 0.8, "completion": 4.0},
        }

        # Default pricing for unknown models
        default_pricing = {"prompt": 3.0, "completion": 15.0}

        # Find matching pricing
        model_pricing = default_pricing
        for known_model, prices in pricing.items():
            if known_model in model.lower():
                model_pricing = prices
                break

        prompt_cost = (prompt_tokens / 1_000_000) * model_pricing["prompt"]
        completion_cost = (completion_tokens / 1_000_000) * model_pricing["completion"]

        return prompt_cost + completion_cost
