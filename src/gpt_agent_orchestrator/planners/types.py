"""
Data types for planner adapters.
"""

from dataclasses import dataclass, field


@dataclass
class UsageMetrics:
    """Token usage and cost metrics from an API call."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary format."""
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": self.cost_usd,
        }


@dataclass
class TaskSpec:
    """Specification for a single task to be executed."""

    title: str
    prompt: str
    id: str | None = None
    summary: str = ""
    steps: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    acceptance_checks: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary format."""
        return {
            "title": self.title,
            "prompt": self.prompt,
            "id": self.id,
            "summary": self.summary,
            "steps": self.steps,
            "files": self.files,
            "acceptance_checks": self.acceptance_checks,
            "risks": self.risks,
            "constraints": self.constraints,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TaskSpec":
        """Create TaskSpec from dictionary."""
        return cls(
            title=data.get("title", "Untitled Task"),
            prompt=data.get("prompt", ""),
            id=data.get("id"),
            summary=data.get("summary", ""),
            steps=data.get("steps", []),
            files=data.get("files", []),
            acceptance_checks=data.get("acceptance_checks", []),
            risks=data.get("risks", []),
            constraints=data.get("constraints", []),
        )


@dataclass
class PlanResult:
    """Result from plan_batch including tasks and usage metrics."""

    tasks: list[TaskSpec]
    usage: UsageMetrics

    def to_dict(self) -> dict:
        """Convert to dictionary format."""
        return {
            "tasks": [t.to_dict() for t in self.tasks],
            "usage": self.usage.to_dict(),
        }


@dataclass
class ReviewSpec:
    """Specification for batch assessment results."""

    cumulative_summary: str
    batch_assessment: str
    issues: list[str] = field(default_factory=list)
    project_complete: bool = False
    completion_percentage: int = 0
    recommendations: str = ""
    next_tasks: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary format."""
        return {
            "cumulative_summary": self.cumulative_summary,
            "batch_assessment": self.batch_assessment,
            "issues": self.issues,
            "project_complete": self.project_complete,
            "completion_percentage": self.completion_percentage,
            "recommendations": self.recommendations,
            "next_tasks": self.next_tasks,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ReviewSpec":
        """Create ReviewSpec from dictionary."""
        return cls(
            cumulative_summary=data.get("cumulative_summary", ""),
            batch_assessment=data.get("batch_assessment", ""),
            issues=data.get("issues", []),
            project_complete=data.get("project_complete", False),
            completion_percentage=data.get("completion_percentage", 0),
            recommendations=data.get("recommendations", ""),
            next_tasks=data.get("next_tasks", []),
        )


@dataclass
class ReviewResult:
    """Result from review_batch including assessment and usage metrics."""

    review: ReviewSpec
    usage: UsageMetrics

    def to_dict(self) -> dict:
        """Convert to dictionary format."""
        return {
            "review": self.review.to_dict(),
            "usage": self.usage.to_dict(),
        }
