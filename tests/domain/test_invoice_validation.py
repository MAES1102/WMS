from datetime import date
from decimal import Decimal

import pytest

from app.domain.invoice import (
    InvoiceMetadataError,
    RawInvoiceMetadata,
    validate_invoice_metadata,
)


def valid_metadata(**changes: str) -> RawInvoiceMetadata:
    values = {
        "supplier_name": "  Acme S.p.A.  ",
        "invoice_number": "  INV-2026-001  ",
        "issue_date": "2026-08-13",
        "amount": "100.50",
        "currency": "EUR",
    }
    values.update(changes)
    return RawInvoiceMetadata(**values)


def test_valid_metadata_is_trimmed_and_typed() -> None:
    result = validate_invoice_metadata(valid_metadata())

    assert result.supplier_name == "Acme S.p.A."
    assert result.invoice_number == "INV-2026-001"
    assert result.issue_date == date(2026, 8, 13)
    assert result.amount == Decimal("100.50")
    assert result.currency == "EUR"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("supplier_name", "   "),
        ("invoice_number", "x" * 65),
        ("issue_date", "2026-02-30"),
        ("issue_date", "13-08-2026"),
        ("amount", "0"),
        ("amount", "1.001"),
        ("amount", "1e2"),
        ("amount", "1000000000.00"),
        ("currency", "eur"),
        ("currency", "EURO"),
        ("currency", "ÉUR"),
    ],
)
def test_each_invalid_field_has_a_field_specific_issue(
    field: str,
    value: str,
) -> None:
    with pytest.raises(InvoiceMetadataError) as captured:
        validate_invoice_metadata(valid_metadata(**{field: value}))

    assert [issue.field for issue in captured.value.issues] == [field]


def test_all_field_issues_are_returned_in_deterministic_order() -> None:
    metadata = RawInvoiceMetadata(" ", " ", "bad", "bad", "bad")

    with pytest.raises(InvoiceMetadataError) as captured:
        validate_invoice_metadata(metadata)

    assert [issue.field for issue in captured.value.issues] == [
        "supplier_name",
        "invoice_number",
        "issue_date",
        "amount",
        "currency",
    ]
