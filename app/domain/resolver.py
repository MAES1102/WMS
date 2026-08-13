"""Shared transition-resolution policy for both execution modes."""

from app.domain.types import (
    ResolutionResult,
    TaskOutcome,
    TerminalDecision,
    TerminalReached,
    TransitionCondition,
    TransitionDefinition,
    TransitionSelected,
)


class ResolverAmbiguityError(Exception):
    """A validated definition should never contain equal-precedence ambiguity."""


def resolve_transition(
    from_task_id: int,
    outcome: TaskOutcome,
    transitions: tuple[TransitionDefinition, ...],
) -> ResolutionResult:
    """Resolve a specific condition before ALWAYS, or return terminal state."""
    try:
        normalized_outcome = TaskOutcome(outcome)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Unsupported task outcome {outcome!r}; expected SUCCESS or FAILURE"
        ) from exc

    outgoing = [
        transition
        for transition in transitions
        if transition.from_task_id == from_task_id
    ]
    specific_condition = TransitionCondition(normalized_outcome.value)
    specific = [
        transition
        for transition in outgoing
        if transition.condition == specific_condition
    ]
    if len(specific) > 1:
        raise ResolverAmbiguityError(
            f"Task {from_task_id} has {len(specific)} outgoing "
            f"{specific_condition.value} transitions"
        )
    if specific:
        return TransitionSelected(specific[0])

    fallback = [
        transition
        for transition in outgoing
        if transition.condition == TransitionCondition.ALWAYS
    ]
    if len(fallback) > 1:
        raise ResolverAmbiguityError(
            f"Task {from_task_id} has {len(fallback)} ALWAYS transitions"
        )
    if fallback:
        return TransitionSelected(fallback[0])

    decision = (
        TerminalDecision.SUCCESSFUL_TERMINAL
        if normalized_outcome == TaskOutcome.SUCCESS
        else TerminalDecision.UNSUCCESSFUL_TERMINAL
    )
    return TerminalReached(decision)
