"""Immutable domain types for the defense-core workflow engine."""

from dataclasses import dataclass
from enum import Enum


class TransitionCondition(str, Enum):
    """Accepted transition condition labels (FR-007)."""

    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    ALWAYS = "ALWAYS"


class TaskOutcome(str, Enum):
    """Deterministic task-attempt outcomes."""

    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class ExecutionMode(str, Enum):
    ORCHESTRATION = "orchestration"
    CHOREOGRAPHY = "choreography"


class TaskType(str, Enum):
    """Closed task catalog for the invoice reference workflow (FR-049)."""

    DOCUMENT_VALIDATION = "DOCUMENT_VALIDATION"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"
    ARCHIVE_DOCUMENT = "ARCHIVE_DOCUMENT"
    CREATE_NOTIFICATION = "CREATE_NOTIFICATION"

    @property
    def is_automatic(self) -> bool:
        return self is not TaskType.HUMAN_APPROVAL


class FailureClass(str, Enum):
    """Failure meaning used by retry policy before transition resolution."""

    BUSINESS = "BUSINESS"
    RETRYABLE_TECHNICAL = "RETRYABLE_TECHNICAL"
    NON_RETRYABLE_TECHNICAL = "NON_RETRYABLE_TECHNICAL"


class TerminalDecision(str, Enum):
    """Terminal classification produced by the resolver (FR-011/012)."""

    SUCCESSFUL_TERMINAL = "SUCCESSFUL_TERMINAL"
    UNSUCCESSFUL_TERMINAL = "UNSUCCESSFUL_TERMINAL"


@dataclass(frozen=True)
class TaskDefinition:
    """Immutable task-definition data (CON-004)."""

    id: int
    name: str
    task_type: TaskType
    is_start: bool
    max_attempts: int | None


@dataclass(frozen=True)
class TaskResult:
    """Controlled result returned by an automatic task executor."""

    outcome: TaskOutcome
    failure_class: FailureClass | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        try:
            normalized_outcome = TaskOutcome(self.outcome)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Unsupported task outcome {self.outcome!r}") from exc
        object.__setattr__(self, "outcome", normalized_outcome)

        normalized_failure = self.failure_class
        if normalized_failure is not None:
            try:
                normalized_failure = FailureClass(normalized_failure)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Unsupported failure class {self.failure_class!r}"
                ) from exc
            object.__setattr__(self, "failure_class", normalized_failure)

        if (
            normalized_outcome is TaskOutcome.SUCCESS
            and normalized_failure is not None
        ):
            raise ValueError("A successful task result cannot have a failure class")
        if normalized_outcome is TaskOutcome.FAILURE and normalized_failure is None:
            raise ValueError("A failed task result requires a failure class")


@dataclass(frozen=True)
class TransitionDefinition:
    """Immutable directed edge between task definitions."""

    id: int
    from_task_id: int
    to_task_id: int
    condition: TransitionCondition


@dataclass(frozen=True)
class WorkflowDefinition:
    """Immutable workflow definition consumed by domain policy."""

    id: int
    tasks: tuple[TaskDefinition, ...]
    transitions: tuple[TransitionDefinition, ...]


@dataclass(frozen=True)
class TransitionSelected:
    transition: TransitionDefinition


@dataclass(frozen=True)
class TerminalReached:
    decision: TerminalDecision


ResolutionResult = TransitionSelected | TerminalReached
