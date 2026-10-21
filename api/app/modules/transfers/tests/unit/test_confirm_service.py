"""Confirmar una transferencia con dobles de wallet/accounts y repositorio falso (HU-07)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from flask import Flask

from app.common.idempotency import IdempotencyContext
from app.common.idempotency_store import DuplicateIdempotencyKeyError
from app.common.models.transaction import TransactionStatus
from app.modules.transfers import service
from app.modules.transfers.service import RecipientNotFoundError, SelfTransferError
from app.modules.transfers.tests.unit.fakes import (
    FakeAccounts,
    FakeTransfersRepository,
    FakeWallet,
)
from app.modules.wallet.service import (
    AmountOutOfRangeError,
    InsufficientBalanceError,
    WalletNotFoundError,
)

SENDER, RECIPIENT = 1, 2
PHONE = "3001234567"
CTX = IdempotencyContext(key="00000000-0000-4000-8000-000000000001", request_hash="h" * 64)


@pytest.fixture
def wallet() -> FakeWallet:
    return FakeWallet({SENDER: Decimal("500000.00"), RECIPIENT: Decimal("0.00")})


@pytest.fixture
def accounts() -> FakeAccounts:
    return FakeAccounts({PHONE: (RECIPIENT, None), "3000000001": (SENDER, None)})


@pytest.fixture
def repo() -> FakeTransfersRepository:
    return FakeTransfersRepository()


def _confirm(  # noqa: PLR0913
    app: Flask,
    repo: FakeTransfersRepository,
    wallet: FakeWallet,
    accounts: FakeAccounts,
    amount: str,
    phone: str = PHONE,
    request_id: str | None = None,
) -> service.TransferResult:
    return service.confirm_transfer(
        SENDER,
        phone,
        Decimal(amount),
        CTX,
        request_id=request_id,
        repo=repo,
        wallet=wallet,
        accounts=accounts,
    )


def test_confirm_moves_money_and_records_one_successful_transaction(
    app: Flask, repo: FakeTransfersRepository, wallet: FakeWallet, accounts: FakeAccounts
) -> None:
    """HU-07 CA-3, CA-5."""
    result = _confirm(app, repo, wallet, accounts, "150000.00")

    assert wallet.balances == {SENDER: Decimal("350000.00"), RECIPIENT: Decimal("150000.00")}
    assert result.balance_after == Decimal("350000.00")
    [movement] = repo.transactions
    assert movement.status is TransactionStatus.EXITOSA
    assert (movement.sender_wallet_id, movement.receiver_wallet_id) == (10, 20)
    assert movement.amount == Decimal("150000.00")


def test_confirm_body_matches_the_documented_response_and_masks_the_recipient(
    app: Flask, repo: FakeTransfersRepository, wallet: FakeWallet
) -> None:
    """HU-07 CA-7, RNF-06.1."""
    accounts = FakeAccounts({PHONE: (RECIPIENT, "Maria Garcia")})

    body = _confirm(app, repo, wallet, accounts, "150000.00").to_body()

    assert body == {
        "id": 1,
        "type": "transferencia",
        "status": "exitosa",
        "amount": "150000.00",
        "recipient": {"name_masked": "Mar** G*****", "phone_masked": "***4567"},
        "balance_after": "350000.00",
        "created_at": "2026-10-14T21:40:00Z",
    }


def test_confirm_stores_the_idempotency_key_in_the_same_unit_of_work(
    app: Flask, repo: FakeTransfersRepository, wallet: FakeWallet, accounts: FakeAccounts
) -> None:
    """HU-07 CA-8, ADR-0005: movimiento y clave se escriben juntos."""
    _confirm(app, repo, wallet, accounts, "1000.00")

    assert repo.units_of_work == ["transaction:exitosa", "key:201"]
    assert repo.keys[0]["key"] == CTX.key
    assert repo.keys[0]["body"]["status"] == "exitosa"


def test_confirm_failure_after_debit_propagates_and_writes_no_key(
    app: Flask, repo: FakeTransfersRepository, wallet: FakeWallet, accounts: FakeAccounts
) -> None:
    """HU-07 CA-4: un fallo inesperado no se registra como rechazo de negocio."""
    repo.fail_on_transaction = True

    with pytest.raises(RuntimeError):
        _confirm(app, repo, wallet, accounts, "1000.00")

    assert repo.keys == [] and repo.transactions == []


@pytest.mark.parametrize(
    ("error", "amount", "phone", "reason"),
    [
        (AmountOutOfRangeError, "99.00", PHONE, "amount_out_of_range"),
        (SelfTransferError, "1000.00", "3000000001", "self_transfer"),
        (InsufficientBalanceError, "500000.01", PHONE, "insufficient_balance"),
    ],
)
def test_rejection_records_a_rejected_transaction_and_key_in_a_second_unit_of_work(
    app: Flask,
    repo: FakeTransfersRepository,
    wallet: FakeWallet,
    accounts: FakeAccounts,
    error: type[Exception],
    amount: str,
    phone: str,
    reason: str,
) -> None:
    """HU-07 CA-2, CA-6, architecture.md 'Estados de una operación'."""
    with pytest.raises(error):
        _confirm(app, repo, wallet, accounts, amount, phone, request_id="abc123")

    assert wallet.balances[SENDER] == Decimal("500000.00")
    [movement] = repo.transactions
    assert movement.status is TransactionStatus.RECHAZADA
    assert movement.rejection_reason == reason
    assert movement.sender_wallet_id == 10
    assert repo.units_of_work == ["transaction:rechazada", "key:422"]
    assert repo.keys[0]["body"]["code"] == reason
    assert repo.keys[0]["body"]["request_id"] == "abc123"


def test_rejection_for_unknown_recipient_stores_only_the_key(
    app: Flask, repo: FakeTransfersRepository, wallet: FakeWallet, accounts: FakeAccounts
) -> None:
    """HU-07 CA-2: sin destinatario no hay billetera receptora (columna NOT NULL), no hay fila."""
    with pytest.raises(RecipientNotFoundError):
        _confirm(app, repo, wallet, accounts, "1000.00", phone="3999999999")

    assert repo.transactions == []
    assert repo.units_of_work == ["key:404"]
    assert repo.keys[0]["body"]["code"] == "recipient_not_found"


def test_rejection_without_sender_wallet_stores_only_the_key(
    app: Flask, repo: FakeTransfersRepository, accounts: FakeAccounts
) -> None:
    wallet = FakeWallet({RECIPIENT: Decimal("0.00")})

    with pytest.raises(WalletNotFoundError):
        _confirm(app, repo, wallet, accounts, "1000.00")

    assert repo.transactions == []
    assert repo.units_of_work == ["key:404"]


def test_duplicate_key_race_is_reported_as_in_progress(
    app: Flask, repo: FakeTransfersRepository, wallet: FakeWallet, accounts: FakeAccounts
) -> None:
    """HU-07 CA-8, ADR-0005: dos peticiones con la misma clave compiten en el INSERT."""
    from sqlalchemy.exc import IntegrityError

    def boom(**_: object) -> None:
        raise IntegrityError("INSERT", {}, Exception("duplicate"))

    repo.add_idempotency_key = boom  # type: ignore[method-assign]

    with pytest.raises(DuplicateIdempotencyKeyError):
        _confirm(app, repo, wallet, accounts, "1000.00")

    assert repo.units_of_work == ["transaction:exitosa"]
