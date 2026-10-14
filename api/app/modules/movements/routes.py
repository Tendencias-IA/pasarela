"""Rutas del módulo movements: solo parsean, delegan al servicio y serializan."""

from __future__ import annotations

from flask import Blueprint, Response, jsonify, request

from app.common.auth import current_user_id, login_required
from app.modules.movements import service
from app.modules.movements.schemas import MovementsPageOut, MovementsQuery

bp = Blueprint("movements", __name__)


@bp.get("", strict_slashes=False)
@login_required
def list_movements() -> tuple[Response, int]:
    user_id = current_user_id()  # nunca de la query (security.md, HU-09 CA-5)
    query = MovementsQuery.parse(request.args)
    page = service.list_movements(user_id, query.page, query.filters)
    return jsonify(MovementsPageOut.from_page(page).model_dump()), 200
