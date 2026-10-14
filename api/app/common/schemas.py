"""Base de los schemas de entrada: estrictos y con errores por campo (api.md, RNF-03.2)."""

from __future__ import annotations

from typing import Any, Self

from pydantic import BaseModel, ConfigDict
from pydantic import ValidationError as PydanticValidationError
from pydantic_core import ErrorDetails

from app.common.errors import ValidationError


class StrictInput(BaseModel):
    """Entrada sin campos extra ni coerción de tipos (un número JSON no es una cadena)."""

    model_config = ConfigDict(extra="forbid", strict=True)

    @classmethod
    def parse(cls, payload: Any) -> Self:
        """Valida el cuerpo y reporta todos los campos inválidos a la vez como RFC 9457."""
        try:
            return cls.model_validate(payload if payload is not None else {})
        except PydanticValidationError as exc:
            errors = [
                {"field": ".".join(str(p) for p in e["loc"]) or "body", "message": _message(e)}
                for e in exc.errors()
            ]
            raise ValidationError("Revisa los campos indicados.", errors=errors) from None


def _message(error: ErrorDetails) -> str:
    raw = (error.get("ctx") or {}).get("error")
    if isinstance(raw, ValueError):
        return str(raw)
    kind = error.get("type", "")
    if kind == "extra_forbidden":
        return "Campo no permitido."
    if kind.endswith("missing"):
        return "Campo obligatorio."
    return "Valor inválido."
