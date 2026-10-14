"""Repositorio y colaboradores falsos para probar `movements.service` sin base de datos."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

from app.common.models.transaction import TransactionStatus, TransactionType
from app.modules.wallet.service import WalletOwner


def row(
    id_: int,
    *,
    type_: TransactionType = TransactionType.RECARGA,
    status: TransactionStatus = TransactionStatus.EXITOSA,
    amount: str = "50000.00",
    receiver: int = 1,
    sender: int | None = None,
    reason: str | None = None,
    created_at: datetime = datetime(2026, 10, 14, 21, 40, 0),
) -> SimpleNamespace:
    return SimpleNamespace(
        id=id_,
        type=type_,
        status=status,
        amount=Decimal(amount),
        receiver_wallet_id=receiver,
        sender_wallet_id=sender,
        rejection_reason=reason,
        created_at=created_at,
    )


class FakeMovementsRepository:
    def __init__(self, rows: list[SimpleNamespace]) -> None:
        self.rows = rows
        self.calls: list[tuple[int, int, int]] = []

    def _for_wallet(self, wallet_id: int) -> list[SimpleNamespace]:
        # Misma regla que SqlMovementsRepository._owned_by.
        mine = [
            r
            for r in self.rows
            if r.sender_wallet_id == wallet_id
            or (
                r.receiver_wallet_id == wallet_id
                and (r.type is TransactionType.RECARGA or r.status is TransactionStatus.EXITOSA)
            )
        ]
        return sorted(mine, key=lambda r: (r.created_at, r.id), reverse=True)

    def list_for_wallet(self, wallet_id: int, *, offset: int, limit: int) -> list[SimpleNamespace]:
        self.calls.append((wallet_id, offset, limit))
        return self._for_wallet(wallet_id)[offset : offset + limit]

    def count_for_wallet(self, wallet_id: int) -> int:
        return len(self._for_wallet(wallet_id))


class FakeOwners:
    """Simula `wallet_service.get_wallet_owners` y registra cada llamada."""

    def __init__(self, owners: dict[int, WalletOwner] | None = None) -> None:
        self.owners = owners or {}
        self.calls: list[set[int]] = []

    def __call__(self, wallet_ids: Iterable[int]) -> dict[int, WalletOwner]:
        ids = set(wallet_ids)
        self.calls.append(ids)
        return {k: v for k, v in self.owners.items() if k in ids}


def owner(wallet_id: int, user_id: int, phone: str, full_name: str | None = None) -> WalletOwner:
    return WalletOwner(wallet_id=wallet_id, user_id=user_id, phone=phone, full_name=full_name)
