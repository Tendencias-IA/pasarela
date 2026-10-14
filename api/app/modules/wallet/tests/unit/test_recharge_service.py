"""Servicio de recarga con repositorio falso (HU-08)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from flask import Flask

from app.common.idempotency import IdempotencyContext
from app.common.models.transaction import TransactionStatus, TransactionType
from app.modules.wallet import service
from app.modules.wallet.service import AmountOutOfRangeError, WalletNotFoundError
from app.modules.wallet.tests.unit.fakes import FakeWalletRepository

CTX = IdempotencyContext(key="00000000-0000-4000-8000-000000000001", request_hash="h" * 64)


@pytest.fixture
def repo() -> FakeWalletRepository:
    return FakeWalletRepository({1: Decimal("0.00"), 2: Decimal("4995000.00")})


def test_recharge_min_amount_increases_balance_and_records_transaction(
    app: Flask, repo: FakeWalletRepository
) -> None:
    """HU-08 CA-1, CA-3, CA-4."""
    result = service.recharge(1, Decimal("5000.00"), CTX, repo=repo)

    assert repo.wallets[1].balance == Decimal("5000.00")
    assert result.balance_after == Decimal("5000.00")
    assert result.amount == Decimal("5000.00")
    assert [t.status for t in repo.transactions] == [TransactionStatus.EXITOSA]
    assert repo.transactions[0].type is TransactionType.RECARGA
    assert repo.transactions[0].receiver_wallet_id == repo.wallets[1].id
    assert repo.locked == [1]


def test_recharge_max_amount_has_no_balance_cap(app: Flask, repo: FakeWalletRepository) -> None:
    """HU-08 CA-1, CA-7."""
    result = service.recharge(2, Decimal("5000000.00"), CTX, repo=repo)

    assert result.balance_after == Decimal("9995000.00")


def test_recharge_keeps_two_decimals_exactly(app: Flask, repo: FakeWalletRepository) -> None:
    """RNF-04.3."""
    result = service.recharge(1, Decimal("120500.50"), CTX, repo=repo)

    assert result.balance_after == Decimal("120500.50")
    assert result.to_body()["amount"] == "120500.50"
    assert result.to_body()["balance_after"] == "120500.50"


def test_recharge_persists_idempotency_key_in_same_unit_of_work(
    app: Flask, repo: FakeWalletRepository
) -> None:
    """FR-006, FR-007: la clave se guarda junto al movimiento, con el cuerpo de la respuesta."""
    service.recharge(1, Decimal("5000.00"), CTX, repo=repo)

    assert repo.units_of_work == ["transaction:exitosa", "key:201"]
    assert repo.keys[0]["key"] == CTX.key
    assert repo.keys[0]["body"]["balance_after"] == "5000.00"
    assert repo.keys[0]["body"]["status"] == "exitosa"


def test_recharge_without_wallet_raises_wallet_not_found(
    app: Flask, repo: FakeWalletRepository
) -> None:
    with pytest.raises(WalletNotFoundError):
        service.recharge(99, Decimal("5000.00"), CTX, repo=repo)

    assert repo.transactions == []
    assert repo.keys == []


@pytest.mark.parametrize("amount", ["4999.99", "5000000.01", "0.01"])
def test_recharge_out_of_range_is_rejected_without_changing_balance(
    app: Flask, repo: FakeWalletRepository, amount: str
) -> None:
    """HU-08 CA-2, CA-5."""
    with pytest.raises(AmountOutOfRangeError) as excinfo:
        service.recharge(1, Decimal(amount), CTX, repo=repo)

    assert repo.wallets[1].balance == Decimal("0.00")
    assert excinfo.value.errors[0]["field"] == "amount"
    assert "5000.00" in excinfo.value.detail


def test_rejected_recharge_records_rejected_transaction_and_key_in_second_unit_of_work(
    app: Flask, repo: FakeWalletRepository
) -> None:
    """FR-006, FR-007, architecture.md 'Estados de una operación'."""
    with pytest.raises(AmountOutOfRangeError):
        service.recharge(1, Decimal("100.00"), CTX, repo=repo, request_id="abc123")

    assert [t.status for t in repo.transactions] == [TransactionStatus.RECHAZADA]
    assert repo.transactions[0].rejection_reason == "amount_out_of_range"
    assert repo.units_of_work == ["transaction:rechazada", "key:422"]
    assert repo.keys[0]["status_code"] == 422
    assert repo.keys[0]["body"]["code"] == "amount_out_of_range"
    assert repo.keys[0]["body"]["request_id"] == "abc123"


def test_create_wallet_starts_at_zero(app: Flask, repo: FakeWalletRepository) -> None:
    """HU-01 CA-2 (expuesto para accounts)."""
    wallet_id = service.create_wallet(5, repo=repo)

    assert repo.wallets[5].balance == Decimal("0.00")
    assert wallet_id == repo.wallets[5].id


def test_duplicate_key_race_is_reported_as_in_progress(
    app: Flask, repo: FakeWalletRepository
) -> None:
    """ADR-0005: dos peticiones con la misma clave compiten en el INSERT."""
    from sqlalchemy.exc import IntegrityError

    def boom(**_: object) -> None:
        raise IntegrityError("INSERT", {}, Exception("duplicate"))

    repo.add_idempotency_key = boom  # type: ignore[method-assign]

    with pytest.raises(service.DuplicateIdempotencyKeyError):
        service.recharge(1, Decimal("5000.00"), CTX, repo=repo)
