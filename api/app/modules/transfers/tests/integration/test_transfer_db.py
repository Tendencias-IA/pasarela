"""Atomicidad, bloqueo, concurrencia e idempotencia de HU-07 contra MySQL real."""

from __future__ import annotations

import threading
from decimal import Decimal

import pytest
from flask import Flask
from pytest_mock import MockerFixture
from sqlalchemy import event, select

from app.common.errors import AppError
from app.common.idempotency import IdempotencyContext
from app.common.models.idempotency_key import IdempotencyKey
from app.common.models.transaction import Transaction, TransactionStatus
from app.extensions import db
from app.modules.transfers import service
from app.modules.transfers.repository import SqlTransfersRepository
from app.modules.wallet import service as wallet_service
from app.modules.wallet.models import Wallet
from tests.factories import SeededUser

pytestmark = pytest.mark.mysql


def ctx(n: int) -> IdempotencyContext:
    return IdempotencyContext(key=f"00000000-0000-4000-8000-{n:012d}", request_hash=f"{n:064d}")


@pytest.fixture
def funded(app: Flask, seeded_users: list[SeededUser]) -> list[SeededUser]:
    """Billeteras de 1 y 2; el usuario 1 parte con 100.000,00 y el 2 con 0,00."""
    wallet_service.create_wallet(1)
    wallet_service.create_wallet(2)
    wallet = db.session.execute(select(Wallet).where(Wallet.user_id == 1)).scalar_one()
    wallet.balance = Decimal("100000.00")
    db.session.commit()
    return seeded_users


def balance(user_id: int) -> Decimal:
    db.session.expire_all()
    return Decimal(
        db.session.execute(select(Wallet.balance).where(Wallet.user_id == user_id)).scalar_one()
    )


def transactions() -> list[Transaction]:
    db.session.expire_all()
    return list(db.session.execute(select(Transaction).order_by(Transaction.id)).scalars())


def keys() -> list[IdempotencyKey]:
    db.session.expire_all()
    return list(db.session.execute(select(IdempotencyKey)).scalars())


def test_success_moves_money_and_writes_movement_and_key_together(funded: list[SeededUser]) -> None:
    """HU-07 CA-3, CA-5, CA-8."""
    result = service.confirm_transfer(1, funded[1].phone, Decimal("40000.00"), ctx(1))

    assert result.balance_after == Decimal("60000.00")
    assert (balance(1), balance(2)) == (Decimal("60000.00"), Decimal("40000.00"))
    [movement] = transactions()
    assert movement.status is TransactionStatus.EXITOSA
    assert (movement.sender_wallet_id, movement.receiver_wallet_id) == (1, 2)
    [key] = keys()
    assert key.status_code == 201 and key.response_body["id"] == movement.id


def test_failure_after_debit_rolls_back_both_balances(
    funded: list[SeededUser], mocker: MockerFixture
) -> None:
    """HU-07 CA-4, RNF-04.1: un fallo tras débito y crédito no deja ningún cambio."""
    mocker.patch.object(
        SqlTransfersRepository, "add_transaction", side_effect=RuntimeError("caída simulada")
    )

    with pytest.raises(RuntimeError):
        service.confirm_transfer(1, funded[1].phone, Decimal("40000.00"), ctx(1))

    assert (balance(1), balance(2)) == (Decimal("100000.00"), Decimal("0.00"))
    assert transactions() == [] and keys() == []


def test_failure_storing_the_key_rolls_back_the_transfer(
    funded: list[SeededUser], mocker: MockerFixture
) -> None:
    """ADR-0005: no puede quedar movimiento sin clave."""
    mocker.patch.object(
        SqlTransfersRepository, "add_idempotency_key", side_effect=RuntimeError("caída simulada")
    )

    with pytest.raises(RuntimeError):
        service.confirm_transfer(1, funded[1].phone, Decimal("40000.00"), ctx(1))

    assert (balance(1), balance(2)) == (Decimal("100000.00"), Decimal("0.00"))
    assert transactions() == []


def test_wallets_are_locked_in_ascending_id_order_with_for_update(
    funded: list[SeededUser],
) -> None:
    """RNF-04.2: el emisor tiene el id mayor y aun así se pide el bloqueo en orden de id."""
    statements: list[str] = []

    def capture(conn: object, cursor: object, statement: str, *args: object) -> None:
        statements.append(" ".join(statement.split()).upper())

    event.listen(db.engine, "before_cursor_execute", capture)
    try:
        service.confirm_transfer(2, funded[0].phone, Decimal("100.00"), ctx(1))
    except wallet_service.InsufficientBalanceError:
        pass
    finally:
        event.remove(db.engine, "before_cursor_execute", capture)

    locking = [s for s in statements if "FOR UPDATE" in s and "FROM WALLETS" in s]
    assert len(locking) == 1
    assert "ORDER BY WALLETS.ID" in locking[0]


def test_insufficient_balance_records_a_rejected_movement_and_the_key(
    funded: list[SeededUser],
) -> None:
    """HU-07 CA-2, CA-6: saldos intactos, fila rechazada y clave con el problem."""
    with pytest.raises(wallet_service.InsufficientBalanceError):
        service.confirm_transfer(1, funded[1].phone, Decimal("100000.01"), ctx(1))

    assert (balance(1), balance(2)) == (Decimal("100000.00"), Decimal("0.00"))
    [movement] = transactions()
    assert movement.status is TransactionStatus.RECHAZADA
    assert movement.rejection_reason == "insufficient_balance"
    assert (movement.sender_wallet_id, movement.receiver_wallet_id) == (1, 2)
    [key] = keys()
    assert key.status_code == 422 and key.response_body["code"] == "insufficient_balance"


def test_unknown_recipient_stores_only_the_key(funded: list[SeededUser]) -> None:
    """HU-07 CA-2: sin billetera receptora no hay fila (receiver_wallet_id es NOT NULL)."""
    with pytest.raises(service.RecipientNotFoundError):
        service.confirm_transfer(1, "3999999999", Decimal("1000.00"), ctx(1))

    assert transactions() == []
    [key] = keys()
    assert key.status_code == 404 and key.response_body["code"] == "recipient_not_found"


def _run_in_threads(app: Flask, jobs: list[tuple[int, str, IdempotencyContext]]) -> list[object]:
    barrier = threading.Barrier(len(jobs))
    outcomes: list[object] = []

    def attempt(user_id: int, phone: str, context: IdempotencyContext) -> None:
        with app.app_context():
            barrier.wait()
            try:
                service.confirm_transfer(user_id, phone, Decimal("100000.00"), context)
                outcomes.append("applied")
            except AppError as exc:
                outcomes.append(exc)
            finally:
                db.session.remove()

    threads = [threading.Thread(target=attempt, args=job) for job in jobs]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return outcomes


def test_two_simultaneous_transfers_of_the_whole_balance_only_one_passes(
    app: Flask, funded: list[SeededUser]
) -> None:
    """HU-07 CA-9, RNF-04.2: exactamente una pasa y el saldo nunca queda negativo."""
    outcomes = _run_in_threads(app, [(1, funded[1].phone, ctx(1)), (1, funded[1].phone, ctx(2))])

    assert outcomes.count("applied") == 1
    [rejected] = [o for o in outcomes if isinstance(o, wallet_service.InsufficientBalanceError)]
    assert rejected.code == "insufficient_balance"
    assert (balance(1), balance(2)) == (Decimal("0.00"), Decimal("100000.00"))
    assert sorted(t.status.value for t in transactions()) == ["exitosa", "rechazada"]


def test_crossed_transfers_do_not_deadlock_and_conserve_money(
    app: Flask, funded: list[SeededUser]
) -> None:
    """RNF-04.2: 1→2 y 2→1 a la vez piden los bloqueos en el mismo orden."""
    first = db.session.execute(select(Wallet).where(Wallet.user_id == 2)).scalar_one()
    first.balance = Decimal("100000.00")
    db.session.commit()

    outcomes = _run_in_threads(app, [(1, funded[1].phone, ctx(1)), (2, funded[0].phone, ctx(2))])

    assert outcomes == ["applied", "applied"]
    assert balance(1) + balance(2) == Decimal("200000.00")
    assert balance(1) == balance(2) == Decimal("100000.00")


def test_same_key_in_parallel_applies_once(app: Flask, funded: list[SeededUser]) -> None:
    """HU-07 CA-8: la misma clave en paralelo produce un solo movimiento."""
    barrier = threading.Barrier(2)
    outcomes: list[str] = []

    def attempt() -> None:
        with app.app_context():
            barrier.wait()
            try:
                service.confirm_transfer(1, funded[1].phone, Decimal("30000.00"), ctx(1))
                outcomes.append("applied")
            except wallet_service.DuplicateIdempotencyKeyError:
                outcomes.append("duplicate")
            finally:
                db.session.remove()

    threads = [threading.Thread(target=attempt) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sorted(outcomes) == ["applied", "duplicate"]
    assert (balance(1), balance(2)) == (Decimal("70000.00"), Decimal("30000.00"))
    assert len(transactions()) == 1
