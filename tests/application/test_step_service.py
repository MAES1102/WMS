from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from app.application.executors import (
    AutomaticExecutorRegistry,
    DeterministicFaultExecutor,
    DeterministicFaultSchedule,
    ExecutorRegistryError,
    FaultKey,
)
from app.application.ports import (
    AutomaticStepCommit,
    ExecutionContext,
    ReadyAutomaticStep,
    RetryCurrentTask,
    TraceKind,
)
from app.application.step_service import (
    AutomaticStepService,
    StateVersionConflict,
    StepStateError,
)
from app.domain.types import (
    FailureClass,
    TaskDefinition,
    TaskOutcome,
    TaskResult,
    TaskType,
    TransitionCondition,
    TransitionDefinition,
    TransitionSelected,
)


SUCCESS = TaskResult(TaskOutcome.SUCCESS)
RETRYABLE_FAILURE = TaskResult(
    TaskOutcome.FAILURE,
    FailureClass.RETRYABLE_TECHNICAL,
    "temporary storage fault",
)


class RecordingExecutor:
    def __init__(
        self,
        result: TaskResult = SUCCESS,
        events: list[str] | None = None,
    ) -> None:
        self.result = result
        self.events = events
        self.contexts: list[ExecutionContext] = []

    def execute(self, context: ExecutionContext) -> TaskResult:
        self.contexts.append(context)
        if self.events is not None:
            self.events.append("execute")
        return self.result


class FakeStepUnitOfWork:
    def __init__(
        self,
        state: ReadyAutomaticStep,
        tasks: tuple[TaskDefinition, ...],
        events: list[str] | None = None,
    ) -> None:
        self.state = state
        self.tasks = {task.id: task for task in tasks}
        self.events = events
        self.commits: list[AutomaticStepCommit] = []

    def load_ready_step(self, run_id: str) -> ReadyAutomaticStep:
        assert run_id == self.state.run_id
        return self.state

    def commit_automatic_step(self, command: AutomaticStepCommit) -> None:
        assert command.expected_state_version == self.state.state_version
        assert command.next_state_version == self.state.state_version + 1
        if self.events is not None:
            self.events.append("commit")
        self.commits.append(command)

        next_task = self.state.task
        completed_attempts = command.attempt_ordinal
        if isinstance(command.resolution, TransitionSelected):
            next_task = self.tasks[command.resolution.transition.to_task_id]
            completed_attempts = 0
        self.state = replace(
            self.state,
            task=next_task,
            completed_attempts=completed_attempts,
            state_version=command.next_state_version,
        )


class TickingClock:
    def __init__(self) -> None:
        self.current = datetime(2026, 8, 13, tzinfo=UTC)

    def __call__(self) -> datetime:
        value = self.current
        self.current += timedelta(milliseconds=1)
        return value


def automatic_task(
    task_id: int,
    *,
    name: str = "Archive invoice",
    max_attempts: int = 2,
) -> TaskDefinition:
    return TaskDefinition(
        id=task_id,
        name=name,
        task_type=TaskType.ARCHIVE_DOCUMENT,
        is_start=task_id == 1,
        max_attempts=max_attempts,
    )


def notification_task(task_id: int) -> TaskDefinition:
    return TaskDefinition(
        id=task_id,
        name="Notify submitter",
        task_type=TaskType.CREATE_NOTIFICATION,
        is_start=False,
        max_attempts=2,
    )


def registry_with(archive_executor) -> AutomaticExecutorRegistry:
    default = RecordingExecutor()
    return AutomaticExecutorRegistry(
        {
            TaskType.DOCUMENT_VALIDATION: default,
            TaskType.ARCHIVE_DOCUMENT: archive_executor,
            TaskType.CREATE_NOTIFICATION: default,
        }
    )


def ready_step(
    task: TaskDefinition,
    transitions: tuple[TransitionDefinition, ...],
) -> ReadyAutomaticStep:
    return ReadyAutomaticStep(
        run_id="run-1",
        invoice_id="invoice-1",
        task=task,
        transitions=transitions,
        completed_attempts=0,
        state_version=1,
    )


def test_registry_requires_the_complete_closed_automatic_catalog() -> None:
    executor = RecordingExecutor()
    with pytest.raises(ExecutorRegistryError, match="Missing automatic executors"):
        AutomaticExecutorRegistry({TaskType.ARCHIVE_DOCUMENT: executor})

    with pytest.raises(ExecutorRegistryError, match="not an automatic executor"):
        AutomaticExecutorRegistry(
            {
                TaskType.DOCUMENT_VALIDATION: executor,
                TaskType.ARCHIVE_DOCUMENT: executor,
                TaskType.CREATE_NOTIFICATION: executor,
                TaskType.HUMAN_APPROVAL: executor,
            }
        )


def test_fault_schedule_uses_run_task_and_attempt_not_display_name() -> None:
    wrapped = RecordingExecutor()
    schedule = DeterministicFaultSchedule(
        {FaultKey("run-1", 7): (RETRYABLE_FAILURE,)}
    )
    executor = DeterministicFaultExecutor(wrapped, schedule)

    first = executor.execute(
        ExecutionContext(
            run_id="run-1",
            invoice_id="invoice-1",
            task_id=7,
            task_type=TaskType.ARCHIVE_DOCUMENT,
            attempt_ordinal=1,
        )
    )
    second = executor.execute(
        ExecutionContext(
            run_id="run-1",
            invoice_id="invoice-1",
            task_id=7,
            task_type=TaskType.ARCHIVE_DOCUMENT,
            attempt_ordinal=2,
        )
    )

    assert first == RETRYABLE_FAILURE
    assert second == SUCCESS
    assert len(wrapped.contexts) == 1


def test_success_route_commits_attempt_trace_and_selected_transition() -> None:
    archive = automatic_task(1)
    notify = notification_task(2)
    transition = TransitionDefinition(
        id=11,
        from_task_id=archive.id,
        to_task_id=notify.id,
        condition=TransitionCondition.SUCCESS,
    )
    executor = RecordingExecutor()
    uow = FakeStepUnitOfWork(
        ready_step(archive, (transition,)),
        (archive, notify),
    )
    service = AutomaticStepService(uow, registry_with(executor), TickingClock())

    completed = service.execute("run-1", expected_state_version=1)

    assert isinstance(completed.resolution, TransitionSelected)
    assert completed.resolution.transition == transition
    assert completed.committed_state_version == 2
    assert len(uow.commits) == 1
    assert uow.commits[0].result == SUCCESS
    assert [item.kind for item in uow.commits[0].trace] == [
        TraceKind.ATTEMPT_OUTCOME,
        TraceKind.TRANSITION_SELECTED,
    ]


def test_retry_then_success_repeats_task_without_transition_during_retry() -> None:
    archive = automatic_task(1, name="Renamed archive step")
    notify = notification_task(2)
    transition = TransitionDefinition(
        id=12,
        from_task_id=archive.id,
        to_task_id=notify.id,
        condition=TransitionCondition.SUCCESS,
    )
    wrapped = RecordingExecutor()
    faulted = DeterministicFaultExecutor(
        wrapped,
        DeterministicFaultSchedule(
            {FaultKey("run-1", archive.id): (RETRYABLE_FAILURE,)}
        ),
    )
    uow = FakeStepUnitOfWork(
        ready_step(archive, (transition,)),
        (archive, notify),
    )
    service = AutomaticStepService(uow, registry_with(faulted), TickingClock())

    first = service.execute("run-1", expected_state_version=1)
    second = service.execute("run-1", expected_state_version=2)

    assert first.resolution == RetryCurrentTask(archive.id, 2)
    assert [item.kind for item in uow.commits[0].trace] == [
        TraceKind.ATTEMPT_OUTCOME,
        TraceKind.RETRY_OBSERVATION,
    ]
    assert all(
        item.kind is not TraceKind.TRANSITION_SELECTED
        for item in uow.commits[0].trace
    )
    assert isinstance(second.resolution, TransitionSelected)
    assert [commit.attempt_ordinal for commit in uow.commits] == [1, 2]
    assert len(wrapped.contexts) == 1


def test_exhausted_retryable_failure_enters_normal_failure_route() -> None:
    archive = automatic_task(1, max_attempts=2)
    notify = notification_task(2)
    failure_transition = TransitionDefinition(
        id=13,
        from_task_id=archive.id,
        to_task_id=notify.id,
        condition=TransitionCondition.FAILURE,
    )
    faulted = DeterministicFaultExecutor(
        RecordingExecutor(),
        DeterministicFaultSchedule(
            {
                FaultKey("run-1", archive.id): (
                    RETRYABLE_FAILURE,
                    RETRYABLE_FAILURE,
                )
            }
        ),
    )
    uow = FakeStepUnitOfWork(
        ready_step(archive, (failure_transition,)),
        (archive, notify),
    )
    service = AutomaticStepService(uow, registry_with(faulted), TickingClock())

    first = service.execute("run-1", expected_state_version=1)
    exhausted = service.execute("run-1", expected_state_version=2)

    assert isinstance(first.resolution, RetryCurrentTask)
    assert isinstance(exhausted.resolution, TransitionSelected)
    assert exhausted.resolution.transition == failure_transition
    assert [item.kind for item in uow.commits[1].trace] == [
        TraceKind.ATTEMPT_OUTCOME,
        TraceKind.TRANSITION_SELECTED,
    ]


def test_commit_finishes_before_caller_can_emit_the_next_trigger() -> None:
    events: list[str] = []
    task = automatic_task(1, max_attempts=1)
    executor = RecordingExecutor(events=events)
    uow = FakeStepUnitOfWork(ready_step(task, ()), (task,), events)
    service = AutomaticStepService(uow, registry_with(executor), TickingClock())

    completed = service.execute("run-1")
    events.append(f"trigger:{completed.committed_state_version}")

    assert events == ["execute", "commit", "trigger:2"]


def test_stale_state_version_and_human_task_stop_before_execution() -> None:
    executor = RecordingExecutor()
    task = automatic_task(1)
    uow = FakeStepUnitOfWork(ready_step(task, ()), (task,))
    service = AutomaticStepService(uow, registry_with(executor), TickingClock())

    with pytest.raises(StateVersionConflict):
        service.execute("run-1", expected_state_version=99)
    assert executor.contexts == []
    assert uow.commits == []

    human = replace(
        task,
        task_type=TaskType.HUMAN_APPROVAL,
        max_attempts=None,
    )
    human_uow = FakeStepUnitOfWork(ready_step(human, ()), (human,))
    human_service = AutomaticStepService(
        human_uow,
        registry_with(executor),
        TickingClock(),
    )
    with pytest.raises(StepStateError, match="approval lifecycle"):
        human_service.execute("run-1")
    assert human_uow.commits == []

    exhausted_uow = FakeStepUnitOfWork(
        replace(ready_step(task, ()), completed_attempts=2),
        (task,),
    )
    exhausted_service = AutomaticStepService(
        exhausted_uow,
        registry_with(executor),
        TickingClock(),
    )
    with pytest.raises(StepStateError, match="already exhausted"):
        exhausted_service.execute("run-1")
    assert exhausted_uow.commits == []


def test_application_layer_has_no_framework_or_persistence_imports() -> None:
    root = Path(__file__).parents[2] / "app" / "application"
    sources = {path.name: path.read_text() for path in root.glob("*.py")}
    source = "\n".join(sources.values())
    forbidden = (
        "fastapi",
        "sqlalchemy",
        "app.models",
        "app.persistence",
        "app.routes",
        "app.engine",
    )
    assert all(name not in source for name in forbidden)
    assert [
        name
        for name, text in sources.items()
        if "from app.domain.retry import should_retry" in text
    ] == ["step_service.py"]
    assert {
        name
        for name, text in sources.items()
        if "from app.domain.resolver import resolve_transition" in text
    } == {"step_service.py", "approval.py"}
