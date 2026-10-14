"""Consultas SQLAlchemy del módulo auth. Sin commit: lo abre el servicio."""

from __future__ import annotations

from datetime import datetime
from typing import Any, cast

from sqlalchemy import select, update
from sqlalchemy.engine import CursorResult

from app.common.clock import utcnow
from app.extensions import db
from app.modules.auth.models import Session


def create_session(user_id: int, token_hash: str, expires_at: datetime) -> Session:
    # last_activity_at con el reloj de Python (UTC), igual que expires_at: nunca now() de MySQL.
    session = Session(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        last_activity_at=utcnow(),
    )
    db.session.add(session)
    return session


def get_by_token_hash(token_hash: str) -> Session | None:
    return db.session.execute(
        select(Session).where(Session.token_hash == token_hash)
    ).scalar_one_or_none()


def revoke_session(session_id: int, now: datetime) -> bool:
    """HU-03 CA-1: escritura condicional, sin tocar otras sesiones."""
    result = cast(
        CursorResult[Any],
        db.session.execute(
            update(Session)
            .where(Session.id == session_id, Session.revoked_at.is_(None))
            .values(revoked_at=now)
        ),
    )
    return bool(result.rowcount == 1)
