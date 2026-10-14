"""Consultas SQLAlchemy del módulo wallet. Sin commit: la transacción la abre el servicio."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Protocol

from sqlalchemy import select

from app.common.models.idempotency_key import IdempotencyKey
from app.common.models.transaction import Transaction, TransactionStatus, TransactionType
from app.extensions import db
from app.modules.wallet.models import Wallet


class WalletLike(Protocol):
    id: int
    user_id: int
    balance: Decimal


class TransactionLike(Protocol):
    @property
    def id(self) -> int: ...

    @property
    def created_at(self) -> datetime | None: ...


class WalletRepository(Protocol):
    """Contrato que implementan el repositorio real y el falso de las pruebas unitarias."""

    def get_wallet_by_user(self, user_id: int) -> WalletLike | None: ...

    def create_wallet(self, user_id: int) -> WalletLike: ...

    def lock_wallet_for_user(self, user_id: int) -> WalletLike | None: ...

    def add_transaction(
        self,
        *,
        type_: TransactionType,
        status: TransactionStatus,
        amount: Decimal,
        receiver_wallet_id: int,
        sender_wallet_id: int | None = None,
        rejection_reason: str | None = None,
    ) -> TransactionLike: ...

    def add_idempotency_key(
        self, *, user_id: int, key: str, request_hash: str, status_code: int, body: dict[str, Any]
    ) -> None: ...


class SqlWalletRepository:
    def get_wallet_by_user(self, user_id: int) -> Wallet | None:
        return db.session.execute(
            select(Wallet).where(Wallet.user_id == user_id)
        ).scalar_one_or_none()

    def create_wallet(self, user_id: int) -> Wallet:
        wallet = Wallet(user_id=user_id, balance=Decimal("0.00"))
        db.session.add(wallet)
        db.session.flush()
        return wallet

    def lock_wallet_for_user(self, user_id: int) -> Wallet | None:
        # SELECT ... FOR UPDATE: serializa recargas y transferencias sobre la misma
        # billetera (RNF-04.2).
        return db.session.execute(
            select(Wallet).where(Wallet.user_id == user_id).with_for_update()
        ).scalar_one_or_none()

    def add_transaction(
        self,
        *,
        type_: TransactionType,
        status: TransactionStatus,
        amount: Decimal,
        receiver_wallet_id: int,
        sender_wallet_id: int | None = None,
        rejection_reason: str | None = None,
    ) -> Transaction:
        transaction = Transaction(
            type=type_,
            status=status,
            amount=amount,
            receiver_wallet_id=receiver_wallet_id,
            sender_wallet_id=sender_wallet_id,
            rejection_reason=rejection_reason,
        )
        db.session.add(transaction)
        db.session.flush()
        return transaction

    def add_idempotency_key(
        self, *, user_id: int, key: str, request_hash: str, status_code: int, body: dict[str, Any]
    ) -> None:
        db.session.add(
            IdempotencyKey(
                user_id=user_id,
                key=key,
                request_hash=request_hash,
                status_code=status_code,
                response_body=body,
            )
        )
        db.session.flush()


default_repository: WalletRepository = SqlWalletRepository()
