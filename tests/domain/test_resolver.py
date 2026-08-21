from app.domain.resolver import resolve_transition
from app.domain.types import (
    TaskOutcome,
    TerminalDecision,
    TerminalReached,
    TransitionCondition,
    TransitionDefinition,
    TransitionSelected,
)


def test_specific_transition_precedes_always() -> None:
    specific = TransitionDefinition(1, 10, 20, TransitionCondition.SUCCESS)
    fallback = TransitionDefinition(2, 10, 30, TransitionCondition.ALWAYS)

    result = resolve_transition(10, TaskOutcome.SUCCESS, (fallback, specific))

    assert result == TransitionSelected(specific)


def test_always_is_used_only_without_specific_match() -> None:
    fallback = TransitionDefinition(1, 10, 30, TransitionCondition.ALWAYS)

    result = resolve_transition(10, TaskOutcome.FAILURE, (fallback,))

    assert result == TransitionSelected(fallback)


def test_no_transition_returns_outcome_specific_terminal() -> None:
    success = resolve_transition(10, TaskOutcome.SUCCESS, ())
    failure = resolve_transition(10, TaskOutcome.FAILURE, ())

    assert success == TerminalReached(TerminalDecision.SUCCESSFUL_TERMINAL)
    assert failure == TerminalReached(TerminalDecision.UNSUCCESSFUL_TERMINAL)
