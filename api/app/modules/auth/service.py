"""Reglas de negocio de auth: iniciar y cerrar sesión, resolver el usuario actual.

HU-02 CA-2/CA-3: teléfono inexistente y contraseña incorrecta deben ser
indistinguibles para quien llama, tanto en el error como en el tiempo de respuesta.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta

from flask import current_app

from app.common.clock import utcnow
from app.common.errors import AppError
from app.common.passwords import hash_password, verify_password
from app.extensions import transaction
from app.modules.accounts import service as accounts_service
from app.modules.auth import repository
from app.modules.auth.models import Session

log = logging.getLogger("app.auth")

# HU-04: no se escribe en cada petición; con actividad hace menos de 10 s no se reescribe.
TOUCH_THRESHOLD = timedelta(seconds=10)

# Hash señuelo constante: se verifica siempre, exista o no el teléfono, para que el
# tiempo de respuesta no revele cuál credencial falló (RNF-01.5).
_DECOY_PASSWORD_HASH = hash_password(secrets.token_urlsafe(16))


class InvalidCredentialsError(AppError):
    status = 401
    code = "invalid_credentials"
    title = "Teléfono o contraseña incorrectos"


class InvalidSessionError(AppError):
    status = 401
    code = "invalid_session"
    title = "No hay una sesión válida"


@dataclass(frozen=True)
class LoginResult:
    session: Session
    token: str


def _mask_phone(phone: str) -> str:
    return f"***{phone[-4:]}" if len(phone) >= 4 else "***"


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def login(phone: str, password: str) -> LoginResult:
    # La lectura y la escritura viven en el mismo `with transaction():` (app/extensions.py):
    # SQLAlchemy 2.0 abre una transacción implícita en el primer SELECT (autobegin) y
    # `db.session.begin()` fallaría si ya hay una abierta en la petición.
    with transaction():
        user = accounts_service.get_user_by_phone(phone)

        if user is None:
            verify_password(password, _DECOY_PASSWORD_HASH)
            log.info("auth.login_failed", extra={"phone": _mask_phone(phone)})
            raise InvalidCredentialsError()

        if not verify_password(password, user.password_hash):
            log.info("auth.login_failed", extra={"phone": _mask_phone(phone)})
            raise InvalidCredentialsError()

        token = secrets.token_urlsafe(32)
        expires_at = utcnow() + current_app.config["SESSION_IDLE"]
        user_id = user.id
        session = repository.create_session(user_id, _hash_token(token), expires_at)

    # user_id ya está capturado: tras el commit, SQLAlchemy expira los objetos del
    # bloque y leer un atributo de `user`/`session` aquí reabriría una transacción.
    log.info("auth.login_ok", extra={"user_id": user_id})
    return LoginResult(session=session, token=token)


def get_current_session(token: str | None) -> Session | None:
    if not token:
        return None

    token_hash = _hash_token(token)
    session = repository.get_by_token_hash(token_hash)
    if session is None:
        return None
    if not hmac.compare_digest(session.token_hash, token_hash):
        return None
    if session.revoked_at is not None:
        return None
    now = utcnow()
    if session.expires_at <= now:
        _revoke_expired(session, now)
        return None
    return session


def _revoke_expired(session: Session, now: datetime) -> None:
    """Limpieza perezosa (HU-04 CA-1): la sesión vencida queda revocada, sin cron."""
    user_id = session.user_id
    with transaction():
        session.revoked_at = now
    log.info("auth.session_expired", extra={"user_id": user_id})


def touch_session(session: Session) -> datetime:
    """Reinicia el periodo de inactividad y devuelve el nuevo vencimiento (HU-04 CA-4).

    La actividad válida extiende `expires_at` a ahora + SESSION_IDLE. Si la última
    actividad fue hace menos de TOUCH_THRESHOLD no escribe (menos carga en MySQL); una
    `last_activity_at` en el futuro (reloj adelantado) sí fuerza la escritura.
    """
    now = utcnow()
    elapsed = now - session.last_activity_at
    if timedelta(0) <= elapsed < TOUCH_THRESHOLD:
        current: datetime = session.expires_at
        return current
    expires_at: datetime = now + current_app.config["SESSION_IDLE"]
    with transaction():
        session.last_activity_at = now
        session.expires_at = expires_at
    return expires_at
