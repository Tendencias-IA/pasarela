"""Reglas de negocio de accounts. Único punto de entrada que otros módulos pueden
importar (nunca su repository.py ni sus models.py, ver architecture.md)."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from app.modules.accounts import repository
from app.modules.accounts.models import User


def get_user_by_phone(phone: str) -> User | None:
    return repository.get_by_phone(phone)


@dataclass(frozen=True)
class UserSummary:
    """Datos de un usuario que otros módulos pueden conocer (HU-09 CA-3, HU-06 CA-7)."""

    id: int
    phone: str
    full_name: str | None


def get_users_by_ids(user_ids: Iterable[int]) -> dict[int, UserSummary]:
    """Resumen por id; los ids inexistentes se omiten. Quien lo consume enmascara.

    `full_name` queda en None hasta que HU-01 añada la columna a `users`; entonces basta
    con leer `user.full_name` aquí.
    """
    return {
        user.id: UserSummary(id=user.id, phone=user.phone, full_name=None)
        for user in repository.get_by_ids(user_ids)
    }
