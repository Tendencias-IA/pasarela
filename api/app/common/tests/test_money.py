"""Dinero con decimal exacto (RNF-04.3, FR-013)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.common.money import (
    RECHARGE_MAX,
    RECHARGE_MIN,
    TRANSFER_MAX,
    TRANSFER_MIN,
    parse_amount,
    quantize,
    to_json,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("50000", "50000.00"),
        ("50000.5", "50000.50"),
        ("50000.50", "50000.50"),
        (" 5000 ", "5000.00"),
    ],
)
def test_parse_amount_accepts_valid_strings(raw: str, expected: str) -> None:
    assert parse_amount(raw) == Decimal(expected)


@pytest.mark.parametrize(
    "raw",
    ["", "abc", "-1", "+5", "1.234", "NaN", "Infinity", "1e3", "0", "0.00", "1234567890123456"],
)
def test_parse_amount_rejects_invalid_strings(raw: str) -> None:
    with pytest.raises(ValueError, match="hasta dos decimales"):
        parse_amount(raw)


@pytest.mark.parametrize("raw", [50000, 50000.0, None, ["5000"]])
def test_parse_amount_rejects_non_strings(raw: object) -> None:
    with pytest.raises(ValueError):
        parse_amount(raw)


def test_quantize_rounds_half_up_to_two_places() -> None:
    assert quantize(Decimal("1.005")) == Decimal("1.01")
    assert quantize(Decimal("1.004")) == Decimal("1.00")


def test_to_json_always_has_two_decimals() -> None:
    assert to_json(Decimal("5000")) == "5000.00"
    assert to_json(Decimal("120500.5")) == "120500.50"


def test_business_limits_match_requirements() -> None:
    assert (Decimal("5000.00"), Decimal("5000000.00")) == (RECHARGE_MIN, RECHARGE_MAX)
    assert (Decimal("100.00"), Decimal("3000000.00")) == (TRANSFER_MIN, TRANSFER_MAX)
