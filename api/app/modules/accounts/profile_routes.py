"""HU-12: consulta y actualización del perfil propio, identidad desde sesión."""

from dataclasses import asdict

from flask import Blueprint, Response, jsonify, request

from app.common.auth import current_user_id, login_required
from app.modules.accounts import service
from app.modules.accounts.schemas import UpdatePhoneIn

bp = Blueprint("profile", __name__, url_prefix="/api/v1/profile")


@bp.get("")
@login_required
def get_profile() -> Response:
    return jsonify(asdict(service.get_profile(current_user_id())))


@bp.patch("")
@login_required
def update_phone() -> Response:
    payload = UpdatePhoneIn.model_validate(request.get_json())
    return jsonify(asdict(service.update_phone(current_user_id(), payload.phone)))
