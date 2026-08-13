"""ORM-independent contracts for one automatic workflow step."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol

from app.domain.invoice import InvoiceState, ValidatedInvoiceMetadata
from app.domain.types import (
    ResolutionResult,
    TaskDefinition,
    TaskResult,
    TaskType,
    TransitionDefinition,
)


class TraceKind(str, Enum):
    ATTEMPT_OUTCOME = "ATTEMPT_OUTCOME"
    RETRY_OBSERVATION = "RETRY_OBSERVATION"
    TRANSITION_SELECTED = "TRANSITION_SELECTED"
    INVOICE_STATE_CHANGED = "INVOICE_STATE_CHANGED"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    APPROVAL_DECIDED = "APPROVAL_DECIDED"
    RUN_RESUMED = "RUN_RESUMED"
    NOTIFICATION_CREATED = "NOTIFICATION_CREATED"
    SUCCESSFUL_TERMINAL = "SUCCESSFUL_TERMINAL"
    UNSUCCESSFUL_TERMINAL = "UNSUCCESSFUL_TERMINAL"


@dataclass(frozen=True)
class ExecutionContext:
    """Stable executor input; task display names are intentionally absent."""

    run_id: str
    invoice_id: str
    task_id: int
    task_type: TaskType
    attempt_ordinal: int


class TaskExecutor(Protocol):
    def execute(self, context: ExecutionContext) -> TaskResult:
        """Execute one automatic task attempt."""


@dataclass(frozen=True)
class InvoiceMetadataValidated:
    metadata: ValidatedInvoiceMetadata


@dataclass(frozen=True)
class InvoiceStateChanged:
    state: InvoiceState
    reason: str | None = None


@dataclass(frozen=True)
class ArchiveRecordCreated:
    document_identity: str


@dataclass(frozen=True)
class InternalNotificationCreated:
    message: str


StepEffect = (
    InvoiceMetadataValidated
    | InvoiceStateChanged
    | ArchiveRecordCreated
    | InternalNotificationCreated
)


class AutomaticStepEffectPolicy(Protocol):
    def effects_for(
        self,
        context: ExecutionContext,
        result: TaskResult,
        resolution: StepResolution | None = None,
    ) -> tuple[StepEffect, ...]:
        """Return explicit business effects derived from one task result."""


@dataclass(frozen=True)
class ReadyAutomaticStep:
    run_id: str
    invoice_id: str
    task: TaskDefinition
    transitions: tuple[TransitionDefinition, ...]
    completed_attempts: int
    state_version: int


@dataclass(frozen=True)
class RetryCurrentTask:
    task_id: int
    next_attempt_ordinal: int


StepResolution = RetryCurrentTask | ResolutionResult


@dataclass(frozen=True)
class TraceObservation:
    kind: TraceKind
    task_id: int
    attempt_ordinal: int
    detail: str | None = None
    transition_id: int | None = None


@dataclass(frozen=True)
class AutomaticStepCommit:
    run_id: str
    expected_state_version: int
    next_state_version: int
    task_id: int
    attempt_ordinal: int
    result: TaskResult
    started_at: datetime
    finished_at: datetime
    resolution: StepResolution
    effects: tuple[StepEffect, ...]
    trace: tuple[TraceObservation, ...]


@dataclass(frozen=True)
class AutomaticStepCompleted:
    """Returned only after the unit of work has committed the step."""

    run_id: str
    committed_state_version: int
    resolution: StepResolution


class AutomaticStepUnitOfWork(Protocol):
    def load_ready_step(self, run_id: str) -> ReadyAutomaticStep:
        """Load the authoritative cursor and immutable revision data."""

    def commit_automatic_step(self, command: AutomaticStepCommit) -> None:
        """Atomically persist attempt, cursor decision, and ordered trace."""
