"""Purchase Request business data and deterministic validation."""

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from enum import Enum

_DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
_AMOUNT_PATTERN = re.compile(r"\d+(?:\.\d{1,2})?\Z")
_CURRENCY_PATTERN = re.compile(r"[A-Z]{3}\Z", re.ASCII)
_MAX_AMOUNT = Decimal("999999999.99")
MIN_JUSTIFICATION_LENGTH = 20


class PurchaseRequestState(str, Enum):
    SUBMITTED = "SUBMITTED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    AUTHORIZED = "AUTHORIZED"
    NEEDS_MANUAL_ACTION = "NEEDS_MANUAL_ACTION"


@dataclass(frozen=True)
class RawPurchaseRequest:
    requester_name: str
    department: str
    item_or_service: str
    supplier: str
    amount: str
    currency: str
    business_justification: str
    required_date: str


@dataclass(frozen=True)
class ValidatedPurchaseRequest:
    requester_name: str
    department: str
    item_or_service: str
    supplier: str
    amount: Decimal
    currency: str
    business_justification: str
    required_date: date


@dataclass(frozen=True)
class PurchaseRequestIssue:
    field: str
    detail: str


class PurchaseRequestValidationError(ValueError):
    def __init__(self, issues: list[PurchaseRequestIssue]) -> None:
        self.issues = tuple(issues)
        super().__init__("; ".join(f"{i.field}: {i.detail}" for i in issues))


def validate_purchase_request(
    value: RawPurchaseRequest, *, submitted_on: date
) -> ValidatedPurchaseRequest:
    """Normalize a structured request or report every deterministic issue."""
    issues: list[PurchaseRequestIssue] = []
    fields = {
        "requester_name": (value.requester_name, 120),
        "department": (value.department, 120),
        "item_or_service": (value.item_or_service, 200),
        "supplier": (value.supplier, 120),
    }
    normalized: dict[str, str] = {}
    for field, (raw, maximum) in fields.items():
        text = raw.strip() if isinstance(raw, str) else ""
        normalized[field] = text
        if not 1 <= len(text) <= maximum:
            issues.append(PurchaseRequestIssue(field, f"trimmed length must be between 1 and {maximum} characters"))

    justification = value.business_justification.strip() if isinstance(value.business_justification, str) else ""
    if not MIN_JUSTIFICATION_LENGTH <= len(justification) <= 1000:
        issues.append(PurchaseRequestIssue("business_justification", f"trimmed length must be between {MIN_JUSTIFICATION_LENGTH} and 1000 characters"))

    amount: Decimal | None = None
    if isinstance(value.amount, str) and _AMOUNT_PATTERN.fullmatch(value.amount):
        try:
            candidate = Decimal(value.amount)
        except InvalidOperation:
            candidate = Decimal(0)
        if Decimal(0) < candidate <= _MAX_AMOUNT:
            amount = candidate
    if amount is None:
        issues.append(PurchaseRequestIssue("amount", "must be positive, at most 999999999.99, and have at most two decimal places"))

    if not isinstance(value.currency, str) or not _CURRENCY_PATTERN.fullmatch(value.currency):
        issues.append(PurchaseRequestIssue("currency", "must contain exactly three uppercase ASCII letters"))

    required_date: date | None = None
    if isinstance(value.required_date, str) and _DATE_PATTERN.fullmatch(value.required_date):
        try:
            required_date = date.fromisoformat(value.required_date)
        except ValueError:
            pass
    if required_date is None:
        issues.append(PurchaseRequestIssue("required_date", "must be a valid date in YYYY-MM-DD form"))
    elif required_date < submitted_on:
        issues.append(PurchaseRequestIssue("required_date", "must not be earlier than the submission date"))

    if issues:
        raise PurchaseRequestValidationError(issues)
    assert amount is not None and required_date is not None
    return ValidatedPurchaseRequest(
        requester_name=normalized["requester_name"], department=normalized["department"],
        item_or_service=normalized["item_or_service"], supplier=normalized["supplier"],
        amount=amount, currency=value.currency, business_justification=justification,
        required_date=required_date,
    )
