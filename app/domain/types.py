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


class TerminalDecision(str, Enum):
    """Terminal classification produced by the resolver (FR-011/012)."""

    SUCCESSFUL_TERMINAL = "SUCCESSFUL_TERMINAL"
    UNSUCCESSFUL_TERMINAL = "UNSUCCESSFUL_TERMINAL"


@dataclass(frozen=True)
class TaskDefinition:
    """Immutable task-definition data (CON-004)."""

    id: int
    name: str
    is_start: bool
    max_attempts: int


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
