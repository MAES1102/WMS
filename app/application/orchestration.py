"""Centralized execution control over shared automatic and human-step services."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol, TYPE_CHECKING

from app.application.approval import (
    ApprovalDecisionAccepted,
    HumanApprovalService,
)
from app.application.errors import StepStateError
from app.application.step_service import AutomaticStepService
from app.domain.approval import ApprovalDecisionInput
from app.domain.types import DemoScenario, ExecutionMode, TaskType, TerminalDecision

if TYPE_CHECKING:
    from app.application.choreography import ChoreographyResult, PurchaseRequestChoreographer


class PurchaseRequestRunNotFound(LookupError):
    pass


class CursorPhase(str, Enum):
    READY = "READY"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    TERMINAL = "TERMINAL"


@dataclass(frozen=True)
class RunControlState:
    run_id: str
    mode: ExecutionMode
    phase: CursorPhase
    state_version: int
    task_type: TaskType | None
    work_item_id: str | None
    terminal_decision: TerminalDecision | None


class RunControlReader(Protocol):
    def load_control_state(self, run_id: str) -> RunControlState:
        """Load the committed cursor state used for the next control decision."""


@dataclass(frozen=True)
class OrchestrationResult:
    run_id: str
    phase: CursorPhase
    state_version: int
    committed_steps: int
    work_item_id: str | None = None
    terminal_decision: TerminalDecision | None = None


class PurchaseRequestOrchestrator:
    """Drive one run centrally until persistent waiting or terminal state."""

    def __init__(
        self,
        state_reader: RunControlReader,
        automatic_steps: AutomaticStepService,
        approvals: HumanApprovalService,
        *,
        max_committed_steps: int = 64,
    ) -> None:
        if max_committed_steps < 1:
            raise ValueError("max_committed_steps must be positive")
        self._state_reader = state_reader
        self._automatic_steps = automatic_steps
        self._approvals = approvals
        self._max_committed_steps = max_committed_steps

    def drive(self, run_id: str) -> OrchestrationResult:
        committed_steps = 0
        while committed_steps < self._max_committed_steps:
            state = self._state_reader.load_control_state(run_id)
            self._validate_state(state, run_id)

            if state.phase is CursorPhase.TERMINAL:
                return OrchestrationResult(
                    run_id=run_id,
                    phase=state.phase,
                    state_version=state.state_version,
                    committed_steps=committed_steps,
                    terminal_decision=state.terminal_decision,
                )
            if state.phase is CursorPhase.WAITING_FOR_APPROVAL:
                return OrchestrationResult(
                    run_id=run_id,
                    phase=state.phase,
                    state_version=state.state_version,
                    committed_steps=committed_steps,
                    work_item_id=state.work_item_id,
                )

            if state.task_type is TaskType.HUMAN_APPROVAL:
                waiting = self._approvals.enter_wait(
                    run_id,
                    expected_state_version=state.state_version,
                )
                return OrchestrationResult(
                    run_id=run_id,
                    phase=CursorPhase.WAITING_FOR_APPROVAL,
                    state_version=waiting.committed_state_version,
                    committed_steps=committed_steps + (0 if waiting.replayed else 1),
                    work_item_id=waiting.work_item_id,
                )

            self._automatic_steps.execute(
                run_id,
                expected_state_version=state.state_version,
            )
            committed_steps += 1

        raise StepStateError(
            f"Orchestration safety bound {self._max_committed_steps} exceeded"
        )

    @staticmethod
    def _validate_state(state: RunControlState, requested_run_id: str) -> None:
        if state.run_id != requested_run_id:
            raise StepStateError("Control state belongs to a different run")
        if state.mode is not ExecutionMode.ORCHESTRATION:
            raise StepStateError(
                "PurchaseRequestOrchestrator can drive only orchestration runs"
            )
        if state.state_version < 1:
            raise StepStateError("Control state_version must be positive")
        if state.phase is CursorPhase.READY and state.task_type is None:
            raise StepStateError("Ready cursor has no current task type")
        if (
            state.phase is CursorPhase.WAITING_FOR_APPROVAL
            and state.work_item_id is None
        ):
            raise StepStateError("Waiting cursor has no approval work item")
        if (
            state.phase is CursorPhase.TERMINAL
            and state.terminal_decision is None
        ):
            raise StepStateError("Terminal cursor has no terminal decision")


@dataclass(frozen=True)
class OrchestratedDecisionResult:
    decision: ApprovalDecisionAccepted
    execution: "OrchestrationResult | ChoreographyResult"


class PurchaseRequestExecutionCoordinator:
    """Select the persisted run's control strategy and resume the same run."""

    def __init__(
        self,
        orchestrator: PurchaseRequestOrchestrator,
        approvals: HumanApprovalService,
        choreographer: "PurchaseRequestChoreographer | None" = None,
        state_reader: RunControlReader | None = None,
    ) -> None:
        self._orchestrator = orchestrator
        self._approvals = approvals
        self._choreographer = choreographer
        self._state_reader = state_reader

    def drive(
        self,
        run_id: str,
    ) -> "OrchestrationResult | ChoreographyResult":
        if self._choreographer is None:
            return self._orchestrator.drive(run_id)
        if self._state_reader is None:
            raise RuntimeError(
                "A RunControlReader is required when choreography is configured"
            )
        mode = self._state_reader.load_control_state(run_id).mode
        if mode is ExecutionMode.ORCHESTRATION:
            return self._orchestrator.drive(run_id)
        if mode is ExecutionMode.CHOREOGRAPHY:
            return self._choreographer.drive(run_id)
        raise StepStateError(f"Unsupported execution mode {mode!r}")

    def decide_and_resume(
        self,
        work_item_id: str,
        decision: ApprovalDecisionInput,
        *,
        expected_state_version: int | None = None,
    ) -> OrchestratedDecisionResult:
        accepted = self._approvals.decide(
            work_item_id,
            decision,
            expected_state_version=expected_state_version,
        )
        execution = self.drive(accepted.run_id)
        return OrchestratedDecisionResult(accepted, execution)


@dataclass(frozen=True)
class ApprovalResultView:
    decision: str
    note: str | None
    reason: str | None
    decided_at: datetime


@dataclass(frozen=True)
class PurchaseRequestTraceView:
    position: int
    kind: str
    task_id: int | None
    attempt_ordinal: int | None
    detail: str | None
    timestamp: datetime


@dataclass(frozen=True)
class PurchaseRequestRunStatusView:
    purchase_request_id: str
    requester_name: str
    department: str
    item_or_service: str
    supplier: str
    amount: str
    currency: str
    business_justification: str
    required_date: str
    run_id: str
    execution_mode: ExecutionMode
    scenario: DemoScenario
    purchase_request_state: str
    run_status: str
    cursor_phase: CursorPhase
    state_version: int
    terminal_decision: TerminalDecision | None
    approval: ApprovalResultView | None
    purchase_authorization_code: str | None
    notification: str | None
    trace: tuple[PurchaseRequestTraceView, ...]


class PurchaseRequestRunQueryService(Protocol):
    def get(self, run_id: str) -> PurchaseRequestRunStatusView:
        """Return one isolated business/run projection with ordered history."""
