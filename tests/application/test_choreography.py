from dataclasses import replace

import pytest

from app.application.choreography import InvoiceChoreographer
from app.application.errors import StateVersionConflict, StepStateError
from app.application.orchestration import CursorPhase, RunControlState
from app.domain.types import ExecutionMode, TaskType, TerminalDecision
from app.infrastructure.event_bus import InMemoryRunEventBus


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
        return type(
            "Completed",
            (),
            {"committed_state_version": expected_state_version + 1},
        )()


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
        ExecutionMode.CHOREOGRAPHY,
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


def test_events_advance_shared_steps_and_cleanup_at_waiting() -> None:
    bus = InMemoryRunEventBus()
    automatic = AutomaticSteps()
    approvals = ApprovalWait()
    reader = ScriptedReader(
        [
            state(CursorPhase.READY, 1, TaskType.DOCUMENT_VALIDATION),
            state(CursorPhase.READY, 1, TaskType.DOCUMENT_VALIDATION),
            state(CursorPhase.READY, 2, TaskType.HUMAN_APPROVAL),
        ]
    )

    result = InvoiceChoreographer(reader, automatic, approvals, bus).drive("run-1")

    assert automatic.calls == [("run-1", 1)]
    assert approvals.calls == [("run-1", 2)]
    assert result.phase is CursorPhase.WAITING_FOR_APPROVAL
    assert result.committed_steps == 2
    assert bus.subscriber_count == 0


def test_terminal_state_opens_no_subscription() -> None:
    bus = InMemoryRunEventBus()
    result = InvoiceChoreographer(
        ScriptedReader([state(CursorPhase.TERMINAL, 8)]),
        AutomaticSteps(),
        ApprovalWait(),
        bus,
    ).drive("run-1")

    assert result.terminal_decision is TerminalDecision.SUCCESSFUL_TERMINAL
    assert bus.subscriber_count == 0


def test_wrong_mode_version_conflict_and_errors_always_cleanup() -> None:
    choreography = state(CursorPhase.READY, 1, TaskType.ARCHIVE_DOCUMENT)
    with pytest.raises(StepStateError, match="only choreography"):
        InvoiceChoreographer(
            ScriptedReader(
                [replace(choreography, mode=ExecutionMode.ORCHESTRATION)]
            ),
            AutomaticSteps(),
            ApprovalWait(),
            InMemoryRunEventBus(),
        ).drive("run-1")

    bus = InMemoryRunEventBus()
    with pytest.raises(StateVersionConflict, match="Expected state version 1"):
        InvoiceChoreographer(
            ScriptedReader([choreography, replace(choreography, state_version=2)]),
            AutomaticSteps(),
            ApprovalWait(),
            bus,
        ).drive("run-1")
    assert bus.subscriber_count == 0

    bus = InMemoryRunEventBus()
    with pytest.raises(StepStateError, match="safety bound"):
        InvoiceChoreographer(
            ScriptedReader(
                [
                    choreography,
                    choreography,
                    replace(choreography, state_version=2),
                    replace(choreography, state_version=3),
                ]
            ),
            AutomaticSteps(),
            ApprovalWait(),
            bus,
            max_committed_steps=2,
        ).drive("run-1")
    assert bus.subscriber_count == 0
