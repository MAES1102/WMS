import pytest

from app.domain.approval import (
    ApprovalChoice,
    ApprovalDecisionError,
    ApprovalDecisionInput,
    validate_approval_decision,
)


def test_approve_accepts_optional_bounded_note() -> None:
    validated = validate_approval_decision(
        ApprovalDecisionInput(ApprovalChoice.APPROVE, note="Looks correct")
    )

    assert validated.choice is ApprovalChoice.APPROVE
    assert validated.note == "Looks correct"
    assert validated.reason is None


def test_reject_requires_and_trims_reason() -> None:
    validated = validate_approval_decision(
        ApprovalDecisionInput(ApprovalChoice.REJECT, reason="  duplicate purchase_request  ")
    )

    assert validated.choice is ApprovalChoice.REJECT
    assert validated.note is None
    assert validated.reason == "duplicate purchase_request"


@pytest.mark.parametrize(
    "value",
    [
        ApprovalDecisionInput(ApprovalChoice.APPROVE, reason="not allowed"),
        ApprovalDecisionInput(ApprovalChoice.APPROVE, note="x" * 501),
        ApprovalDecisionInput(ApprovalChoice.REJECT),
        ApprovalDecisionInput(ApprovalChoice.REJECT, note="not allowed", reason="x"),
        ApprovalDecisionInput(ApprovalChoice.REJECT, reason="   "),
        ApprovalDecisionInput(ApprovalChoice.REJECT, reason="x" * 501),
    ],
)
def test_invalid_decision_payloads_are_rejected(value: ApprovalDecisionInput) -> None:
    with pytest.raises(ApprovalDecisionError):
        validate_approval_decision(value)
