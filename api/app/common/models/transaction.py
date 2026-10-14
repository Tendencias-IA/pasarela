"""Tabla compartida `transactions` (ADR-0006): recargas y transferencias."""

from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import Base


class TransactionType(enum.StrEnum):
    TRANSFERENCIA = "transferencia"
    RECARGA = "recarga"


class TransactionStatus(enum.StrEnum):
    EXITOSA = "exitosa"
    RECHAZADA = "rechazada"


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_transactions_amount_positive"),
        Index("ix_transactions_receiver_created", "receiver_wallet_id", "created_at"),
        Index("ix_transactions_sender_created", "sender_wallet_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    type: Mapped[TransactionType] = mapped_column(
        Enum(
            TransactionType, name="transaction_type", values_callable=lambda e: [m.value for m in e]
        ),
        nullable=False,
    )
    status: Mapped[TransactionStatus] = mapped_column(
        Enum(
            TransactionStatus,
            name="transaction_status",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2, asdecimal=True), nullable=False)
    sender_wallet_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("wallets.id"), nullable=True
    )
    receiver_wallet_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("wallets.id"), nullable=False
    )
    rejection_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=func.now()
    )
