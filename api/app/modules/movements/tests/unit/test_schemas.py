"""Validación de la query del historial (HU-09 CA-6, FR-009)."""

from __future__ import annotations

from datetime import date

import pytest

from app.common.errors import ValidationError
from app.modules.movements.repository import MovementsFilter, MovementType
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


def test_filters_default_to_no_filters() -> None:
    """HU-10 CA-3: sin parámetros, tipo "all" y rango abierto."""
    assert MovementsQuery.parse({}).filters == MovementsFilter()


def test_valid_filters_are_parsed() -> None:
    """HU-10 CA-1, CA-3, CA-4."""
    query = MovementsQuery.parse(
        {"from": "2026-10-01", "to": "2026-10-31", "type": "recharge", "page": "2"}
    )

    assert query.page == 2
    assert query.filters == MovementsFilter(
        from_=date(2026, 10, 1), to=date(2026, 10, 31), type_=MovementType.RECHARGE
    )


@pytest.mark.parametrize("value", ["all", "sent", "received", "recharge"])
def test_every_allowed_type_is_accepted(value: str) -> None:
    """HU-10 CA-3."""
    assert MovementsQuery.parse({"type": value}).filters.type_ == MovementType(value)


def test_only_one_end_of_the_range_is_allowed() -> None:
    """HU-10 CA-1: rango abierto por el otro extremo."""
    only_from = MovementsQuery.parse({"from": "2026-10-01"}).filters
    only_to = MovementsQuery.parse({"to": "2026-10-31"}).filters

    assert (only_from.from_, only_from.to) == (date(2026, 10, 1), None)
    assert (only_to.from_, only_to.to) == (None, date(2026, 10, 31))


@pytest.mark.parametrize("raw", ["2026-13-01", "2026-02-31", "01-10-2026", "hoy", "", "2026-1-1"])
def test_invalid_date_is_a_validation_error_on_that_field(raw: str) -> None:
    """HU-10 CA-1: formato AAAA-MM-DD y fecha existente."""
    for field in ("from", "to"):
        with pytest.raises(ValidationError) as excinfo:
            MovementsQuery.parse({field: raw})

        assert excinfo.value.errors == [
            {"field": field, "message": "La fecha debe tener el formato AAAA-MM-DD."}
        ]


@pytest.mark.parametrize("raw", ["foo", "ALL", "", "sent;drop"])
def test_unknown_type_is_a_validation_error(raw: str) -> None:
    """HU-10 CA-3: lista blanca."""
    with pytest.raises(ValidationError) as excinfo:
        MovementsQuery.parse({"type": raw})

    assert excinfo.value.errors == [
        {"field": "type", "message": "El tipo debe ser all, sent, received o recharge."}
    ]


def test_all_invalid_fields_are_reported_at_once() -> None:
    """RNF-03.2: todos los campos inválidos a la vez."""
    with pytest.raises(ValidationError) as excinfo:
        MovementsQuery.parse({"page": "0", "from": "x", "to": "y", "type": "z"})

    assert [e["field"] for e in excinfo.value.errors] == ["page", "from", "to", "type"]


def test_reversed_range_is_not_a_schema_error() -> None:
    """HU-10 CA-2 lo decide el servicio (invalid_date_range), no el schema."""
    query = MovementsQuery.parse({"from": "2026-12-31", "to": "2026-01-01"})

    assert query.filters.from_ > query.filters.to  # type: ignore[operator]
