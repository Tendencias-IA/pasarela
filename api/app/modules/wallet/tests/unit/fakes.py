"""Repositorio falso en memoria para probar el servicio sin base de datos (testing.md)."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

from app.common.models.transaction import TransactionStatus, TransactionType


class FakeWalletRepository:
    def __init__(self, balances: dict[int, Decimal] | None = None) -> None:
        self.wallets: dict[int, SimpleNamespace] = {}
        for i, (user_id, balance) in enumerate((balances or {}).items(), start=1):
            self.wallets[user_id] = SimpleNamespace(id=i, user_id=user_id, balance=balance)
        self.transactions: list[SimpleNamespace] = []
        self.keys: list[dict[str, Any]] = []
        self.locked: list[int] = []
        self.locked_wallet_ids: list[list[int]] = []
        self.units_of_work: list[str] = []
        self.fail_on_key = False

    def get_wallet_by_user(self, user_id: int) -> SimpleNamespace | None:
        return self.wallets.get(user_id)

    def create_wallet(self, user_id: int) -> SimpleNamespace:
        wallet = SimpleNamespace(id=len(self.wallets) + 1, user_id=user_id, balance=Decimal("0.00"))
        self.wallets[user_id] = wallet
        return wallet

    def get_wallets_by_ids(self, wallet_ids: Iterable[int]) -> list[SimpleNamespace]:
        ids = set(wallet_ids)
        return [w for w in self.wallets.values() if w.id in ids]

    def lock_wallet_for_user(self, user_id: int) -> SimpleNamespace | None:
        self.locked.append(user_id)
        return self.wallets.get(user_id)

    def lock_wallets(self, wallet_ids: Iterable[int]) -> list[SimpleNamespace]:
        ordered = sorted(set(wallet_ids))
        self.locked_wallet_ids.append(ordered)
        return [w for i in ordered for w in self.wallets.values() if w.id == i]

    def add_transaction(
        self,
        *,
        type_: TransactionType,
        status: TransactionStatus,
        amount: Decimal,
        receiver_wallet_id: int,
        sender_wallet_id: int | None = None,
        rejection_reason: str | None = None,
    ) -> SimpleNamespace:
        transaction = SimpleNamespace(
            id=len(self.transactions) + 1,
            type=type_,
            status=status,
            amount=amount,
            receiver_wallet_id=receiver_wallet_id,
            sender_wallet_id=sender_wallet_id,
            rejection_reason=rejection_reason,
            created_at=datetime(2026, 10, 14, 21, 40, 0),
        )
        self.transactions.append(transaction)
        self.units_of_work.append(f"transaction:{status.value}")
        return transaction

    def add_idempotency_key(
        self, *, user_id: int, key: str, request_hash: str, status_code: int, body: dict[str, Any]
    ) -> None:
        if self.fail_on_key:
            raise RuntimeError("fallo inyectado al guardar la clave")
        self.keys.append(
            {
                "user_id": user_id,
                "key": key,
                "request_hash": request_hash,
                "status_code": status_code,
                "body": body,
            }
        )
        self.units_of_work.append(f"key:{status_code}")
