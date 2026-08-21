from dataclasses import replace

import pytest

from app.application.errors import StepStateError
from app.application.orchestration import (
    CursorPhase,
    PurchaseRequestOrchestrator,
    RunControlState,
)
from app.domain.types import ExecutionMode, TaskType, TerminalDecision


class ScriptedReader:
    def __init__(self, states: list[RunControlState]) -> None:
        self.states = states
        self.index = 0

    def load_control_state(self, _run_id: str) -> RunControlState:
        state = self.states[min(self.index, len(self.states) - 1)]
        self.index += 1
        return state


class AutomaticSteps:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []

    def execute(self, run_id: str, *, expected_state_version: int):
        self.calls.append((run_id, expected_state_version))


class ApprovalWait:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []

    def enter_wait(self, run_id: str, *, expected_state_version: int):
        self.calls.append((run_id, expected_state_version))
        return type(
            "Waiting",
            (),
            {
                "committed_state_version": expected_state_version + 1,
                "work_item_id": "work-1",
                "replayed": False,
            },
        )()


def state(
    phase: CursorPhase,
    version: int,
    task_type: TaskType | None = None,
) -> RunControlState:
    return RunControlState(
        "run-1",
        ExecutionMode.ORCHESTRATION,
        phase,
        version,
        task_type,
        "work-1" if phase is CursorPhase.WAITING_FOR_APPROVAL else None,
        (
            TerminalDecision.SUCCESSFUL_TERMINAL
            if phase is CursorPhase.TERMINAL
            else None
        ),
    )


def test_central_loop_drives_automatic_steps_then_stops_for_human() -> None:
    reader = ScriptedReader(
        [
            state(CursorPhase.READY, 1, TaskType.REQUEST_VALIDATION),
            state(CursorPhase.READY, 2, TaskType.HUMAN_APPROVAL),
        ]
    )
    automatic = AutomaticSteps()
    approval = ApprovalWait()

    result = PurchaseRequestOrchestrator(reader, automatic, approval).drive("run-1")

    assert automatic.calls == [("run-1", 1)]
    assert approval.calls == [("run-1", 2)]
    assert result.phase is CursorPhase.WAITING_FOR_APPROVAL
    assert result.work_item_id == "work-1"
    assert result.committed_steps == 2


def test_terminal_and_existing_waiting_states_do_not_execute_again() -> None:
    automatic = AutomaticSteps()
    approval = ApprovalWait()
    terminal = PurchaseRequestOrchestrator(
        ScriptedReader([state(CursorPhase.TERMINAL, 8)]),
        automatic,
        approval,
    ).drive("run-1")
    waiting = PurchaseRequestOrchestrator(
        ScriptedReader([state(CursorPhase.WAITING_FOR_APPROVAL, 3)]),
        automatic,
        approval,
    ).drive("run-1")

    assert terminal.terminal_decision is TerminalDecision.SUCCESSFUL_TERMINAL
    assert waiting.work_item_id == "work-1"
    assert automatic.calls == []
    assert approval.calls == []


def test_orchestrator_rejects_other_mode_and_bounds_control_loop() -> None:
    ready = state(CursorPhase.READY, 1, TaskType.PURCHASE_AUTHORIZATION)
    choreography = replace(ready, mode=ExecutionMode.CHOREOGRAPHY)
    with pytest.raises(StepStateError, match="only orchestration"):
        PurchaseRequestOrchestrator(
            ScriptedReader([choreography]), AutomaticSteps(), ApprovalWait()
        ).drive("run-1")

    with pytest.raises(StepStateError, match="safety bound"):
        PurchaseRequestOrchestrator(
            ScriptedReader([ready]),
            AutomaticSteps(),
            ApprovalWait(),
            max_committed_steps=2,
        ).drive("run-1")
