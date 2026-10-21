"""Persistencia de la respuesta idempotente dentro de la transacción del servicio (ADR-0005).

Vive aparte de `idempotency.py` (capa de ruta) porque los servicios de `wallet` y `transfers`
lo importan y `idempotency.py` depende de `auth`, que a su vez llega hasta `wallet`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

from sqlalchemy.exc import IntegrityError

from app.common.errors import AppError

if TYPE_CHECKING:
    from app.common.idempotency import IdempotencyContext


class DuplicateIdempotencyKeyError(AppError):
    """Carrera entre dos peticiones con la misma clave; la ruta responde con el replay."""

    status = 409
    code = "idempotency_key_in_progress"
    title = "Solicitud en curso"


class IdempotencyKeyStore(Protocol):
    """Lo que `store_response` necesita de un repositorio (wallet y transfers lo cumplen)."""

    def add_idempotency_key(
        self, *, user_id: int, key: str, request_hash: str, status_code: int, body: dict[str, Any]
    ) -> None: ...


def store_response(
    repo: IdempotencyKeyStore,
    user_id: int,
    idempotency: IdempotencyContext,
    status_code: int,
    body: dict[str, Any],
) -> None:
    """Guarda la respuesta junto a la operación o al rechazo que la produjo."""
    try:
        repo.add_idempotency_key(
            user_id=user_id,
            key=idempotency.key,
            request_hash=idempotency.request_hash,
            status_code=status_code,
            body=body,
        )
    except IntegrityError as exc:
        # Otra petición con la misma clave ganó la carrera: se deshace todo y la ruta
        # reproduce la respuesta ganadora.
        raise DuplicateIdempotencyKeyError("Otra solicitud idéntica está en curso.") from exc
