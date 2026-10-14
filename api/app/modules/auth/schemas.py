"""Schemas Pydantic de entrada/salida de auth."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class LoginIn(BaseModel):
    phone: str
    password: str = Field(min_length=8)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        if not (len(value) == 10 and value.isdigit() and value.startswith("3")):
            msg = "El teléfono debe tener 10 dígitos y empezar por 3."
            raise ValueError(msg)
        return value


class LoginOut(BaseModel):
    user_id: int


class SessionOut(BaseModel):
    expires_at: str
