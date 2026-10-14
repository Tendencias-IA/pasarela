"""Rutas del módulo wallet: solo parsean, delegan al servicio y serializan."""

from __future__ import annotations

from typing import Any

from flask import Blueprint, Response, g, jsonify, request

from app.common.auth import current_user_id, login_required
from app.common.idempotency import find_existing, idempotent
from app.modules.wallet import service
from app.modules.wallet.schemas import RechargeIn, RechargeOut

bp = Blueprint("wallet", __name__)


@bp.post("/recharges")
@login_required
@idempotent
def create_recharge() -> tuple[Response, int]:
    user_id = current_user_id()  # nunca del cuerpo ni de la URL (security.md)
    payload = RechargeIn.parse(request.get_json(silent=True))
    try:
        result = service.recharge(
            user_id,
            payload.amount_decimal,
            g.idempotency,
            instance=request.path,
            request_id=getattr(g, "request_id", None),
        )
    except service.DuplicateIdempotencyKeyError:
        stored = find_existing(user_id, g.idempotency.key)
        if stored is None:
            raise
        body: dict[str, Any] = stored.body
        response = jsonify(body)
        response.status_code = stored.status_code
        response.headers["Idempotent-Replayed"] = "true"
        return response, stored.status_code
    return jsonify(RechargeOut.from_result(result).model_dump()), 201
