"""Closed automatic-executor registry and deterministic verification adapter."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType

from app.application.ports import ExecutionContext, TaskExecutor
from app.domain.types import (
    DemoScenario,
    FailureClass,
    TaskOutcome,
    TaskResult,
    TaskType,
)


AUTOMATIC_TASK_TYPES = frozenset(
    task_type for task_type in TaskType if task_type.is_automatic
)


class ExecutorRegistryError(ValueError):
    pass


class AutomaticExecutorRegistry:
    """Complete registry for the closed automatic task catalog."""

    def __init__(self, executors: Mapping[TaskType, TaskExecutor]) -> None:
        normalized: dict[TaskType, TaskExecutor] = {}
        for raw_type, executor in executors.items():
            try:
                task_type = TaskType(raw_type)
            except (TypeError, ValueError) as exc:
                raise ExecutorRegistryError(
                    f"Unsupported executor task type {raw_type!r}"
                ) from exc
            if not task_type.is_automatic:
                raise ExecutorRegistryError(
                    "HUMAN_APPROVAL is not an automatic executor"
                )
            if not callable(getattr(executor, "execute", None)):
                raise ExecutorRegistryError(
                    f"Executor for {task_type.value} has no execute method"
                )
            normalized[task_type] = executor

        missing = AUTOMATIC_TASK_TYPES - normalized.keys()
        if missing:
            names = ", ".join(sorted(task_type.value for task_type in missing))
            raise ExecutorRegistryError(f"Missing automatic executors: {names}")

        self._executors = MappingProxyType(normalized)

    def executor_for(self, task_type: TaskType) -> TaskExecutor:
        try:
            normalized_type = TaskType(task_type)
        except (TypeError, ValueError) as exc:
            raise ExecutorRegistryError(
                f"Unsupported executor task type {task_type!r}"
            ) from exc
        if not normalized_type.is_automatic:
            raise ExecutorRegistryError(
                "HUMAN_APPROVAL must use the persistent approval lifecycle"
            )
        return self._executors[normalized_type]


@dataclass(frozen=True)
class FaultKey:
    run_id: str
    task_id: int


class DeterministicFaultSchedule:
    """Attempt-indexed results keyed only by stable run and task identity."""

    def __init__(
        self,
        results: Mapping[FaultKey, tuple[TaskResult, ...]],
    ) -> None:
        copied: dict[FaultKey, tuple[TaskResult, ...]] = {}
        for key, sequence in results.items():
            if not isinstance(key, FaultKey):
                raise ValueError("Fault schedule keys must be FaultKey values")
            if not key.run_id or key.task_id < 1:
                raise ValueError(
                    "Fault schedule keys require run_id and positive task_id"
                )
            if not sequence:
                raise ValueError("Fault result sequence cannot be empty")
            if not all(isinstance(result, TaskResult) for result in sequence):
                raise ValueError("Fault result sequence must contain TaskResult values")
            copied[key] = tuple(sequence)
        self._results = MappingProxyType(copied)

    def result_for(self, context: ExecutionContext) -> TaskResult | None:
        if context.attempt_ordinal < 1:
            raise ValueError("attempt_ordinal must be positive")
        sequence = self._results.get(FaultKey(context.run_id, context.task_id))
        index = context.attempt_ordinal - 1
        if sequence is None or index >= len(sequence):
            return None
        return sequence[index]


class DeterministicFaultExecutor:
    """Return a scheduled verification result, otherwise call the real executor."""

    def __init__(
        self,
        wrapped: TaskExecutor,
        schedule: DeterministicFaultSchedule,
    ) -> None:
        self._wrapped = wrapped
        self._schedule = schedule

    def execute(self, context: ExecutionContext) -> TaskResult:
        scheduled = self._schedule.result_for(context)
        if scheduled is not None:
            return scheduled
        return self._wrapped.execute(context)


class ArchiveDemoFaultExecutor:
    """Apply one of two explicit archive-failure demonstrations."""

    def __init__(
        self,
        wrapped: TaskExecutor,
        scenario_for_run: Callable[[str], DemoScenario],
    ) -> None:
        self._wrapped = wrapped
        self._scenario_for_run = scenario_for_run

    def execute(self, context: ExecutionContext) -> TaskResult:
        if context.task_type is not TaskType.ARCHIVE_DOCUMENT:
            raise ValueError(
                "ArchiveDemoFaultExecutor requires ARCHIVE_DOCUMENT"
            )
        scenario = DemoScenario(self._scenario_for_run(context.run_id))
        should_fail = scenario is DemoScenario.ARCHIVE_UNAVAILABLE or (
            scenario is DemoScenario.RETRY_THEN_SUCCESS
            and context.attempt_ordinal == 1
        )
        if should_fail:
            return TaskResult(
                TaskOutcome.FAILURE,
                FailureClass.RETRYABLE_TECHNICAL,
                "demonstration: archive storage temporarily unavailable",
            )
        return self._wrapped.execute(context)
