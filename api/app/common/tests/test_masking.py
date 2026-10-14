"""Enmascaramiento de datos de terceros en servidor (HU-09 CA-3, RNF-06.1)."""

from __future__ import annotations

import pytest

from app.common.masking import mask_name, mask_phone


@pytest.mark.parametrize(
    ("phone", "expected"),
    [("3001234567", "***4567"), ("4567", "***4567"), ("12", "***"), ("", "***")],
)
def test_mask_phone_keeps_only_last_four_digits(phone: str, expected: str) -> None:
    """HU-09 CA-3: el teléfono del otro participante sale parcialmente oculto."""
    assert mask_phone(phone) == expected


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Maria Garcia", "Mar** G*****"),
        ("Ana", "Ana"),
        ("Jose Luis Perez", "Jos* L*** P****"),
        ("  Maria   Garcia  ", "Mar** G*****"),
        ("", "***"),
        (None, "***"),
    ],
)
def test_mask_name_shows_initials_only(name: str | None, expected: str) -> None:
    """HU-09 CA-3, RNF-06.1: el nombre nunca viaja completo al navegador."""
    assert mask_name(name) == expected
