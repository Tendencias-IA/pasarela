"""Decorador @login_required y acceso al usuario/sesión actuales.

Cookie de sesión server-side; revocada o expirada se tratan igual: sin sesión
(FR-005 de HU-02). Ver .claude/rules/security.md.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps

from flask import request

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


def login_required[**P, R](view: Callable[P, R]) -> Callable[P, R]:
    @wraps(view)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
        if current_session() is None:
            raise InvalidSessionError()
        return view(*args, **kwargs)

    return wrapped


__all__ = ["SESSION_COOKIE_NAME", "current_session", "current_user", "login_required"]
