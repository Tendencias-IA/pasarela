"""Validación de entrada de la recarga (HU-08 CA-2, FR-003, RNF-01.4)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.common.errors import ValidationError
from app.modules.wallet.schemas import RechargeIn


def test_valid_amount_string_is_parsed_to_decimal() -> None:
    payload = RechargeIn.parse({"amount": "5000"})

    assert payload.amount_decimal == Decimal("5000.00")


@pytest.mark.parametrize("raw", ["", "abc", "-5", "1.234", 50000, 50000.0, None])
def test_invalid_amounts_are_rejected_with_field_error(raw: object) -> None:
    with pytest.raises(ValidationError) as excinfo:
        RechargeIn.parse({"amount": raw})

    assert excinfo.value.errors[0]["field"] == "amount"
    assert excinfo.value.errors[0]["message"]


def test_extra_fields_such_as_user_id_are_forbidden() -> None:
    with pytest.raises(ValidationError) as excinfo:
        RechargeIn.parse({"amount": "5000.00", "user_id": 2})

    assert {e["field"] for e in excinfo.value.errors} == {"user_id"}


def test_missing_body_reports_amount_as_required() -> None:
    with pytest.raises(ValidationError) as excinfo:
        RechargeIn.parse(None)

    assert excinfo.value.errors[0]["field"] == "amount"
    assert excinfo.value.errors[0]["message"] == "Campo obligatorio."
