"""Rutas del módulo wallet: solo parsean, delegan al servicio y serializan."""

from __future__ import annotations

from flask import Blueprint, Response, g, jsonify, request

from app.common.auth import current_user_id, login_required
from app.common.idempotency import idempotent, replay_lost_race
from app.common.idempotency_store import DuplicateIdempotencyKeyError
from app.modules.wallet import service
from app.modules.wallet.schemas import RechargeIn, RechargeOut, WalletOut

bp = Blueprint("wallet", __name__)


@bp.get("", strict_slashes=False)
@login_required
def get_wallet() -> tuple[Response, int]:
    user_id = current_user_id()  # nunca de la query (HU-05 CA-4, security.md)
    result = service.get_balance(user_id)
    return jsonify(WalletOut.from_balance(result).model_dump()), 200


@bp.post("/recharges")
@login_required
@idempotent
def create_recharge() -> Response | tuple[Response, int]:
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
    except DuplicateIdempotencyKeyError as error:
        return replay_lost_race(user_id, g.idempotency.key, error)
    return jsonify(RechargeOut.from_result(result).model_dump()), 201
