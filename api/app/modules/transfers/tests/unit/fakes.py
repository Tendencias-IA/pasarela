"""Dobles de `wallet_service` y `accounts_service` para probar transfers sin BD (testing.md)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

from app.common.models.transaction import TransactionStatus
from app.modules.wallet.service import (
    InsufficientBalanceError,
    WalletBalance,
    WalletNotFoundError,
)


class FakeAccounts:
    def __init__(self, users: dict[str, tuple[int, str | None]] | None = None) -> None:
        # teléfono -> (user_id, nombre completo)
        self.users = users or {}
        self.lookups: list[str] = []

    def get_user_by_phone(self, phone: str) -> SimpleNamespace | None:
        self.lookups.append(phone)
        found = self.users.get(phone)
        if found is None:
            return None
        return SimpleNamespace(id=found[0], phone=phone, full_name=found[1])


class FakeWallet:
    """Billetera de cada usuario: id = user_id * 10; solo lectura en HU-06."""

    def __init__(self, balances: dict[int, Decimal]) -> None:
        self.balances = balances
        self.calls: list[str] = []

    def get_wallet_id(self, user_id: int) -> int | None:
        self.calls.append("get_wallet_id")
        return user_id * 10 if user_id in self.balances else None

    def get_balance(self, user_id: int) -> WalletBalance:
        self.calls.append("get_balance")
        if user_id not in self.balances:
            raise WalletNotFoundError("sin billetera")
        return WalletBalance(balance=self.balances[user_id])

    def transfer_funds(
        self, sender_wallet_id: int, receiver_wallet_id: int, amount: Decimal
    ) -> Decimal:
        self.calls.append("transfer_funds")
        sender, receiver = sender_wallet_id // 10, receiver_wallet_id // 10
        if self.balances[sender] < amount:
            raise InsufficientBalanceError
        self.balances[sender] -= amount
        self.balances[receiver] += amount
        return self.balances[sender]


class FakeTransfersRepository:
    """Registra en orden lo que escribiría el repositorio real."""

    def __init__(self) -> None:
        self.transactions: list[SimpleNamespace] = []
        self.keys: list[dict[str, Any]] = []
        self.units_of_work: list[str] = []
        self.fail_on_transaction = False

    def add_transaction(
        self,
        *,
        status: TransactionStatus,
        amount: Decimal,
        sender_wallet_id: int,
        receiver_wallet_id: int,
        rejection_reason: str | None = None,
    ) -> SimpleNamespace:
        if self.fail_on_transaction:
            raise RuntimeError("fallo inyectado al registrar el movimiento")
        movement = SimpleNamespace(
            id=len(self.transactions) + 1,
            status=status,
            amount=amount,
            sender_wallet_id=sender_wallet_id,
            receiver_wallet_id=receiver_wallet_id,
            rejection_reason=rejection_reason,
            created_at=datetime(2026, 10, 14, 21, 40, 0),
        )
        self.transactions.append(movement)
        self.units_of_work.append(f"transaction:{status.value}")
        return movement

    def add_idempotency_key(
        self, *, user_id: int, key: str, request_hash: str, status_code: int, body: dict[str, Any]
    ) -> None:
        self.keys.append({"user_id": user_id, "key": key, "status_code": status_code, "body": body})
        self.units_of_work.append(f"key:{status_code}")
