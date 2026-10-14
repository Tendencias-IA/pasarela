"""HU-01 request and response schemas."""

import re
import unicodedata
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


class RegisterAccountIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    full_name: str
    phone: str
    national_id: str
    email: str
    password: str

    @field_validator("full_name")
    @classmethod
    def valid_name(cls, value: str) -> str:
        allowed = all(
            unicodedata.category(char).startswith(("L", "M")) or char in " '-" for char in value
        )
        if (
            not 2 <= len(value) <= 100
            or not allowed
            or not value[0].isalpha()
            or not value[-1].isalpha()
        ):
            raise ValueError("Ingresa un nombre válido de 2 a 100 caracteres.")
        return " ".join(value.split())

    @field_validator("phone")
    @classmethod
    def valid_phone(cls, value: str) -> str:
        if not re.fullmatch(r"3[0-9]{9}", value):
            raise ValueError("Ingresa un número móvil colombiano de 10 dígitos.")
        return value

    @field_validator("national_id")
    @classmethod
    def valid_national_id(cls, value: str) -> str:
        canonical = value.upper()
        if not re.fullmatch(r"[A-Z0-9]{5,20}", canonical):
            raise ValueError("Ingresa una identificación alfanumérica de 5 a 20 caracteres.")
        return canonical

    @field_validator("email")
    @classmethod
    def valid_email(cls, value: str) -> str:
        canonical = value.lower()
        if len(canonical) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", canonical):
            raise ValueError("Ingresa un correo electrónico válido.")
        return canonical

    @field_validator("password")
    @classmethod
    def valid_password(cls, value: str) -> str:
        if (
            len(value) < 8
            or not any(char.isalpha() for char in value)
            or not any(char in "0123456789" for char in value)
        ):
            raise ValueError("Usa al menos 8 caracteres, una letra y un número.")
        return value


class RegisterAccountOut(BaseModel):
    account_id: int
    balance: str

    def response_body(self) -> dict[str, Any]:
        return {"account_id": self.account_id, "wallet": {"balance": self.balance}}


class UpdatePhoneIn(BaseModel):
    """HU-12 CA-1: la misma regla de teléfono de HU-01."""

    model_config = ConfigDict(extra="forbid", strict=True)
    phone: str

    @field_validator("phone")
    @classmethod
    def valid_phone(cls, value: str) -> str:
        return RegisterAccountIn.valid_phone(value)
