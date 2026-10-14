"""Factories de datos ficticios para pruebas (RNF-06.3: nunca datos reales)."""

from __future__ import annotations

import itertools
from dataclasses import dataclass

from app.common.passwords import hash_password
from app.modules.accounts.models import User

_phone_sequence = itertools.count(3_000_000_000)


def make_phone() -> str:
    return str(next(_phone_sequence))


@dataclass(frozen=True)
class SeededUser:
    """Usuario ya persistido junto con sus datos en claro, capturados antes del commit.

    Leer un atributo del `User` después de un `commit()` dispara una recarga perezosa
    que abre una transacción nueva (ver conftest.py#db_session); por eso las pruebas
    usan `seeded.phone`/`seeded.password`, no `seeded.user.phone`.
    """

    user: User
    phone: str
    password: str


def make_user(phone: str | None = None, password: str = "Clave1234") -> SeededUser:
    phone = phone or make_phone()
    return SeededUser(
        user=User(phone=phone, password_hash=hash_password(password)),
        phone=phone,
        password=password,
    )
