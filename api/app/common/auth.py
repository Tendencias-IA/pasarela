"""Decorador @login_required y acceso al usuario/sesión actuales (RNF-01.1).

Cookie de sesión server-side (HU-02); revocada o expirada se tratan igual: sin sesión.
`current_user_id()` es lo que usan los módulos de negocio; cachea el id en `g.user_id`
para no consultar la sesión dos veces en la misma petición, y las pruebas unitarias
pueden fijar `g.user_id` directamente para simular la capa de sesión.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps

from flask import g, request

from app.extensions import db
from app.modules.accounts.models import User
from app.modules.auth.models import Session
from app.modules.auth.service import InvalidSessionError, get_current_session

SESSION_COOKIE_NAME = "session"


def current_session() -> Session | None:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    return get_current_session(token)


def current_user() -> User | None:
    session = current_session()
    if session is None:
        return None
    return db.session.get(User, session.user_id)


def current_user_id() -> int:
    """Id del usuario autenticado; lanza `InvalidSessionError` (401) si no hay sesión."""
    cached = getattr(g, "user_id", None)
    if isinstance(cached, int):
        return cached
    session = current_session()
    if session is None:
        raise InvalidSessionError("Inicia sesión para continuar.")
    g.user_id = session.user_id
    return session.user_id


def login_required[**P, R](view: Callable[P, R]) -> Callable[P, R]:
    @wraps(view)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
        current_user_id()
        return view(*args, **kwargs)

    return wrapped


__all__ = [
    "SESSION_COOKIE_NAME",
    "current_session",
    "current_user",
    "current_user_id",
    "login_required",
]
