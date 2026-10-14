"""Reglas de negocio de la billetera (HU-05, HU-08). Abre y cierra las transacciones."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy.exc import IntegrityError

from app.common.errors import AppError, problem_body
from app.common.models.transaction import TransactionStatus, TransactionType
from app.common.money import RECHARGE_MAX, RECHARGE_MIN, to_json
from app.extensions import transaction
from app.modules.accounts import service as accounts_service
from app.modules.wallet import repository as wallet_repository
from app.modules.wallet.models import Wallet
from app.modules.wallet.repository import SessionLike, WalletRepository, default_repository

log = logging.getLogger("app.wallet")

if TYPE_CHECKING:
    from app.common.idempotency import IdempotencyContext


def create_wallet_for_account(user_id: int, session: SessionLike) -> Wallet:
    """HU-01 CA-2: crea la billetera dentro de la transacción del registro."""
    return wallet_repository.create_for_user(user_id, session)


class WalletNotFoundError(AppError):
    status = 404
    code = "wallet_not_found"
    title = "Billetera no encontrada"


class AmountOutOfRangeError(AppError):
    status = 422
    code = "amount_out_of_range"
    title = "Monto fuera de rango"

    def __init__(self) -> None:
        detail = f"El monto debe estar entre {to_json(RECHARGE_MIN)} y {to_json(RECHARGE_MAX)} COP."
        super().__init__(
            detail,
            errors=[
                {
                    "field": "amount",
                    "message": (
                        f"Debe estar entre {to_json(RECHARGE_MIN)} y {to_json(RECHARGE_MAX)}"
                    ),
                }
            ],
        )


class DuplicateIdempotencyKeyError(AppError):
    """Carrera entre dos peticiones con la misma clave; la ruta responde con el replay."""

    status = 409
    code = "idempotency_key_in_progress"
    title = "Solicitud en curso"


@dataclass(frozen=True)
class RechargeResult:
    transaction_id: int
    amount: Decimal
    balance_after: Decimal
    created_at: datetime

    def to_body(self) -> dict[str, Any]:
        return {
            "id": self.transaction_id,
            "type": TransactionType.RECARGA.value,
            "status": TransactionStatus.EXITOSA.value,
            "amount": to_json(self.amount),
            "balance_after": to_json(self.balance_after),
            "created_at": self.created_at.replace(microsecond=0).isoformat() + "Z",
        }


def get_wallet_id(user_id: int, repo: WalletRepository = default_repository) -> int | None:
    """Id de la billetera del usuario, o None si no tiene (sin abrir transacción propia)."""
    wallet = repo.get_wallet_by_user(user_id)
    return None if wallet is None else wallet.id


@dataclass(frozen=True)
class WalletBalance:
    balance: Decimal


def get_balance(user_id: int, repo: WalletRepository = default_repository) -> WalletBalance:
    """Saldo persistido de la billetera del usuario (HU-05). Solo lectura: sin bloqueo.

    Sin billetera (dato inconsistente) lanza `WalletNotFoundError` y registra el error
    técnico (HU-05 CA-5); no se crea una billetera a escondidas.
    """
    wallet = repo.get_wallet_by_user(user_id)
    if wallet is None:
        log.warning("wallet.missing", extra={"user_id": user_id})
        raise WalletNotFoundError("El saldo no está disponible: la cuenta no tiene billetera.")
    return WalletBalance(balance=wallet.balance)


@dataclass(frozen=True)
class WalletOwner:
    """Titular de una billetera, para que otros módulos enmascaren la contraparte (HU-09 CA-3)."""

    wallet_id: int
    user_id: int
    phone: str
    full_name: str | None


def get_wallet_owners(
    wallet_ids: Iterable[int], repo: WalletRepository = default_repository
) -> dict[int, WalletOwner]:
    """Billetera → titular; ids inexistentes se omiten. Usa accounts_service, nunca sus tablas."""
    wallets = repo.get_wallets_by_ids(wallet_ids)
    users = accounts_service.get_users_by_ids(w.user_id for w in wallets)
    return {
        w.id: WalletOwner(
            wallet_id=w.id, user_id=w.user_id, phone=user.phone, full_name=user.full_name
        )
        for w in wallets
        if (user := users.get(w.user_id)) is not None
    }


def create_wallet(user_id: int, repo: WalletRepository = default_repository) -> int:
    """Crea la billetera con saldo 0 (la usa HU-01 al registrar). Devuelve su id."""
    with transaction():
        wallet = repo.create_wallet(user_id)
        return wallet.id


def recharge(
    user_id: int,
    amount: Decimal,
    idempotency: IdempotencyContext,
    *,
    instance: str = "/api/v1/wallet/recharges",
    request_id: str | None = None,
    repo: WalletRepository = default_repository,
) -> RechargeResult:
    """Acredita `amount` en la billetera del usuario como una sola operación (HU-08).

    Éxito: saldo, movimiento `exitosa` y clave idempotente en la misma transacción.
    Rechazo de negocio: rollback y, en una segunda transacción, movimiento `rechazada` y
    clave idempotente con el problem (architecture.md, "Operación atómica con bloqueo").
    """
    try:
        with transaction():
            wallet = repo.lock_wallet_for_user(user_id)
            if wallet is None:
                raise WalletNotFoundError("El usuario no tiene una billetera asociada.")
            if not RECHARGE_MIN <= amount <= RECHARGE_MAX:
                raise AmountOutOfRangeError
            wallet.balance = wallet.balance + amount
            movement = repo.add_transaction(
                type_=TransactionType.RECARGA,
                status=TransactionStatus.EXITOSA,
                amount=amount,
                receiver_wallet_id=wallet.id,
            )
            result = RechargeResult(
                transaction_id=movement.id,
                amount=amount,
                balance_after=wallet.balance,
                created_at=movement.created_at,
            )
            _store_key(repo, user_id, idempotency, 201, result.to_body())
    except AmountOutOfRangeError as exc:
        _record_rejection(repo, user_id, amount, idempotency, exc, instance, request_id)
        raise
    log.info(
        "recharge.applied",
        extra={
            "user_id": user_id,
            "amount": to_json(amount),
            "transaction_id": result.transaction_id,
        },
    )
    return result


def _record_rejection(
    repo: WalletRepository,
    user_id: int,
    amount: Decimal,
    idempotency: IdempotencyContext,
    exc: AppError,
    instance: str,
    request_id: str | None,
) -> None:
    wallet = repo.get_wallet_by_user(user_id)
    if wallet is None:
        return
    with transaction():
        repo.add_transaction(
            type_=TransactionType.RECARGA,
            status=TransactionStatus.RECHAZADA,
            amount=amount,
            receiver_wallet_id=wallet.id,
            rejection_reason=exc.code,
        )
        _store_key(repo, user_id, idempotency, exc.status, problem_body(exc, instance, request_id))
    log.info(
        "recharge.rejected",
        extra={"user_id": user_id, "reason": exc.code, "amount": to_json(amount)},
    )


def _store_key(
    repo: WalletRepository,
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
