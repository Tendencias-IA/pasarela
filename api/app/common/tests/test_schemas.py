"""Base de schemas de entrada: errores por campo, todos a la vez (RNF-03.2, RNF-01.4)."""

from __future__ import annotations

import pytest
from pydantic import field_validator

from app.common.errors import ValidationError
from app.common.schemas import StrictInput


class Sample(StrictInput):
    a: str
    b: str

    @field_validator("b")
    @classmethod
    def _b_is_ok(cls, value: str) -> str:
        if value != "ok":
            raise ValueError("b debe ser ok")
        return value


def test_parse_valid_payload_returns_model() -> None:
    assert Sample.parse({"a": "x", "b": "ok"}).a == "x"


def test_parse_reports_missing_invalid_and_extra_fields_at_once() -> None:
    with pytest.raises(ValidationError) as excinfo:
        Sample.parse({"b": "no", "extra": 1})

    messages = {e["field"]: e["message"] for e in excinfo.value.errors}
    assert messages == {
        "a": "Campo obligatorio.",
        "b": "b debe ser ok",
        "extra": "Campo no permitido.",
    }


def test_parse_none_is_treated_as_empty_body() -> None:
    with pytest.raises(ValidationError) as excinfo:
        Sample.parse(None)

    assert {e["field"] for e in excinfo.value.errors} == {"a", "b"}


def test_parse_wrong_type_has_generic_message() -> None:
    with pytest.raises(ValidationError) as excinfo:
        Sample.parse({"a": 5, "b": "ok"})

    assert excinfo.value.errors == [{"field": "a", "message": "Valor inválido."}]
