from datetime import date
from decimal import Decimal

import pytest

from app.domain.purchase_request import PurchaseRequestValidationError, RawPurchaseRequest, validate_purchase_request


def valid(**changes):
    data = dict(requester_name="Alex Morgan", department="Operations", item_or_service="Office chairs", supplier="Supply Co", amount="1200.50", currency="EUR", business_justification="Replace unsafe and damaged office seating.", required_date="2026-09-01")
    data.update(changes)
    return RawPurchaseRequest(**data)


def test_valid_request_is_normalized():
    value = validate_purchase_request(valid(requester_name=" Alex Morgan "), submitted_on=date(2026, 8, 21))
    assert value.requester_name == "Alex Morgan"
    assert value.amount == Decimal("1200.50")


@pytest.mark.parametrize("field,value", [
    ("requester_name", " "), ("department", ""), ("item_or_service", " "),
    ("supplier", ""), ("amount", "0"), ("amount", "1.234"),
    ("currency", "eur"), ("business_justification", "too short"),
    ("required_date", "2026-02-30"), ("required_date", "2026-08-20"),
])
def test_invalid_business_field_is_reported(field, value):
    with pytest.raises(PurchaseRequestValidationError) as exc:
        validate_purchase_request(valid(**{field: value}), submitted_on=date(2026, 8, 21))
    assert field in {issue.field for issue in exc.value.issues}
