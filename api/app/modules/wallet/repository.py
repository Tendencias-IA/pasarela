"""Consultas SQLAlchemy del módulo wallet. Sin commit: la transacción la abre el servicio."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import datetime
from decimal import Decimal
from typing import Any, Protocol

from sqlalchemy import select

from app.common.clock import utcnow
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
    def created_at(self) -> datetime: ...


class WalletRepository(Protocol):
    """Contrato que implementan el repositorio real y el falso de las pruebas unitarias."""

    def get_wallet_by_user(self, user_id: int) -> WalletLike | None: ...

    def create_wallet(self, user_id: int) -> WalletLike: ...

    def lock_wallet_for_user(self, user_id: int) -> WalletLike | None: ...

    def lock_wallets(self, wallet_ids: Iterable[int]) -> Sequence[WalletLike]: ...

    def get_wallets_by_ids(self, wallet_ids: Iterable[int]) -> Sequence[WalletLike]: ...

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

    def get_wallets_by_ids(self, wallet_ids: Iterable[int]) -> list[Wallet]:
        ids = list(wallet_ids)
        if not ids:
            return []
        return list(db.session.execute(select(Wallet).where(Wallet.id.in_(ids))).scalars())

    def lock_wallet_for_user(self, user_id: int) -> Wallet | None:
        # SELECT ... FOR UPDATE: serializa recargas y transferencias sobre la misma
        # billetera (RNF-04.2).
        return db.session.execute(
            select(Wallet).where(Wallet.user_id == user_id).with_for_update()
        ).scalar_one_or_none()

    def lock_wallets(self, wallet_ids: Iterable[int]) -> list[Wallet]:
        # Orden ascendente de id: dos transferencias cruzadas piden los bloqueos en el mismo
        # orden y no pueden dar deadlock (architecture.md, RNF-04.2).
        ids = sorted(set(wallet_ids))
        statement = select(Wallet).where(Wallet.id.in_(ids)).order_by(Wallet.id).with_for_update()
        return list(db.session.execute(statement).scalars())

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
            created_at=utcnow(),
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
                created_at=utcnow(),
            )
        )
        db.session.flush()


default_repository: WalletRepository = SqlWalletRepository()
