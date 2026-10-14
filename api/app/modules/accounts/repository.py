"""Consultas SQLAlchemy del módulo accounts. Sin commit: lo abre el servicio."""

from __future__ import annotations

from sqlalchemy import select

from app.extensions import db
from app.modules.accounts.models import User


def get_by_phone(phone: str) -> User | None:
    return db.session.execute(select(User).where(User.phone == phone)).scalar_one_or_none()
