"""Validación de entrada de la transferencia (HU-06 CA-3, CA-4, RNF-01.4)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.common.errors import ValidationError
from app.modules.transfers.schemas import TransferIn


def test_valid_payload_is_parsed() -> None:
    payload = TransferIn.parse({"recipient_phone": "3001234567", "amount": "100"})

    assert payload.recipient_phone == "3001234567"
    assert payload.amount_decimal == Decimal("100.00")


@pytest.mark.parametrize(
    "phone", ["123", "4001234567", "300123456a", "30012345678", "", 3001234567]
)
def test_invalid_phone_is_rejected_on_its_field(phone: object) -> None:
    """HU-06 CA-4."""
    with pytest.raises(ValidationError) as excinfo:
        TransferIn.parse({"recipient_phone": phone, "amount": "1000"})

    assert [e["field"] for e in excinfo.value.errors] == ["recipient_phone"]


@pytest.mark.parametrize("amount", ["", "abc", "-5", "1.234", 1000, None])
def test_invalid_amount_is_rejected_on_its_field(amount: object) -> None:
    """HU-06 CA-3."""
    with pytest.raises(ValidationError) as excinfo:
        TransferIn.parse({"recipient_phone": "3001234567", "amount": amount})

    assert [e["field"] for e in excinfo.value.errors] == ["amount"]


def test_both_fields_invalid_are_reported_together() -> None:
    """RNF-03.2."""
    with pytest.raises(ValidationError) as excinfo:
        TransferIn.parse({"recipient_phone": "12", "amount": "abc"})

    assert {e["field"] for e in excinfo.value.errors} == {"recipient_phone", "amount"}


def test_sender_fields_are_not_allowed() -> None:
    """RNF-01.4: el emisor sale de la sesión."""
    with pytest.raises(ValidationError) as excinfo:
        TransferIn.parse({"recipient_phone": "3001234567", "amount": "1000", "sender_wallet_id": 2})

    assert excinfo.value.errors == [{"field": "sender_wallet_id", "message": "Campo no permitido."}]
