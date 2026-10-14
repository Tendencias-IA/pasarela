"""Atomicidad, bloqueo e idempotencia contra MySQL real (RNF-04, ADR-0005)."""

from __future__ import annotations

import threading
from decimal import Decimal

import pytest
from flask import Flask
from pytest_mock import MockerFixture
from sqlalchemy import event, select

from app.common.errors import AppError
from app.common.idempotency import IdempotencyContext
from app.common.models.transaction import Transaction
from app.extensions import db
from app.modules.wallet import service
from app.modules.wallet.models import Wallet
from app.modules.wallet.repository import SqlWalletRepository
from tests.factories import SeededUser

pytestmark = pytest.mark.mysql

CTX_A = IdempotencyContext(key="00000000-0000-4000-8000-0000000000a1", request_hash="a" * 64)
CTX_B = IdempotencyContext(key="00000000-0000-4000-8000-0000000000b2", request_hash="b" * 64)


def _balance(user_id: int) -> Decimal:
    db.session.expire_all()
    wallet = db.session.execute(select(Wallet).where(Wallet.user_id == user_id)).scalar_one()
    return Decimal(wallet.balance)


def _count_transactions() -> int:
    db.session.expire_all()
    return len(list(db.session.execute(select(Transaction)).scalars()))


def test_concurrent_distinct_keys_apply_both(app: Flask, seeded_users: list[SeededUser]) -> None:
    """RNF-04.2: dos recargas simultáneas del mismo usuario suman."""
    service.create_wallet(1)
    barrier = threading.Barrier(2)
    errors: list[BaseException] = []

    def attempt(ctx: IdempotencyContext) -> None:
        with app.app_context():
            barrier.wait()
            try:
                service.recharge(1, Decimal("10000.00"), ctx)
            except BaseException as exc:  # noqa: BLE001 (se reporta en la aserción)
                errors.append(exc)
            finally:
                db.session.remove()

    threads = [threading.Thread(target=attempt, args=(c,)) for c in (CTX_A, CTX_B)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
    assert _balance(1) == Decimal("20000.00")
    assert _count_transactions() == 2


def test_concurrent_same_key_applies_once(app: Flask, seeded_users: list[SeededUser]) -> None:
    """HU-08 CA-6: la misma clave en paralelo acredita una sola vez."""
    service.create_wallet(1)
    barrier = threading.Barrier(2)
    outcomes: list[str] = []

    def attempt() -> None:
        with app.app_context():
            barrier.wait()
            try:
                service.recharge(1, Decimal("10000.00"), CTX_A)
                outcomes.append("applied")
            except service.DuplicateIdempotencyKeyError:
                outcomes.append("duplicate")
            finally:
                db.session.remove()

    threads = [threading.Thread(target=attempt) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sorted(outcomes) == ["applied", "duplicate"]
    assert _balance(1) == Decimal("10000.00")
    assert _count_transactions() == 1


def test_failure_after_update_rolls_back_everything(
    app: Flask, seeded_users: list[SeededUser], mocker: MockerFixture
) -> None:
    """RNF-04.5, FR-006: si falla guardar la clave, ni saldo ni movimiento quedan."""
    service.create_wallet(1)
    mocker.patch.object(
        SqlWalletRepository, "add_idempotency_key", side_effect=RuntimeError("caída simulada")
    )

    with pytest.raises(RuntimeError):
        service.recharge(1, Decimal("10000.00"), CTX_A)

    assert _balance(1) == Decimal("0.00")
    assert _count_transactions() == 0


def test_lock_wallet_uses_for_update(app: Flask, seeded_users: list[SeededUser]) -> None:
    """RNF-04.2: la billetera se bloquea con SELECT ... FOR UPDATE."""
    service.create_wallet(1)
    statements: list[str] = []

    def capture(conn: object, cursor: object, statement: str, *args: object) -> None:
        statements.append(statement)

    event.listen(db.engine, "before_cursor_execute", capture)
    try:
        service.recharge(1, Decimal("10000.00"), CTX_A)
    finally:
        event.remove(db.engine, "before_cursor_execute", capture)

    assert any("FOR UPDATE" in s.upper() and "wallets" in s for s in statements)


def test_business_rejection_keeps_balance_and_records_rejected_row(
    app: Flask, seeded_users: list[SeededUser]
) -> None:
    """HU-08 CA-5 en base de datos real."""
    service.create_wallet(1)

    with pytest.raises(AppError):
        service.recharge(1, Decimal("1.00"), CTX_A)

    assert _balance(1) == Decimal("0.00")
    assert _count_transactions() == 1


def test_expired_key_is_forgotten_and_deleted(app: Flask, seeded_users: list[SeededUser]) -> None:
    """ADR-0005: una clave de más de 24 h es una solicitud nueva (limpieza perezosa)."""
    from datetime import timedelta

    from app.common import idempotency
    from app.common.clock import utcnow
    from app.common.models.idempotency_key import IdempotencyKey

    service.create_wallet(1)
    service.recharge(1, Decimal("10000.00"), CTX_A)
    row = db.session.get(IdempotencyKey, (1, CTX_A.key))
    assert row is not None
    row.created_at = utcnow() - idempotency.IDEMPOTENCY_TTL - timedelta(seconds=1)
    db.session.commit()

    assert idempotency.find_existing(1, CTX_A.key) is None
    db.session.expire_all()
    assert db.session.get(IdempotencyKey, (1, CTX_A.key)) is None

    # La misma clave vuelve a acreditar: es una solicitud nueva.
    service.recharge(1, Decimal("10000.00"), CTX_A)
    assert _balance(1) == Decimal("20000.00")
    assert idempotency.find_existing(1, CTX_A.key) is not None


def test_fresh_key_is_kept(app: Flask, seeded_users: list[SeededUser]) -> None:
    from app.common import idempotency

    service.create_wallet(1)
    service.recharge(1, Decimal("10000.00"), CTX_A)

    stored = idempotency.find_existing(1, CTX_A.key)
    assert stored is not None
    assert stored.status_code == 201
