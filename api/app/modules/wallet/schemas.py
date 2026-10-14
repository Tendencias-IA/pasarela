"""Entrada y salida de la API del módulo wallet (api-design.md)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, field_validator

from app.common.money import AMOUNT_FORMAT_MESSAGE, parse_amount, to_json
from app.common.schemas import StrictInput
from app.modules.wallet.service import RechargeResult, WalletBalance


class RechargeIn(StrictInput):
    amount: str

    @field_validator("amount", mode="before")
    @classmethod
    def _amount_is_decimal_string(cls, value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError(AMOUNT_FORMAT_MESSAGE)
        parse_amount(value)
        return value

    @property
    def amount_decimal(self) -> Decimal:
        return parse_amount(self.amount)


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


class WalletOut(BaseModel):
    balance: str

    @classmethod
    def from_balance(cls, result: WalletBalance) -> WalletOut:
        return cls(balance=to_json(result.balance))
