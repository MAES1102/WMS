"""Persistent human-approval lifecycle application service."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from app.application.errors import StateVersionConflict, StepStateError
from app.application.ports import TraceKind
from app.domain.approval import (
    ApprovalChoice,
    ApprovalDecisionInput,
    ValidatedApprovalDecision,
    validate_approval_decision,
)
from app.domain.purchase_request import PurchaseRequestState
from app.domain.resolver import resolve_transition
from app.domain.types import (
    ResolutionResult,
    TaskDefinition,
    TaskOutcome,
    TaskType,
    TerminalDecision,
    TerminalReached,
    TransitionDefinition,
    TransitionSelected,
)


class ApprovalDecisionConflict(RuntimeError):
    pass


class ApprovalNotFound(LookupError):
    pass


@dataclass(frozen=True)
class ReadyHumanApproval:
    run_id: str
    purchase_request_id: str
    task: TaskDefinition
    transitions: tuple[TransitionDefinition, ...]
    state_version: int


@dataclass(frozen=True)
class WaitingHumanApproval:
    run_id: str
    purchase_request_id: str
    task_id: int
    work_item_id: str
    state_version: int


HumanApprovalState = ReadyHumanApproval | WaitingHumanApproval


@dataclass(frozen=True)
class PendingApprovalDecision:
    run_id: str
    purchase_request_id: str
    task: TaskDefinition
    transitions: tuple[TransitionDefinition, ...]
    work_item_id: str
    state_version: int


@dataclass(frozen=True)
class ExistingApprovalDecision:
    run_id: str
    work_item_id: str
    decision: ValidatedApprovalDecision
    outcome: TaskOutcome
    state_version: int


ApprovalDecisionState = PendingApprovalDecision | ExistingApprovalDecision


@dataclass(frozen=True)
class ApprovalTraceObservation:
    kind: TraceKind
    task_id: int
    detail: str | None = None
    transition_id: int | None = None


@dataclass(frozen=True)
class EnterApprovalWaitCommand:
    run_id: str
    purchase_request_id: str
    task_id: int
    work_item_id: str
    expected_state_version: int
    next_state_version: int
    created_at: datetime
    trace: tuple[ApprovalTraceObservation, ...]


@dataclass(frozen=True)
class CommitApprovalDecisionCommand:
    run_id: str
    purchase_request_id: str
    task_id: int
    work_item_id: str
    decision_id: str
    decision: ValidatedApprovalDecision
    outcome: TaskOutcome
    purchase_request_state: PurchaseRequestState
    resolution: ResolutionResult
    expected_state_version: int
    next_state_version: int
    decided_at: datetime
    trace: tuple[ApprovalTraceObservation, ...]


class ApprovalUnitOfWork(Protocol):
    def load_human_approval(self, run_id: str) -> HumanApprovalState:
        """Load a ready human task or its existing waiting work item."""

    def commit_wait(self, command: EnterApprovalWaitCommand) -> None:
        """Atomically create one work item and enter persistent waiting."""

    def load_approval_decision(
        self,
        work_item_id: str,
    ) -> ApprovalDecisionState:
        """Load a pending item or its authoritative existing decision."""

    def commit_decision(self, command: CommitApprovalDecisionCommand) -> None:
        """Atomically decide, resume the same cursor, and append trace."""


@dataclass(frozen=True)
class ApprovalWorkItemView:
    work_item_id: str
    run_id: str
    purchase_request_id: str
    requester_name: str | None
    department: str | None
    item_or_service: str | None
    supplier: str | None
    amount: str
    currency: str
    business_justification: str
    required_date: str
    approval_state: str
    purchase_request_state: str
    run_status: str
    state_version: int
    created_at: datetime


class ApprovalQueryService(Protocol):
    def list_pending(self) -> tuple[ApprovalWorkItemView, ...]:
        """Return pending work items in stable creation order."""

    def get(self, work_item_id: str) -> ApprovalWorkItemView:
        """Return one work item with purchase_request and run context."""


@dataclass(frozen=True)
class ApprovalWaiting:
    run_id: str
    work_item_id: str
    committed_state_version: int
    replayed: bool


@dataclass(frozen=True)
class ApprovalDecisionAccepted:
    run_id: str
    work_item_id: str
    outcome: TaskOutcome
    committed_state_version: int
    resolution: ResolutionResult | None
    replayed: bool


class HumanApprovalService:
    def __init__(
        self,
        unit_of_work: ApprovalUnitOfWork,
        id_factory: Callable[[], str] | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._id_factory = id_factory or (lambda: str(uuid4()))
        self._clock = clock or (lambda: datetime.now(UTC))

    def enter_wait(
        self,
        run_id: str,
        *,
        expected_state_version: int | None = None,
    ) -> ApprovalWaiting:
        state = self._unit_of_work.load_human_approval(run_id)
        if isinstance(state, WaitingHumanApproval):
            if expected_state_version is not None and expected_state_version not in {
                state.state_version,
                state.state_version - 1,
            }:
                raise StateVersionConflict(
                    f"Expected state version {expected_state_version}, "
                    f"found waiting version {state.state_version}"
                )
            return ApprovalWaiting(
                state.run_id,
                state.work_item_id,
                state.state_version,
                replayed=True,
            )

        self._validate_human_task(state.task)
        self._check_version(state.state_version, expected_state_version)
        next_version = state.state_version + 1
        work_item_id = self._id_factory()
        command = EnterApprovalWaitCommand(
            run_id=state.run_id,
            purchase_request_id=state.purchase_request_id,
            task_id=state.task.id,
            work_item_id=work_item_id,
            expected_state_version=state.state_version,
            next_state_version=next_version,
            created_at=self._clock(),
            trace=(
                ApprovalTraceObservation(
                    TraceKind.WORKFLOW_STATE_CHANGED,
                    state.task.id,
                    f"state={PurchaseRequestState.PENDING_APPROVAL.value}",
                ),
                ApprovalTraceObservation(
                    TraceKind.WAITING_FOR_APPROVAL,
                    state.task.id,
                    f"work_item_id={work_item_id}",
                ),
            ),
        )
        self._unit_of_work.commit_wait(command)
        return ApprovalWaiting(
            state.run_id,
            work_item_id,
            next_version,
            replayed=False,
        )

    def decide(
        self,
        work_item_id: str,
        value: ApprovalDecisionInput,
        *,
        expected_state_version: int | None = None,
    ) -> ApprovalDecisionAccepted:
        decision = validate_approval_decision(value)
        state = self._unit_of_work.load_approval_decision(work_item_id)
        if isinstance(state, ExistingApprovalDecision):
            if decision != state.decision:
                raise ApprovalDecisionConflict(
                    "A conflicting decision already exists for this work item"
                )
            return ApprovalDecisionAccepted(
                run_id=state.run_id,
                work_item_id=state.work_item_id,
                outcome=state.outcome,
                committed_state_version=state.state_version,
                resolution=None,
                replayed=True,
            )

        self._validate_human_task(state.task)
        self._check_version(state.state_version, expected_state_version)
        outcome = (
            TaskOutcome.SUCCESS
            if decision.choice is ApprovalChoice.APPROVE
            else TaskOutcome.FAILURE
        )
        purchase_request_state = (
            PurchaseRequestState.APPROVED
            if outcome is TaskOutcome.SUCCESS
            else PurchaseRequestState.REJECTED
        )
        resolution = resolve_transition(
            state.task.id,
            outcome,
            state.transitions,
        )
        next_version = state.state_version + 1
        command = CommitApprovalDecisionCommand(
            run_id=state.run_id,
            purchase_request_id=state.purchase_request_id,
            task_id=state.task.id,
            work_item_id=state.work_item_id,
            decision_id=self._id_factory(),
            decision=decision,
            outcome=outcome,
            purchase_request_state=purchase_request_state,
            resolution=resolution,
            expected_state_version=state.state_version,
            next_state_version=next_version,
            decided_at=self._clock(),
            trace=self._decision_trace(
                state.task.id,
                decision,
                outcome,
                purchase_request_state,
                resolution,
            ),
        )
        self._unit_of_work.commit_decision(command)
        return ApprovalDecisionAccepted(
            run_id=state.run_id,
            work_item_id=state.work_item_id,
            outcome=outcome,
            committed_state_version=next_version,
            resolution=resolution,
            replayed=False,
        )

    @staticmethod
    def _validate_human_task(task: TaskDefinition) -> None:
        if task.task_type is not TaskType.HUMAN_APPROVAL:
            raise StepStateError("Current task is not HUMAN_APPROVAL")
        if task.max_attempts is not None:
            raise StepStateError("HUMAN_APPROVAL cannot have an attempt bound")

    @staticmethod
    def _check_version(actual: int, expected: int | None) -> None:
        if expected is not None and expected != actual:
            raise StateVersionConflict(
                f"Expected state version {expected}, found {actual}"
            )

    @staticmethod
    def _decision_trace(
        task_id: int,
        decision: ValidatedApprovalDecision,
        outcome: TaskOutcome,
        purchase_request_state: PurchaseRequestState,
        resolution: ResolutionResult,
    ) -> tuple[ApprovalTraceObservation, ...]:
        detail = f"decision={decision.choice.value}; outcome={outcome.value}"
        if decision.note is not None:
            detail += f"; note={decision.note}"
        if decision.reason is not None:
            detail += f"; reason={decision.reason}"
        observations = [
            ApprovalTraceObservation(TraceKind.APPROVAL_DECIDED, task_id, detail),
            ApprovalTraceObservation(
                TraceKind.WORKFLOW_STATE_CHANGED,
                task_id,
                f"state={purchase_request_state.value}",
            ),
            ApprovalTraceObservation(TraceKind.RUN_RESUMED, task_id),
        ]
        if isinstance(resolution, TransitionSelected):
            observations.append(
                ApprovalTraceObservation(
                    TraceKind.TRANSITION_SELECTED,
                    task_id,
                    transition_id=resolution.transition.id,
                )
            )
        elif isinstance(resolution, TerminalReached):
            terminal_kind = (
                TraceKind.SUCCESSFUL_TERMINAL
                if resolution.decision is TerminalDecision.SUCCESSFUL_TERMINAL
                else TraceKind.UNSUCCESSFUL_TERMINAL
            )
            observations.append(ApprovalTraceObservation(terminal_kind, task_id))
        return tuple(observations)
