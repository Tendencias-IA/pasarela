"""Modelo `users` del módulo accounts.

Alcance de HU-02: solo los campos que `auth` necesita para verificar credenciales.
HU-01 extiende esta tabla con full_name, national_id y email (ver
specs/001-ppa-2-iniciar-sesion/research.md).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class User(db.Model):  # type: ignore[name-defined,misc]
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    phone: Mapped[str] = mapped_column(db.String(10), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(db.String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
