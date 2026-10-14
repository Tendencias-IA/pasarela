"""Idempotencia por `Idempotency-Key` (ADR-0005).

Capa de ruta: `@idempotent` exige la cabecera, resuelve replay y conflicto y deja
`g.idempotency`. Capa de servicio: el repositorio inserta la fila `idempotency_keys`
dentro de la misma transacción que la operación (éxito) o que el movimiento rechazado.
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from typing import Any

from flask import Response, g, jsonify, request
from sqlalchemy import select

from app.common.auth import current_user_id
from app.common.errors import IdempotencyKeyMismatchError, MissingIdempotencyKeyError
from app.common.models.idempotency_key import IdempotencyKey
from app.extensions import db

log = logging.getLogger("app.idempotency")

REPLAYED_HEADER = "Idempotent-Replayed"


@dataclass(frozen=True)
class IdempotencyContext:
    key: str
    request_hash: str


@dataclass(frozen=True)
class StoredResponse:
    request_hash: str
    status_code: int
    body: dict[str, Any]


def request_hash(method: str, path: str, body: bytes) -> str:
    """SHA-256 de método + ruta + cuerpo JSON canónico (claves ordenadas, sin espacios)."""
    try:
        canonical = json.dumps(json.loads(body or b"null"), sort_keys=True, separators=(",", ":"))
    except ValueError:
        canonical = body.decode("utf-8", errors="replace")
    return hashlib.sha256(f"{method.upper()} {path}\n{canonical}".encode()).hexdigest()


def find_existing(user_id: int, key: str) -> StoredResponse | None:
    row = db.session.execute(
        select(IdempotencyKey).where(IdempotencyKey.user_id == user_id, IdempotencyKey.key == key)
    ).scalar_one_or_none()
    if row is None:
        return None
    return StoredResponse(row.request_hash, row.status_code, row.response_body)


def _replay(stored: StoredResponse) -> Response:
    response = jsonify(stored.body)
    response.status_code = stored.status_code
    if stored.status_code >= 400:
        response.mimetype = "application/problem+json"
    response.headers[REPLAYED_HEADER] = "true"
    return response


def idempotent[**P](view: Callable[P, Any]) -> Callable[P, Any]:
    """Aplica las reglas de replay/conflicto antes de ejecutar la vista."""

    @wraps(view)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
        raw_key = request.headers.get("Idempotency-Key", "").strip()
        try:
            key = str(uuid.UUID(raw_key))
        except ValueError:
            raise MissingIdempotencyKeyError(
                "Envía la cabecera Idempotency-Key con un UUID v4 por intento."
            ) from None
        user_id = current_user_id()
        digest = request_hash(request.method, request.path, request.get_data())
        stored = find_existing(user_id, key)
        if stored is not None:
            if stored.request_hash != digest:
                raise IdempotencyKeyMismatchError(
                    "La Idempotency-Key ya se usó con una solicitud distinta."
                )
            log.info(
                "idempotency.replayed", extra={"user_id": user_id, "status": stored.status_code}
            )
            return _replay(stored)
        g.idempotency = IdempotencyContext(key=key, request_hash=digest)
        return view(*args, **kwargs)

    return wrapper
