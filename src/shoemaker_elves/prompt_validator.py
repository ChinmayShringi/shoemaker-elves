"""
Prompt validator utility for validating task planning and review outputs.
Ensures JSON responses meet quality standards with required fields and content.
"""


class ValidationError(Exception):
    """Raised when validation fails."""

    pass


class PromptValidator:
    """Validates structured outputs from task planning and review prompts."""

    @staticmethod
    def validate_task(task: dict, task_index: int = 0) -> list[str]:
        """
        Validate a single task dictionary.

        Args:
            task: Task dictionary to validate
            task_index: Index of task in batch (for error messages)

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        task_id = f"Task {task_index}"

        # Required fields
        if not isinstance(task, dict):
            errors.append(f"{task_id}: Must be a dictionary, got {type(task).__name__}")
            return errors  # Can't continue validation

        # Check required string fields
        required_string_fields = ["title", "prompt"]
        for field in required_string_fields:
            if field not in task:
                errors.append(f"{task_id}: missing required '{field}' field")
            elif not isinstance(task[field], str):
                errors.append(
                    f"{task_id}: Field '{field}' must be a string, got {type(task[field]).__name__}"
                )
            elif not task[field].strip():
                errors.append(f"{task_id}: Field '{field}' cannot be empty")

        # Check optional but recommended fields
        recommended_fields = {
            "summary": str,
            "steps": list,
            "files": list,
            "acceptance_checks": list,
            "risks": list,
            "constraints": list,
        }

        for field, expected_type in recommended_fields.items():
            if field in task:
                if not isinstance(task[field], expected_type):
                    errors.append(
                        f"{task_id}: Field '{field}' should be {expected_type.__name__}, "
                        f"got {type(task[field]).__name__}"
                    )
                elif expected_type == list and len(task[field]) == 0:
                    # Warning for empty lists (not an error, but worth noting)
                    pass
                elif expected_type == str and not task[field].strip():
                    errors.append(f"{task_id}: Field '{field}' should not be empty if provided")

        # Validate list contents are strings
        for list_field in ["steps", "files", "acceptance_checks", "risks", "constraints"]:
            if list_field in task and isinstance(task[list_field], list):
                for i, item in enumerate(task[list_field]):
                    if not isinstance(item, str):
                        errors.append(
                            f"{task_id}: {list_field}[{i}] must be a string, "
                            f"got {type(item).__name__}"
                        )

        # Quality checks
        if "title" in task and isinstance(task["title"], str) and len(task["title"]) > 100:
            errors.append(f"{task_id}: Title too long ({len(task['title'])} chars, max 100)")

        if "files" in task and isinstance(task["files"], list) and len(task["files"]) == 0:
            # This is a warning, not an error - some tasks may not touch files
            pass

        return errors

    @staticmethod
    def validate_planning_response(response: dict, batch_size: int) -> list[str]:
        """
        Validate the complete planning response.

        Args:
            response: Parsed JSON response from planner
            batch_size: Maximum allowed tasks

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check top-level structure
        if not isinstance(response, dict):
            errors.append(f"Response must be a JSON object, got {type(response).__name__}")
            return errors  # Can't continue

        if "tasks" not in response:
            errors.append("Response missing 'tasks' field")
            return errors  # Can't continue

        tasks = response["tasks"]
        if not isinstance(tasks, list):
            errors.append(f"'tasks' field must be a list, got {type(tasks).__name__}")
            return errors  # Can't continue

        # Validate batch size constraint
        if len(tasks) > batch_size:
            errors.append(
                f"Batch size exceeded: {len(tasks)} tasks generated, maximum is {batch_size}"
            )

        # Validate each task
        for i, task in enumerate(tasks):
            task_errors = PromptValidator.validate_task(task, i)
            errors.extend(task_errors)

        # Check for batch_reasoning (optional but recommended)
        if "batch_reasoning" not in response:
            # Not an error, but could add a warning
            pass
        elif not isinstance(response["batch_reasoning"], str):
            errors.append(
                f"'batch_reasoning' must be a string, "
                f"got {type(response['batch_reasoning']).__name__}"
            )

        return errors

    @staticmethod
    def validate_review_response(response: dict) -> list[str]:
        """
        Validate the complete review/assessment response.

        Args:
            response: Parsed JSON response from review

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check top-level structure
        if not isinstance(response, dict):
            errors.append(f"Response must be a JSON object, got {type(response).__name__}")
            return errors  # Can't continue

        # Required string fields
        required_string_fields = ["cumulative_summary", "batch_assessment"]
        missing_fields = []
        for field in required_string_fields:
            if field not in response:
                missing_fields.append(field)
                errors.append(f"Response missing required field '{field}'")
            elif not isinstance(response[field], str):
                errors.append(
                    f"Field '{field}' must be a string, got {type(response[field]).__name__}"
                )
            elif not response[field].strip():
                errors.append(f"Field '{field}' cannot be empty")

        # Check other required fields
        if "issues" not in response:
            missing_fields.append("issues")
            errors.append("Missing required field 'issues'")
        elif not isinstance(response["issues"], list):
            errors.append(f"Field 'issues' must be a list, got {type(response['issues']).__name__}")
        else:
            # Validate list contents
            for i, issue in enumerate(response["issues"]):
                if not isinstance(issue, str):
                    errors.append(f"issues[{i}] must be a string, got {type(issue).__name__}")

        # Required boolean fields
        if "project_complete" not in response:
            missing_fields.append("project_complete")
            errors.append("Missing required field 'project_complete'")
        elif not isinstance(response["project_complete"], bool):
            errors.append(
                f"Field 'project_complete' must be a boolean, "
                f"got {type(response['project_complete']).__name__}"
            )

        # Required integer fields
        if "completion_percentage" not in response:
            missing_fields.append("completion_percentage")
            errors.append("Missing required field 'completion_percentage'")
        elif not isinstance(response["completion_percentage"], (int, float)):
            errors.append(
                f"Field 'completion_percentage' must be a number, "
                f"got {type(response['completion_percentage']).__name__}"
            )
        elif not 0 <= response["completion_percentage"] <= 100:
            errors.append(
                f"Field 'completion_percentage' must be between 0 and 100, "
                f"got {response['completion_percentage']}"
            )

        # Optional fields
        if "recommendations" in response and not isinstance(response["recommendations"], str):
            errors.append(
                f"Field 'recommendations' must be a string, "
                f"got {type(response['recommendations']).__name__}"
            )

        if "next_tasks" in response:
            if not isinstance(response["next_tasks"], list):
                errors.append(
                    f"Field 'next_tasks' must be a list, "
                    f"got {type(response['next_tasks']).__name__}"
                )
            else:
                # Validate next_tasks structure
                for i, task in enumerate(response["next_tasks"]):
                    if not isinstance(task, dict):
                        errors.append(f"next_tasks[{i}] must be a dict, got {type(task).__name__}")
                        continue

                    required_task_fields = ["title", "summary", "priority", "reason"]
                    for field in required_task_fields:
                        if field not in task:
                            errors.append(f"next_tasks[{i}]: Missing field '{field}'")
                        elif not isinstance(task[field], str):
                            errors.append(
                                f"next_tasks[{i}]: Field '{field}' must be a string, "
                                f"got {type(task[field]).__name__}"
                            )

                    # Validate priority values
                    if "priority" in task and task["priority"] not in ["high", "medium", "low"]:
                        errors.append(
                            f"next_tasks[{i}]: priority must be 'high', 'medium', or 'low', "
                            f"got '{task['priority']}'"
                        )

        # Add summary error message if multiple fields are missing
        if len(missing_fields) > 1:
            errors.insert(0, f"Response missing required fields: {', '.join(missing_fields)}")

        return errors

    @staticmethod
    def validate_and_raise(response: dict, operation: str, **kwargs) -> None:
        """
        Validate response and raise ValidationError if invalid.

        Args:
            response: Parsed JSON response
            operation: Either "plan_batch" or "review_batch"
            **kwargs: Additional arguments (e.g., batch_size for planning)

        Raises:
            ValidationError: If validation fails
        """
        if operation == "plan_batch":
            batch_size = kwargs.get("batch_size", 10)
            errors = PromptValidator.validate_planning_response(response, batch_size)
        elif operation == "review_batch":
            errors = PromptValidator.validate_review_response(response)
        else:
            raise ValueError(f"Unknown operation: {operation}")

        if errors:
            error_msg = f"Validation failed for {operation}:\n"
            error_msg += "\n".join(f"  - {err}" for err in errors)
            raise ValidationError(error_msg)
