"""Shared transaction-bounded service for one automatic workflow step."""

from collections.abc import Callable
from datetime import UTC, datetime

from app.application.errors import StateVersionConflict, StepStateError
from app.application.executors import AutomaticExecutorRegistry
from app.application.ports import (
    AutomaticStepCommit,
    AutomaticStepCompleted,
    AutomaticStepEffectPolicy,
    AutomaticStepUnitOfWork,
    InternalNotificationCreated,
    ExecutionContext,
    InvoiceStateChanged,
    ReadyAutomaticStep,
    RetryCurrentTask,
    StepEffect,
    TraceKind,
    TraceObservation,
)
from app.domain.resolver import resolve_transition
from app.domain.retry import should_retry
from app.domain.types import (
    TaskResult,
    TerminalDecision,
    TerminalReached,
    TransitionSelected,
)


class AutomaticStepService:
    """Own retry and routing policy for both execution modes."""

    def __init__(
        self,
        unit_of_work: AutomaticStepUnitOfWork,
        registry: AutomaticExecutorRegistry,
        clock: Callable[[], datetime] | None = None,
        effect_policy: AutomaticStepEffectPolicy | None = None,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._registry = registry
        self._clock = clock or (lambda: datetime.now(UTC))
        self._effect_policy = effect_policy or _NoAutomaticStepEffects()

    def execute(
        self,
        run_id: str,
        *,
        expected_state_version: int | None = None,
    ) -> AutomaticStepCompleted:
        step = self._unit_of_work.load_ready_step(run_id)
        self._validate_step(step, run_id, expected_state_version)

        attempt_ordinal = step.completed_attempts + 1
        context = ExecutionContext(
            run_id=step.run_id,
            invoice_id=step.invoice_id,
            task_id=step.task.id,
            task_type=step.task.task_type,
            attempt_ordinal=attempt_ordinal,
        )
        executor = self._registry.executor_for(step.task.task_type)
        started_at = self._clock()
        result = executor.execute(context)
        finished_at = self._clock()
        if not isinstance(result, TaskResult):
            raise TypeError("TaskExecutor.execute must return TaskResult")
        if finished_at < started_at:
            raise StepStateError("Step clock moved backwards during execution")

        if should_retry(
            task_type=step.task.task_type,
            result=result,
            completed_attempts=attempt_ordinal,
            max_attempts=step.task.max_attempts,
        ):
            resolution = RetryCurrentTask(
                task_id=step.task.id,
                next_attempt_ordinal=attempt_ordinal + 1,
            )
        else:
            resolution = resolve_transition(
                step.task.id,
                result.outcome,
                step.transitions,
            )

        effects = self._effect_policy.effects_for(context, result, resolution)

        next_version = step.state_version + 1
        command = AutomaticStepCommit(
            run_id=step.run_id,
            expected_state_version=step.state_version,
            next_state_version=next_version,
            task_id=step.task.id,
            attempt_ordinal=attempt_ordinal,
            result=result,
            started_at=started_at,
            finished_at=finished_at,
            resolution=resolution,
            effects=effects,
            trace=self._trace_for(
                task_id=step.task.id,
                attempt_ordinal=attempt_ordinal,
                result=result,
                resolution=resolution,
                effects=effects,
            ),
        )
        self._unit_of_work.commit_automatic_step(command)
        return AutomaticStepCompleted(
            run_id=step.run_id,
            committed_state_version=next_version,
            resolution=resolution,
        )

    @staticmethod
    def _validate_step(
        step: ReadyAutomaticStep,
        requested_run_id: str,
        expected_state_version: int | None,
    ) -> None:
        if step.run_id != requested_run_id:
            raise StepStateError("Loaded step belongs to a different run")
        if not step.task.task_type.is_automatic:
            raise StepStateError(
                "HUMAN_APPROVAL must enter the persistent approval lifecycle"
            )
        if step.completed_attempts < 0:
            raise StepStateError("completed_attempts cannot be negative")
        max_attempts = step.task.max_attempts
        if (
            not isinstance(max_attempts, int)
            or isinstance(max_attempts, bool)
            or max_attempts < 1
        ):
            raise StepStateError(
                "Automatic task max_attempts must be a positive integer"
            )
        if step.completed_attempts >= max_attempts:
            raise StepStateError("Automatic task attempt bound is already exhausted")
        if step.state_version < 1:
            raise StepStateError("state_version must be positive")
        if (
            expected_state_version is not None
            and expected_state_version != step.state_version
        ):
            raise StateVersionConflict(
                f"Expected state version {expected_state_version}, "
                f"found {step.state_version}"
            )

    @staticmethod
    def _trace_for(
        *,
        task_id: int,
        attempt_ordinal: int,
        result: TaskResult,
        resolution: RetryCurrentTask | TransitionSelected | TerminalReached,
        effects: tuple[StepEffect, ...],
    ) -> tuple[TraceObservation, ...]:
        detail = f"outcome={result.outcome.value}"
        if result.failure_class is not None:
            detail += f"; failure_class={result.failure_class.value}"
        if result.reason:
            detail += f"; reason={result.reason}"

        observations = [
            TraceObservation(
                kind=TraceKind.ATTEMPT_OUTCOME,
                task_id=task_id,
                attempt_ordinal=attempt_ordinal,
                detail=detail,
            )
        ]
        observations.extend(
            TraceObservation(
                kind=TraceKind.INVOICE_STATE_CHANGED,
                task_id=task_id,
                attempt_ordinal=attempt_ordinal,
                detail=f"state={effect.state.value}"
                + (f"; reason={effect.reason}" if effect.reason else ""),
            )
            for effect in effects
            if isinstance(effect, InvoiceStateChanged)
        )
        observations.extend(
            TraceObservation(
                kind=TraceKind.NOTIFICATION_CREATED,
                task_id=task_id,
                attempt_ordinal=attempt_ordinal,
                detail=effect.message,
            )
            for effect in effects
            if isinstance(effect, InternalNotificationCreated)
        )
        if isinstance(resolution, RetryCurrentTask):
            observations.append(
                TraceObservation(
                    kind=TraceKind.RETRY_OBSERVATION,
                    task_id=task_id,
                    attempt_ordinal=attempt_ordinal,
                    detail=f"next_attempt={resolution.next_attempt_ordinal}",
                )
            )
        elif isinstance(resolution, TransitionSelected):
            observations.append(
                TraceObservation(
                    kind=TraceKind.TRANSITION_SELECTED,
                    task_id=task_id,
                    attempt_ordinal=attempt_ordinal,
                    transition_id=resolution.transition.id,
                )
            )
        else:
            terminal_kind = (
                TraceKind.SUCCESSFUL_TERMINAL
                if resolution.decision is TerminalDecision.SUCCESSFUL_TERMINAL
                else TraceKind.UNSUCCESSFUL_TERMINAL
            )
            observations.append(
                TraceObservation(
                    kind=terminal_kind,
                    task_id=task_id,
                    attempt_ordinal=attempt_ordinal,
                )
            )
        return tuple(observations)


class _NoAutomaticStepEffects:
    def effects_for(
        self,
        _context: ExecutionContext,
        _result: TaskResult,
        _resolution=None,
    ) -> tuple[StepEffect, ...]:
        return ()
