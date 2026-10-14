"""Consultas SQLAlchemy del módulo movements. Solo lee la tabla compartida `transactions`
(ADR-0006); billeteras y usuarios se resuelven vía los servicios de `wallet` y `accounts`."""

from __future__ import annotations

import enum
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, time
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


class MovementType(enum.StrEnum):
    """Valores permitidos del filtro `type` (lista blanca, HU-10 CA-3)."""

    ALL = "all"
    SENT = "sent"
    RECEIVED = "received"
    RECHARGE = "recharge"


@dataclass(frozen=True)
class MovementsFilter:
    """Filtros del historial. `MovementsFilter()` equivale a "sin filtros" (HU-09)."""

    from_: date | None = None
    to: date | None = None
    type_: MovementType = MovementType.ALL


class MovementsRepository(Protocol):
    def list_for_wallet(
        self, wallet_id: int, filters: MovementsFilter, *, offset: int, limit: int
    ) -> Sequence[TransactionRow]: ...

    def count_for_wallet(self, wallet_id: int, filters: MovementsFilter) -> int: ...


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


def _of_type(wallet_id: int, type_: MovementType) -> ColumnElement[bool]:
    """Condición por tipo (HU-10 CA-3). Cada una es un subconjunto de `_owned_by`."""
    if type_ is MovementType.SENT:
        return and_(
            Transaction.type == TransactionType.TRANSFERENCIA,
            Transaction.sender_wallet_id == wallet_id,
        )
    if type_ is MovementType.RECEIVED:
        return and_(
            Transaction.type == TransactionType.TRANSFERENCIA,
            Transaction.receiver_wallet_id == wallet_id,
            Transaction.status == TransactionStatus.EXITOSA,
        )
    if type_ is MovementType.RECHARGE:
        return and_(
            Transaction.type == TransactionType.RECARGA,
            Transaction.receiver_wallet_id == wallet_id,
        )
    return _owned_by(wallet_id)


def _matches(wallet_id: int, filters: MovementsFilter) -> ColumnElement[bool]:
    """Titularidad + tipo + rango de días completos UTC, ambos extremos incluidos (HU-10 CA-1)."""
    conditions = [_of_type(wallet_id, filters.type_)]
    if filters.from_ is not None:
        conditions.append(Transaction.created_at >= datetime.combine(filters.from_, time.min))
    if filters.to is not None:
        conditions.append(Transaction.created_at <= datetime.combine(filters.to, time.max))
    return and_(*conditions)


class SqlMovementsRepository:
    def list_for_wallet(
        self, wallet_id: int, filters: MovementsFilter, *, offset: int, limit: int
    ) -> Sequence[Transaction]:
        # HU-09 CA-4: más reciente primero; `id` desempata filas del mismo segundo.
        statement = (
            select(Transaction)
            .where(_matches(wallet_id, filters))
            .order_by(Transaction.created_at.desc(), Transaction.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(db.session.execute(statement).scalars())

    def count_for_wallet(self, wallet_id: int, filters: MovementsFilter) -> int:
        statement = (
            select(func.count()).select_from(Transaction).where(_matches(wallet_id, filters))
        )
        return int(db.session.execute(statement).scalar_one())


default_repository: MovementsRepository = SqlMovementsRepository()
