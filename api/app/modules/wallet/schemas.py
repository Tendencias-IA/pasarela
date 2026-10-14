"""Entrada y salida de la API del módulo wallet (api-design.md)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    field_validator,
)
from pydantic import (
    ValidationError as PydanticValidationError,
)
from pydantic_core import ErrorDetails

from app.common.errors import ValidationError
from app.common.money import parse_amount, to_json
from app.modules.wallet.service import BalanceResult, RechargeResult


class RechargeIn(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    amount: str

    @field_validator("amount")
    @classmethod
    def _amount_is_decimal_string(cls, value: str) -> str:
        parse_amount(value)
        return value

    @property
    def amount_decimal(self) -> Decimal:
        return parse_amount(self.amount)

    @classmethod
    def parse(cls, payload: Any) -> RechargeIn:
        """Convierte errores de Pydantic al formato RFC 9457 con `errors[]` por campo."""
        try:
            return cls.model_validate(payload if payload is not None else {})
        except PydanticValidationError as exc:
            errors = [
                {"field": ".".join(str(p) for p in e["loc"]) or "body", "message": _message(e)}
                for e in exc.errors()
            ]
            raise ValidationError("Revisa los campos indicados.", errors=errors) from None


def _message(error: ErrorDetails) -> str:
    ctx = error.get("ctx") or {}
    raw = ctx.get("error")
    if isinstance(raw, ValueError):
        return str(raw)
    if error.get("type") == "extra_forbidden":
        return "Campo no permitido."
    if error.get("type", "").endswith("missing"):
        return "Campo obligatorio."
    return "El monto debe ser un número positivo con hasta dos decimales."


class RechargeOut(BaseModel):
    id: int
    type: str
    status: str
    amount: str
    balance_after: str
    created_at: str

    @classmethod
    def from_result(cls, result: RechargeResult) -> RechargeOut:
        return cls.model_validate(result.to_body())


class BalanceOut(BaseModel):
    balance: str

    @classmethod
    def from_result(cls, result: BalanceResult) -> BalanceOut:
        return cls.model_validate({"balance": to_json(result.balance)})
