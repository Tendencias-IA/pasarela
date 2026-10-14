"""Consultas SQLAlchemy del módulo movements. Solo lee la tabla compartida `transactions`
(ADR-0006); billeteras y usuarios se resuelven vía los servicios de `wallet` y `accounts`."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from typing import Protocol

from sqlalchemy import ColumnElement, and_, func, or_, select

from app.common.models.transaction import Transaction, TransactionStatus, TransactionType
from app.extensions import db


class TransactionRow(Protocol):
    """Lo que el servicio necesita de una fila; lo cumplen `Transaction` y los fakes."""

    @property
    def id(self) -> int: ...

    @property
    def type(self) -> TransactionType: ...

    @property
    def status(self) -> TransactionStatus: ...

    @property
    def amount(self) -> Decimal: ...

    @property
    def sender_wallet_id(self) -> int | None: ...

    @property
    def receiver_wallet_id(self) -> int: ...

    @property
    def rejection_reason(self) -> str | None: ...

    @property
    def created_at(self) -> datetime: ...


class MovementsRepository(Protocol):
    def list_for_wallet(
        self, wallet_id: int, *, offset: int, limit: int
    ) -> Sequence[TransactionRow]: ...

    def count_for_wallet(self, wallet_id: int) -> int: ...


def _owned_by(wallet_id: int) -> ColumnElement[bool]:
    """Movimientos "de" una billetera (HU-09 CA-1, CA-5).

    Quien envía ve su transferencia aunque fuera rechazada; quien recibe solo la ve si
    fue exitosa (una rechazada nunca le llegó). Una recarga rechazada sí es del titular.
    """
    return or_(
        Transaction.sender_wallet_id == wallet_id,
        and_(
            Transaction.receiver_wallet_id == wallet_id,
            or_(
                Transaction.type == TransactionType.RECARGA,
                Transaction.status == TransactionStatus.EXITOSA,
            ),
        ),
    )


class SqlMovementsRepository:
    def list_for_wallet(self, wallet_id: int, *, offset: int, limit: int) -> Sequence[Transaction]:
        # HU-09 CA-4: más reciente primero; `id` desempata filas del mismo segundo.
        statement = (
            select(Transaction)
            .where(_owned_by(wallet_id))
            .order_by(Transaction.created_at.desc(), Transaction.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(db.session.execute(statement).scalars())

    def count_for_wallet(self, wallet_id: int) -> int:
        statement = select(func.count()).select_from(Transaction).where(_owned_by(wallet_id))
        return int(db.session.execute(statement).scalar_one())


default_repository: MovementsRepository = SqlMovementsRepository()
