"""HU-12/HU-13: perfil propio y datos de contacto, identidad desde sesión."""

from dataclasses import asdict

from flask import Blueprint, Response, jsonify, request

from app.common.auth import current_user_id, login_required
from app.modules.accounts import service
from app.modules.accounts.schemas import UpdateEmailIn, UpdatePhoneIn

bp = Blueprint("profile", __name__, url_prefix="/api/v1/profile")


@bp.get("")
@login_required
def get_profile() -> Response:
    return jsonify(asdict(service.get_profile(current_user_id())))


@bp.patch("")
@login_required
def update_profile() -> Response:
    body = request.get_json()
    if isinstance(body, dict) and "email" in body:
        email = UpdateEmailIn.model_validate(body)
        result = service.update_email(current_user_id(), email.email)
    else:
        phone = UpdatePhoneIn.model_validate(body)
        result = service.update_phone(current_user_id(), phone.phone)
    return jsonify(asdict(result))
