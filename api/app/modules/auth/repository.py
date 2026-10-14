"""Consultas SQLAlchemy del módulo auth. Sin commit: lo abre el servicio."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from app.extensions import db
from app.modules.auth.models import Session


def create_session(user_id: int, token_hash: str, expires_at: datetime) -> Session:
    session = Session(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
    db.session.add(session)
    return session


def get_by_token_hash(token_hash: str) -> Session | None:
    return db.session.execute(
        select(Session).where(Session.token_hash == token_hash)
    ).scalar_one_or_none()
