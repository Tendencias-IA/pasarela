"""Consultas SQLAlchemy del módulo transfers. Sin commit: la transacción la abre el servicio.

`transfers` no tiene tablas propias: escribe en las compartidas `transactions` e
`idempotency_keys` (ADR-0006); billeteras y usuarios se tocan solo vía los servicios de
`wallet` y `accounts`.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Protocol

from app.common.clock import utcnow
from app.common.models.idempotency_key import IdempotencyKey
from app.common.models.transaction import Transaction, TransactionStatus, TransactionType
from app.extensions import db


class TransactionLike(Protocol):
    @property
    def id(self) -> int: ...

    @property
    def created_at(self) -> datetime: ...


class TransfersRepository(Protocol):
    """Contrato que implementan el repositorio real y el falso de las pruebas unitarias."""

    def add_transaction(
        self,
        *,
        status: TransactionStatus,
        amount: Decimal,
        sender_wallet_id: int,
        receiver_wallet_id: int,
        rejection_reason: str | None = None,
    ) -> TransactionLike: ...

    def add_idempotency_key(
        self, *, user_id: int, key: str, request_hash: str, status_code: int, body: dict[str, Any]
    ) -> None: ...


class SqlTransfersRepository:
    def add_transaction(
        self,
        *,
        status: TransactionStatus,
        amount: Decimal,
        sender_wallet_id: int,
        receiver_wallet_id: int,
        rejection_reason: str | None = None,
    ) -> Transaction:
        movement = Transaction(
            type=TransactionType.TRANSFERENCIA,
            status=status,
            amount=amount,
            sender_wallet_id=sender_wallet_id,
            receiver_wallet_id=receiver_wallet_id,
            rejection_reason=rejection_reason,
            created_at=utcnow(),
        )
        db.session.add(movement)
        db.session.flush()
        return movement

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


default_repository: TransfersRepository = SqlTransfersRepository()
