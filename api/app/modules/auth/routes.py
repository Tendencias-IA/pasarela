"""Blueprint de auth: POST /api/v1/auth/login (HU-02).

Contrato fijo en .claude/rules/api-design.md: éxito es 204 + cookie, sin cuerpo.
"""

from __future__ import annotations

from flask import Blueprint, Response, current_app, jsonify, request
from flask_limiter.util import get_remote_address

from app.common.auth import SESSION_COOKIE_NAME, login_required
from app.extensions import limiter
from app.modules.auth import service
from app.modules.auth.schemas import LoginIn

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


@bp.post("/logout")
@login_required
def logout() -> Response:
    service.logout(request.cookies.get(SESSION_COOKIE_NAME))
    response = current_app.make_response(("", 204))
    response.delete_cookie(
        SESSION_COOKIE_NAME,
        httponly=True,
        samesite="Lax",
        secure=current_app.config["SESSION_COOKIE_SECURE"],
    )
    return response


@bp.get("/session")
@login_required
def session_status() -> Response:
    return jsonify(expires_at=service.session_expiry(request.cookies.get(SESSION_COOKIE_NAME)))
