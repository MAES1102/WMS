"""Pure validation for raw invoice metadata."""

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from enum import Enum


_DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
_AMOUNT_PATTERN = re.compile(r"\d+(?:\.\d{1,2})?\Z")
_CURRENCY_PATTERN = re.compile(r"[A-Z]{3}\Z", re.ASCII)
_MAX_AMOUNT = Decimal("999999999.99")


class InvoiceState(str, Enum):
    SUBMITTED = "SUBMITTED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"
    NEEDS_MANUAL_ACTION = "NEEDS_MANUAL_ACTION"


@dataclass(frozen=True)
class RawInvoiceMetadata:
    supplier_name: str
    invoice_number: str
    issue_date: str
    amount: str
    currency: str


@dataclass(frozen=True)
class ValidatedInvoiceMetadata:
    supplier_name: str
    invoice_number: str
    issue_date: date
    amount: Decimal
    currency: str


@dataclass(frozen=True)
class InvoiceMetadataIssue:
    field: str
    detail: str


class InvoiceMetadataError(ValueError):
    def __init__(self, issues: list[InvoiceMetadataIssue]) -> None:
        self.issues = tuple(issues)
        summary = "; ".join(
            f"{issue.field}: {issue.detail}" for issue in self.issues
        )
        super().__init__(summary)


def validate_invoice_metadata(
    metadata: RawInvoiceMetadata,
) -> ValidatedInvoiceMetadata:
    """Return normalized values or every section-6 field issue."""
    issues: list[InvoiceMetadataIssue] = []
    supplier_name = metadata.supplier_name.strip()
    invoice_number = metadata.invoice_number.strip()

    if not 1 <= len(supplier_name) <= 120:
        issues.append(
            InvoiceMetadataIssue(
                "supplier_name",
                "trimmed length must be between 1 and 120 characters",
            )
        )
    if not 1 <= len(invoice_number) <= 64:
        issues.append(
            InvoiceMetadataIssue(
                "invoice_number",
                "trimmed length must be between 1 and 64 characters",
            )
        )

    parsed_date: date | None = None
    if _DATE_PATTERN.fullmatch(metadata.issue_date):
        try:
            parsed_date = date.fromisoformat(metadata.issue_date)
        except ValueError:
            pass
    if parsed_date is None:
        issues.append(
            InvoiceMetadataIssue(
                "issue_date",
                "must be a valid calendar date in YYYY-MM-DD form",
            )
        )

    parsed_amount: Decimal | None = None
    if _AMOUNT_PATTERN.fullmatch(metadata.amount):
        try:
            candidate = Decimal(metadata.amount)
        except InvalidOperation:
            candidate = Decimal(0)
        if Decimal(0) < candidate <= _MAX_AMOUNT:
            parsed_amount = candidate
    if parsed_amount is None:
        issues.append(
            InvoiceMetadataIssue(
                "amount",
                "must be greater than 0, at most 999999999.99, "
                "and have at most two fractional digits",
            )
        )

    if not _CURRENCY_PATTERN.fullmatch(metadata.currency):
        issues.append(
            InvoiceMetadataIssue(
                "currency",
                "must contain exactly three uppercase ASCII letters",
            )
        )

    if issues:
        raise InvoiceMetadataError(issues)
    assert parsed_date is not None
    assert parsed_amount is not None
    return ValidatedInvoiceMetadata(
        supplier_name=supplier_name,
        invoice_number=invoice_number,
        issue_date=parsed_date,
        amount=parsed_amount,
        currency=metadata.currency,
    )
