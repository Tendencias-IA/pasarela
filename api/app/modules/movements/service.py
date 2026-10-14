"""Reglas del historial de movimientos (HU-09). Solo lectura: no abre transacciones."""

from __future__ import annotations

import enum
import logging
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.common.masking import HIDDEN, mask_name, mask_phone
from app.common.models.transaction import TransactionStatus, TransactionType
from app.modules.movements.repository import MovementsRepository, TransactionRow, default_repository
from app.modules.wallet import service as wallet_service
from app.modules.wallet.service import WalletOwner

log = logging.getLogger("app.movements")

PAGE_SIZE = 20  # RF-05: fijo, no configurable por query (api-design.md)


class Direction(enum.StrEnum):
    """Punto de vista de la billetera del usuario (HU-09 CA-1, FR-003)."""

    RECARGA = "recarga"
    ENVIADA = "enviada"
    RECIBIDA = "recibida"


@dataclass(frozen=True)
class Counterparty:
    """Otro participante, ya enmascarado en el servidor (HU-09 CA-3, RNF-06.1)."""

    name_masked: str | None
    phone_masked: str


@dataclass(frozen=True)
class Movement:
    id: int
    direction: Direction
    type: TransactionType
    status: TransactionStatus
    amount: Decimal
    created_at: datetime
    rejection_reason: str | None
    counterparty: Counterparty | None


@dataclass(frozen=True)
class MovementsPage:
    items: list[Movement]
    page: int
    page_size: int
    total: int


WalletIdFor = Callable[[int], int | None]
OwnersFor = Callable[[Iterable[int]], dict[int, WalletOwner]]


def list_movements(
    user_id: int,
    page: int,
    *,
    repo: MovementsRepository = default_repository,
    wallet_id_for: WalletIdFor = wallet_service.get_wallet_id,
    owners_for: OwnersFor = wallet_service.get_wallet_owners,
) -> MovementsPage:
    """Página `page` (desde 1) de los movimientos de la billetera del usuario.

    Sin billetera (dato inconsistente) responde vacío sin crearla. Una página más allá
    de la última responde vacía con el `total` real (FR-009).
    """
    wallet_id = wallet_id_for(user_id)
    if wallet_id is None:
        log.warning("movements.wallet_missing", extra={"user_id": user_id})
        return MovementsPage(items=[], page=page, page_size=PAGE_SIZE, total=0)

    offset = (page - 1) * PAGE_SIZE
    rows = repo.list_for_wallet(wallet_id, offset=offset, limit=PAGE_SIZE)
    total = repo.count_for_wallet(wallet_id)
    owners = _resolve_owners(rows, wallet_id, owners_for)
    items = [_project(row, wallet_id, owners) for row in rows]
    log.info("movements.listed", extra={"user_id": user_id, "page": page, "total": total})
    return MovementsPage(items=items, page=page, page_size=PAGE_SIZE, total=total)


def _other_wallet(row: TransactionRow, wallet_id: int) -> int | None:
    if row.type is not TransactionType.TRANSFERENCIA:
        return None
    return row.receiver_wallet_id if row.sender_wallet_id == wallet_id else row.sender_wallet_id


def _resolve_owners(
    rows: Iterable[TransactionRow], wallet_id: int, owners_for: OwnersFor
) -> dict[int, WalletOwner]:
    # Una sola consulta por página con las billeteras ajenas (research §1).
    others = {w for row in rows if (w := _other_wallet(row, wallet_id)) is not None}
    return owners_for(others) if others else {}


def _project(row: TransactionRow, wallet_id: int, owners: dict[int, WalletOwner]) -> Movement:
    if row.type is TransactionType.RECARGA:
        direction, counterparty = Direction.RECARGA, None
    else:
        direction = Direction.ENVIADA if row.sender_wallet_id == wallet_id else Direction.RECIBIDA
        other = _other_wallet(row, wallet_id)
        owner = owners.get(other) if other is not None else None
        # RNF-06.1: el navegador nunca recibe el dato completo; sin titular, solo "***".
        counterparty = Counterparty(
            name_masked=mask_name(owner.full_name) if owner and owner.full_name else None,
            phone_masked=mask_phone(owner.phone) if owner else HIDDEN,
        )
    return Movement(
        id=row.id,
        direction=direction,
        type=row.type,
        status=row.status,
        amount=row.amount,
        created_at=row.created_at,
        rejection_reason=row.rejection_reason,
        counterparty=counterparty,
    )
