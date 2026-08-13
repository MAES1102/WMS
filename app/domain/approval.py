"""Pure approval-decision validation."""

from dataclasses import dataclass
from enum import Enum


class ApprovalChoice(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"


@dataclass(frozen=True)
class ApprovalDecisionInput:
    choice: ApprovalChoice
    note: str | None = None
    reason: str | None = None


@dataclass(frozen=True)
class ValidatedApprovalDecision:
    choice: ApprovalChoice
    note: str | None
    reason: str | None


class ApprovalDecisionError(ValueError):
    pass


def validate_approval_decision(
    value: ApprovalDecisionInput,
) -> ValidatedApprovalDecision:
    try:
        choice = ApprovalChoice(value.choice)
    except (TypeError, ValueError) as exc:
        raise ApprovalDecisionError(
            f"Unsupported approval choice {value.choice!r}"
        ) from exc

    if value.note is not None and not isinstance(value.note, str):
        raise ApprovalDecisionError("Approval note must be text or null")
    if value.reason is not None and not isinstance(value.reason, str):
        raise ApprovalDecisionError("Rejection reason must be text or null")

    if choice is ApprovalChoice.APPROVE:
        if value.reason is not None:
            raise ApprovalDecisionError("Approval cannot contain a rejection reason")
        if value.note is not None and len(value.note) > 500:
            raise ApprovalDecisionError("Approval note cannot exceed 500 characters")
        return ValidatedApprovalDecision(choice, value.note, None)

    if value.note is not None:
        raise ApprovalDecisionError("Rejection cannot contain an approval note")
    reason = value.reason.strip() if value.reason is not None else ""
    if not 1 <= len(reason) <= 500:
        raise ApprovalDecisionError(
            "Rejection reason must contain 1 to 500 trimmed characters"
        )
    return ValidatedApprovalDecision(choice, None, reason)
