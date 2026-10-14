"""Rutas del módulo transfers: solo parsean, delegan al servicio y serializan."""

from __future__ import annotations

from flask import Blueprint, Response, g, jsonify, request

from app.common.auth import current_user_id, login_required
from app.common.idempotency import find_existing, idempotent, replay_response
from app.modules.transfers import service
from app.modules.transfers.schemas import TransferIn, TransferOut, TransferPreviewOut
from app.modules.wallet.service import DuplicateIdempotencyKeyError

bp = Blueprint("transfers", __name__)


@bp.post("/preview")
@login_required
def preview_transfer() -> tuple[Response, int]:
    user_id = current_user_id()  # nunca del cuerpo ni de la URL (security.md)
    payload = TransferIn.parse(request.get_json(silent=True))
    result = service.preview_transfer(user_id, payload.recipient_phone, payload.amount_decimal)
    return jsonify(TransferPreviewOut.from_result(result).model_dump()), 200


@bp.post("", strict_slashes=False)
@login_required
@idempotent
def create_transfer() -> Response | tuple[Response, int]:
    user_id = current_user_id()  # nunca del cuerpo ni de la URL (security.md)
    payload = TransferIn.parse(request.get_json(silent=True))
    try:
        result = service.confirm_transfer(
            user_id,
            payload.recipient_phone,
            payload.amount_decimal,
            g.idempotency,
            instance=request.path,
            request_id=getattr(g, "request_id", None),
        )
    except DuplicateIdempotencyKeyError:
        # Otra petición con la misma clave ganó la carrera: se reproduce su respuesta.
        stored = find_existing(user_id, g.idempotency.key)
        if stored is None:
            raise
        return replay_response(stored)
    return jsonify(TransferOut.from_result(result).model_dump()), 201
