"""Entrada y salida de la API del módulo transfers (api-design.md)."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, field_validator

from app.common.money import AMOUNT_FORMAT_MESSAGE, parse_amount
from app.common.schemas import StrictInput
from app.modules.transfers.service import TransferPreview, TransferResult

PHONE_PATTERN = re.compile(r"3\d{9}", re.ASCII)
PHONE_MESSAGE = "Debe ser un celular de diez dígitos que empiece por 3."


class TransferIn(StrictInput):
    recipient_phone: str
    amount: str

    @field_validator("recipient_phone", mode="before")
    @classmethod
    def _phone_is_a_colombian_mobile(cls, value: Any) -> str:
        if not isinstance(value, str) or PHONE_PATTERN.fullmatch(value) is None:
            raise ValueError(PHONE_MESSAGE)
        return value

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


class RecipientMaskedOut(BaseModel):
    name_masked: str | None
    phone_masked: str


class TransferPreviewOut(BaseModel):
    amount: str
    recipient: RecipientMaskedOut
    balance_after: str

    @classmethod
    def from_result(cls, result: TransferPreview) -> TransferPreviewOut:
        return cls.model_validate(result.to_body())


class TransferOut(BaseModel):
    id: int
    type: str
    status: str
    amount: str
    recipient: RecipientMaskedOut
    balance_after: str
    created_at: str

    @classmethod
    def from_result(cls, result: TransferResult) -> TransferOut:
        return cls.model_validate(result.to_body())
