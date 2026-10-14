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
from datetime import UTC, datetime

from flask import current_app

from app.common.errors import AppError
from app.common.passwords import hash_password, verify_password
from app.extensions import db
from app.modules.accounts import service as accounts_service
from app.modules.auth import repository
from app.modules.auth.models import Session

log = logging.getLogger("app.auth")

# Hash señuelo constante: se verifica siempre, exista o no el teléfono, para que el
# tiempo de respuesta no revele cuál credencial falló (RNF-01.5).
_DECOY_PASSWORD_HASH = hash_password(secrets.token_urlsafe(16))


class InvalidCredentialsError(AppError):
    status = 401
    code = "invalid_credentials"
    title = "Teléfono o contraseña incorrectos"


class InvalidSessionError(AppError):
    status = 401
    code = "unauthenticated"
    title = "No hay una sesión válida"


@dataclass(frozen=True)
class LoginResult:
    session: Session
    token: str


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _mask_phone(phone: str) -> str:
    return f"***{phone[-4:]}" if len(phone) >= 4 else "***"


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def login(phone: str, password: str) -> LoginResult:
    # La lectura y la escritura viven en el mismo `with db.session.begin():`: SQLAlchemy
    # 2.0 abre una transacción implícita en el primer SELECT (autobegin), así que un
    # `begin()` posterior a una lectura suelta falla con "ya hay una transacción abierta".
    with db.session.begin():
        user = accounts_service.get_user_by_phone(phone)

        if user is None:
            verify_password(password, _DECOY_PASSWORD_HASH)
            log.info("auth.login_failed", extra={"phone": _mask_phone(phone)})
            raise InvalidCredentialsError()

        if not verify_password(password, user.password_hash):
            log.info("auth.login_failed", extra={"phone": _mask_phone(phone)})
            raise InvalidCredentialsError()

        token = secrets.token_urlsafe(32)
        expires_at = _utcnow() + current_app.config["SESSION_IDLE"]
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
    if session.expires_at <= _utcnow():
        return None
    return session
