"""Blueprint de auth: POST /api/v1/auth/login (HU-02).

Contrato fijo en .claude/rules/api-design.md: éxito es 204 + cookie, sin cuerpo.
"""

from __future__ import annotations

from flask import Blueprint, Response, current_app, g, jsonify, request
from flask_limiter.util import get_remote_address

from app.common.auth import (
    SESSION_COOKIE_NAME,
    current_session_expires_at,
    current_user_id,
    login_required,
)
from app.extensions import limiter
from app.modules.auth import service
from app.modules.auth.schemas import LoginIn, SessionOut

bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


def _login_phone_key() -> str:
    body = request.get_json(silent=True) or {}
    return str(body.get("phone", get_remote_address()))


@bp.post("/login")
@limiter.limit("5 per 15 minutes", key_func=_login_phone_key)
@limiter.limit("20 per 15 minutes", key_func=get_remote_address)
def login() -> Response:
    payload = LoginIn.model_validate(request.get_json())
    result = service.login(payload.phone, payload.password)

    response = current_app.make_response(("", 204))
    response.set_cookie(
        "session",
        result.token,
        httponly=True,
        samesite="Lax",
        secure=current_app.config["SESSION_COOKIE_SECURE"],
        max_age=int(current_app.config["SESSION_IDLE"].total_seconds()),
    )
    return response


@bp.get("/session")
@login_required
def get_session() -> tuple[Response, int]:
    """Vencimiento vigente de la sesión (HU-04). Consultarlo cuenta como actividad."""
    current_user_id()
    expires_at = current_session_expires_at().replace(microsecond=0).isoformat() + "Z"
    return jsonify(SessionOut(expires_at=expires_at).model_dump()), 200


@bp.after_app_request
def renew_session_cookie(response: Response) -> Response:
    """HU-04 CA-4: la cookie se renueva junto con la sesión del servidor.

    Sin esto la cookie caducaría a los 5 minutos del login aunque el usuario siga activo.
    Solo se renueva si esta petición tocó una sesión válida (`g.session_expires_at`).
    """
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token and getattr(g, "session_expires_at", None) is not None:
        response.set_cookie(
            SESSION_COOKIE_NAME,
            token,
            httponly=True,
            samesite="Lax",
            secure=current_app.config["SESSION_COOKIE_SECURE"],
            max_age=int(current_app.config["SESSION_IDLE"].total_seconds()),
        )
    return response


@bp.post("/logout")
@login_required
def logout() -> Response:
    service.logout(request.cookies.get(SESSION_COOKIE_NAME))
    # HU-04 renueva la cookie en cada respuesta con sesión válida; aquí la sesión acaba de
    # revocarse y la cookie debe quedar borrada (HU-03 CA-1), no renovada.
    g.pop("session_expires_at", None)
    response = current_app.make_response(("", 204))
    response.delete_cookie(
        SESSION_COOKIE_NAME,
        httponly=True,
        samesite="Lax",
        secure=current_app.config["SESSION_COOKIE_SECURE"],
    )
    return response
