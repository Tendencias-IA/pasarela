"""Validación de la query del historial (HU-09 CA-6, FR-009)."""

from __future__ import annotations

import pytest

from app.common.errors import ValidationError
from app.modules.movements.schemas import MovementsQuery


def test_page_defaults_to_one() -> None:
    assert MovementsQuery.parse({}).page == 1


def test_page_is_parsed_from_string() -> None:
    assert MovementsQuery.parse({"page": "3"}).page == 3


@pytest.mark.parametrize("raw", ["0", "-1", "abc", "1.5", "", "\u00b2", "\u0663"])
def test_invalid_page_is_a_validation_error_on_field_page(raw: str) -> None:
    with pytest.raises(ValidationError) as excinfo:
        MovementsQuery.parse({"page": raw})

    assert excinfo.value.errors == [
        {"field": "page", "message": "La página debe ser un entero desde 1."}
    ]


def test_future_filter_params_are_ignored_for_now() -> None:
    """HU-10 añadirá from/to/type; hoy no rompen la consulta."""
    assert MovementsQuery.parse({"page": "2", "type": "sent", "from": "2026-01-01"}).page == 2
