"""Reglas de negocio de accounts. Único punto de entrada que otros módulos pueden
importar (nunca su repository.py ni sus models.py, ver architecture.md)."""

from __future__ import annotations

from app.modules.accounts import repository
from app.modules.accounts.models import User


def get_user_by_phone(phone: str) -> User | None:
    return repository.get_by_phone(phone)
