"""Reglas de negocio de las transferencias (HU-06, HU-07).

`transfers` solo habla con otros módulos a través de sus `service.py` (architecture.md).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Protocol

from sqlalchemy.exc import IntegrityError

from app.common.errors import AppError, problem_body
from app.common.idempotency import IdempotencyContext
from app.common.masking import mask_name, mask_phone
from app.common.models.transaction import TransactionStatus, TransactionType
from app.common.money import TRANSFER_MAX, TRANSFER_MIN, to_json
from app.extensions import transaction
from app.modules.accounts import service as accounts_service
from app.modules.transfers.repository import TransfersRepository, default_repository
from app.modules.wallet import service as wallet_service
from app.modules.wallet.service import (
    AmountOutOfRangeError,
    DuplicateIdempotencyKeyError,
    InsufficientBalanceError,
    WalletBalance,
    WalletNotFoundError,
)

log = logging.getLogger("app.transfers")


class RecipientNotFoundError(AppError):
    status = 404
    code = "recipient_not_found"
    title = "Destinatario no encontrado"

    def __init__(self) -> None:
        super().__init__("El teléfono no corresponde a un usuario registrado.")


class SelfTransferError(AppError):
    status = 422
    code = "self_transfer"
    title = "Transferencia a la propia cuenta"

    def __init__(self) -> None:
        super().__init__("No puedes transferirte a tu propia cuenta.")


class UserLike(Protocol):
    @property
    def id(self) -> int: ...

    @property
    def phone(self) -> str: ...


class AccountsPort(Protocol):
    def get_user_by_phone(self, phone: str) -> UserLike | None: ...


class WalletPort(Protocol):
    def get_wallet_id(self, user_id: int) -> int | None: ...

    def get_balance(self, user_id: int) -> WalletBalance: ...

    def transfer_funds(
        self, sender_wallet_id: int, receiver_wallet_id: int, amount: Decimal
    ) -> Decimal: ...


@dataclass(frozen=True)
class RecipientMasked:
    """Destinatario ya enmascarado en el servidor (HU-06 CA-7, RNF-06.1)."""

    name_masked: str | None
    phone_masked: str


@dataclass(frozen=True)
class Recipient:
    """Destinatario resuelto; nunca sale del servicio sin pasar por `masked()`."""

    user_id: int
    wallet_id: int
    phone: str
    full_name: str | None

    def masked(self) -> RecipientMasked:
        return RecipientMasked(
            name_masked=mask_name(self.full_name) if self.full_name else None,
            phone_masked=mask_phone(self.phone),
        )


@dataclass(frozen=True)
class TransferPreview:
    amount: Decimal
    recipient: RecipientMasked
    balance_after: Decimal

    def to_body(self) -> dict[str, Any]:
        return {
            "amount": to_json(self.amount),
            "recipient": {
                "name_masked": self.recipient.name_masked,
                "phone_masked": self.recipient.phone_masked,
            },
            "balance_after": to_json(self.balance_after),
        }


def resolve_recipient(
    user_id: int,
    recipient_phone: str,
    amount: Decimal,
    *,
    wallet: WalletPort = wallet_service,
    accounts: AccountsPort = accounts_service,
) -> Recipient:
    """Valida rango, destinatario y propia cuenta, en ese orden (HU-06 CA-2, CA-4, CA-5).

    Un destinatario sin billetera responde igual que uno inexistente para no filtrar el
    estado de otra cuenta (RNF-06.1).
    """
    if not TRANSFER_MIN <= amount <= TRANSFER_MAX:
        raise AmountOutOfRangeError(TRANSFER_MIN, TRANSFER_MAX)
    user = accounts.get_user_by_phone(recipient_phone)
    wallet_id = None if user is None else wallet.get_wallet_id(user.id)
    if user is None or wallet_id is None:
        raise RecipientNotFoundError
    if user.id == user_id:
        raise SelfTransferError
    # `full_name` llega con HU-01; mientras no exista la columna el resumen omite el nombre.
    return Recipient(user.id, wallet_id, user.phone, getattr(user, "full_name", None))


def preview_transfer(
    user_id: int,
    recipient_phone: str,
    amount: Decimal,
    *,
    wallet: WalletPort = wallet_service,
    accounts: AccountsPort = accounts_service,
) -> TransferPreview:
    """Resumen de una transferencia sin ejecutarla: no escribe nada (HU-06 CA-8)."""
    try:
        recipient = resolve_recipient(
            user_id, recipient_phone, amount, wallet=wallet, accounts=accounts
        )
        balance = wallet.get_balance(user_id).balance
        if balance < amount:
            raise InsufficientBalanceError
    except AppError as exc:
        log.info(
            "transfer.preview_rejected",
            extra={
                "user_id": user_id,
                "reason": exc.code,
                "recipient_phone": mask_phone(recipient_phone),
            },
        )
        raise
    log.info(
        "transfer.previewed",
        extra={
            "user_id": user_id,
            "amount": to_json(amount),
            "recipient_phone": mask_phone(recipient_phone),
        },
    )
    return TransferPreview(
        amount=amount, recipient=recipient.masked(), balance_after=balance - amount
    )


@dataclass(frozen=True)
class TransferResult:
    transaction_id: int
    amount: Decimal
    recipient: RecipientMasked
    balance_after: Decimal
    created_at: datetime

    def to_body(self) -> dict[str, Any]:
        return {
            "id": self.transaction_id,
            "type": TransactionType.TRANSFERENCIA.value,
            "status": TransactionStatus.EXITOSA.value,
            "amount": to_json(self.amount),
            "recipient": {
                "name_masked": self.recipient.name_masked,
                "phone_masked": self.recipient.phone_masked,
            },
            "balance_after": to_json(self.balance_after),
            "created_at": self.created_at.replace(microsecond=0).isoformat() + "Z",
        }


def confirm_transfer(
    user_id: int,
    recipient_phone: str,
    amount: Decimal,
    idempotency: IdempotencyContext,
    *,
    instance: str = "/api/v1/transfers",
    request_id: str | None = None,
    repo: TransfersRepository = default_repository,
    wallet: WalletPort = wallet_service,
    accounts: AccountsPort = accounts_service,
) -> TransferResult:
    """Ejecuta la transferencia como una sola operación atómica (HU-07).

    Éxito: débito, crédito, movimiento `exitosa` y clave idempotente en la misma transacción.
    Rechazo de negocio: rollback y, en una segunda transacción, movimiento `rechazada` y clave
    idempotente con el problem (architecture.md, "Operación atómica con bloqueo"). Se revalida
    todo en el servidor, también el saldo, ya con las billeteras bloqueadas (HU-07 CA-2).
    """
    try:
        recipient = resolve_recipient(
            user_id, recipient_phone, amount, wallet=wallet, accounts=accounts
        )
        sender_wallet_id = wallet.get_wallet_id(user_id)
        if sender_wallet_id is None:
            raise WalletNotFoundError("El usuario no tiene una billetera asociada.")
        with transaction():
            balance_after = wallet.transfer_funds(sender_wallet_id, recipient.wallet_id, amount)
            movement = repo.add_transaction(
                status=TransactionStatus.EXITOSA,
                amount=amount,
                sender_wallet_id=sender_wallet_id,
                receiver_wallet_id=recipient.wallet_id,
            )
            result = TransferResult(
                transaction_id=movement.id,
                amount=amount,
                recipient=recipient.masked(),
                balance_after=balance_after,
                created_at=movement.created_at,
            )
            _store_key(repo, user_id, idempotency, 201, result.to_body())
    except DuplicateIdempotencyKeyError:
        raise  # la ruta reproduce la respuesta de la petición que ganó la carrera
    except AppError as exc:
        _record_rejection(
            repo, wallet, accounts, user_id, recipient_phone, amount, idempotency, exc,
            instance, request_id,
        )  # fmt: skip
        raise
    log.info(
        "transfer.applied",
        extra={
            "user_id": user_id,
            "amount": to_json(amount),
            "transaction_id": result.transaction_id,
            "recipient_phone": mask_phone(recipient_phone),
        },
    )
    return result


def _record_rejection(  # noqa: PLR0913
    repo: TransfersRepository,
    wallet: WalletPort,
    accounts: AccountsPort,
    user_id: int,
    recipient_phone: str,
    amount: Decimal,
    idempotency: IdempotencyContext,
    exc: AppError,
    instance: str,
    request_id: str | None,
) -> None:
    """Segunda transacción: movimiento `rechazada` (si hay ambas billeteras) y la clave.

    `transactions.receiver_wallet_id` es NOT NULL: si el destinatario no existe o el emisor
    no tiene billetera no hay a quién asociar la fila y solo se guarda la clave, para que el
    reintento reciba el mismo problem.
    """
    sender_wallet_id = wallet.get_wallet_id(user_id)
    recipient = accounts.get_user_by_phone(recipient_phone)
    receiver_wallet_id = None if recipient is None else wallet.get_wallet_id(recipient.id)
    with transaction():
        if sender_wallet_id is not None and receiver_wallet_id is not None:
            repo.add_transaction(
                status=TransactionStatus.RECHAZADA,
                amount=amount,
                sender_wallet_id=sender_wallet_id,
                receiver_wallet_id=receiver_wallet_id,
                rejection_reason=exc.code,
            )
        _store_key(repo, user_id, idempotency, exc.status, problem_body(exc, instance, request_id))
    log.info(
        "transfer.rejected",
        extra={
            "user_id": user_id,
            "reason": exc.code,
            "amount": to_json(amount),
            "recipient_phone": mask_phone(recipient_phone),
        },
    )


def _store_key(
    repo: TransfersRepository,
    user_id: int,
    idempotency: IdempotencyContext,
    status_code: int,
    body: dict[str, Any],
) -> None:
    try:
        repo.add_idempotency_key(
            user_id=user_id,
            key=idempotency.key,
            request_hash=idempotency.request_hash,
            status_code=status_code,
            body=body,
        )
    except IntegrityError as exc:
        # Otra petición con la misma clave ganó la carrera: se deshace todo y la ruta
        # reproduce la respuesta ganadora.
        raise DuplicateIdempotencyKeyError("Otra solicitud idéntica está en curso.") from exc
