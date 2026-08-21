"""Run-scoped choreography over the shared persisted step services."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from app.application.approval import HumanApprovalService
from app.application.errors import StateVersionConflict, StepStateError
from app.application.orchestration import (
    CursorPhase,
    RunControlReader,
    RunControlState,
)
from app.application.step_service import AutomaticStepService
from app.domain.types import ExecutionMode, TaskType, TerminalDecision


@dataclass(frozen=True)
class AdvanceRun:
    """Transient trigger carrying identity and the committed state version only."""

    run_id: str
    expected_state_version: int


AdvanceHandler = Callable[[AdvanceRun], None]


class RunScopedEventBus(Protocol):
    def subscribe(self, run_id: str, handler: AdvanceHandler) -> None:
        """Register one temporary handler for the selected run."""

    def unsubscribe(self, run_id: str, handler: AdvanceHandler) -> None:
        """Remove the exact handler registered for the selected run."""

    def publish(self, event: AdvanceRun) -> None:
        """Dispatch synchronously or raise a controlled missing-handler error."""


@dataclass(frozen=True)
class ChoreographyResult:
    run_id: str
    phase: CursorPhase
    state_version: int
    committed_steps: int
    work_item_id: str | None = None
    terminal_decision: TerminalDecision | None = None


class PurchaseRequestChoreographer:
    """Advance one run through temporary, run-keyed event reactions."""

    def __init__(
        self,
        state_reader: RunControlReader,
        automatic_steps: AutomaticStepService,
        approvals: HumanApprovalService,
        event_bus: RunScopedEventBus,
        *,
        max_committed_steps: int = 64,
    ) -> None:
        if max_committed_steps < 1:
            raise ValueError("max_committed_steps must be positive")
        self._state_reader = state_reader
        self._automatic_steps = automatic_steps
        self._approvals = approvals
        self._event_bus = event_bus
        self._max_committed_steps = max_committed_steps

    def drive(self, run_id: str) -> ChoreographyResult:
        initial = self._state_reader.load_control_state(run_id)
        self._validate_state(initial, run_id)
        if initial.phase is not CursorPhase.READY:
            return self._result_from_state(initial, committed_steps=0)

        committed_steps = 0
        final: ChoreographyResult | None = None

        def advance(event: AdvanceRun) -> None:
            nonlocal committed_steps, final
            if event.run_id != run_id:
                raise StepStateError("Advance event belongs to a different run")

            state = self._state_reader.load_control_state(run_id)
            self._validate_state(state, run_id)
            if state.state_version != event.expected_state_version:
                raise StateVersionConflict(
                    f"Expected state version {event.expected_state_version}, "
                    f"found {state.state_version}"
                )
            if state.phase is not CursorPhase.READY:
                final = self._result_from_state(state, committed_steps)
                return
            if committed_steps >= self._max_committed_steps:
                raise StepStateError(
                    f"Choreography safety bound {self._max_committed_steps} exceeded"
                )

            if state.task_type is TaskType.HUMAN_APPROVAL:
                waiting = self._approvals.enter_wait(
                    run_id,
                    expected_state_version=state.state_version,
                )
                if not waiting.replayed:
                    committed_steps += 1
                final = ChoreographyResult(
                    run_id=run_id,
                    phase=CursorPhase.WAITING_FOR_APPROVAL,
                    state_version=waiting.committed_state_version,
                    committed_steps=committed_steps,
                    work_item_id=waiting.work_item_id,
                )
                return

            completed = self._automatic_steps.execute(
                run_id,
                expected_state_version=state.state_version,
            )
            committed_steps += 1
            self._event_bus.publish(
                AdvanceRun(run_id, completed.committed_state_version)
            )

        self._event_bus.subscribe(run_id, advance)
        try:
            self._event_bus.publish(AdvanceRun(run_id, initial.state_version))
            if final is None:
                raise StepStateError(
                    "Choreography dispatch ended without waiting or terminal state"
                )
            return final
        finally:
            self._event_bus.unsubscribe(run_id, advance)

    @staticmethod
    def _validate_state(state: RunControlState, requested_run_id: str) -> None:
        if state.run_id != requested_run_id:
            raise StepStateError("Control state belongs to a different run")
        if state.mode is not ExecutionMode.CHOREOGRAPHY:
            raise StepStateError(
                "PurchaseRequestChoreographer can drive only choreography runs"
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

    @staticmethod
    def _result_from_state(
        state: RunControlState,
        committed_steps: int,
    ) -> ChoreographyResult:
        return ChoreographyResult(
            run_id=state.run_id,
            phase=state.phase,
            state_version=state.state_version,
            committed_steps=committed_steps,
            work_item_id=state.work_item_id,
            terminal_decision=state.terminal_decision,
        )
