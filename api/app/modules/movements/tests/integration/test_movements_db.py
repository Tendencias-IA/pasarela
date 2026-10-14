"""Titularidad, enmascaramiento, orden estable y paginación contra MySQL real (HU-09)."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from flask import Flask

from app.common.models.transaction import TransactionStatus, TransactionType
from app.extensions import db
from app.modules.movements import service
from app.modules.movements.repository import MovementsFilter, SqlMovementsRepository
from app.modules.movements.schemas import MovementsPageOut
from app.modules.movements.service import Direction
from app.modules.wallet import service as wallet_service
from tests.factories import SeededUser, make_transaction

pytestmark = pytest.mark.mysql

T0 = datetime(2026, 10, 14, 12, 0, 0)


def _seed(rows: list) -> None:  # type: ignore[type-arg]
    db.session.add_all(rows)
    db.session.commit()


def _recharge(wallet: int, amount: str, at: datetime, ok: bool = True) -> object:
    return make_transaction(
        type_=TransactionType.RECARGA,
        status=TransactionStatus.EXITOSA if ok else TransactionStatus.RECHAZADA,
        amount=Decimal(amount),
        receiver_wallet_id=wallet,
        rejection_reason=None if ok else "amount_out_of_range",
        created_at=at,
    )


def _transfer(
    sender: int, receiver: int, amount: str, at: datetime, reason: str | None = None
) -> object:
    return make_transaction(
        type_=TransactionType.TRANSFERENCIA,
        status=TransactionStatus.RECHAZADA if reason else TransactionStatus.EXITOSA,
        amount=Decimal(amount),
        receiver_wallet_id=receiver,
        sender_wallet_id=sender,
        rejection_reason=reason,
        created_at=at,
    )


@pytest.fixture
def two_wallets(app: Flask, seeded_users: list[SeededUser]) -> tuple[int, int]:
    return wallet_service.create_wallet(1), wallet_service.create_wallet(2)


def test_each_user_sees_only_movements_of_their_wallet(
    two_wallets: tuple[int, int], seeded_users: list[SeededUser]
) -> None:
    """HU-09 CA-1, CA-5, FR-003, FR-006; RNF-06.1."""
    a, b = two_wallets
    _seed(
        [
            _recharge(a, "50000.00", T0),
            _recharge(a, "4999.00", T0 + timedelta(minutes=1), ok=False),
            _recharge(b, "70000.00", T0 + timedelta(minutes=2)),
            _transfer(a, b, "10000.00", T0 + timedelta(minutes=3)),
            _transfer(a, b, "999999.00", T0 + timedelta(minutes=4), reason="insufficient_balance"),
            _transfer(b, a, "5000.00", T0 + timedelta(minutes=5)),
        ]
    )

    mine = service.list_movements(1, 1)
    theirs = service.list_movements(2, 1)

    assert mine.total == 5
    assert [m.direction for m in mine.items] == [
        Direction.RECIBIDA,
        Direction.ENVIADA,
        Direction.ENVIADA,
        Direction.RECARGA,
        Direction.RECARGA,
    ]
    assert mine.items[1].status is TransactionStatus.RECHAZADA
    assert mine.items[1].rejection_reason == "insufficient_balance"
    assert theirs.total == 3
    assert [m.direction for m in theirs.items] == [
        Direction.ENVIADA,
        Direction.RECIBIDA,
        Direction.RECARGA,
    ]
    assert all(m.status is TransactionStatus.EXITOSA for m in theirs.items)


def test_counterparty_is_masked_and_never_leaks_full_phone(
    two_wallets: tuple[int, int], seeded_users: list[SeededUser]
) -> None:
    """HU-09 CA-3, FR-004, SC-002."""
    a, b = two_wallets
    _seed([_transfer(a, b, "10000.00", T0), _transfer(b, a, "5000.00", T0 + timedelta(minutes=1))])

    page = service.list_movements(1, 1)
    body = json.dumps(MovementsPageOut.from_page(page).model_dump())

    received, sent = page.items
    other_phone = seeded_users[1].phone
    assert sent.counterparty == service.Counterparty(
        name_masked=None, phone_masked="***" + other_phone[-4:]
    )
    assert received.counterparty is not None
    assert received.counterparty.phone_masked == "***" + other_phone[-4:]
    assert other_phone not in body
    assert seeded_users[0].phone not in body


def test_forty_five_movements_paginate_without_gaps_or_duplicates(
    two_wallets: tuple[int, int],
) -> None:
    """HU-09 CA-4, CA-6, SC-003: 20 + 20 + 5, orden estable por (created_at, id)."""
    a, _ = two_wallets
    rows = [_recharge(a, "5000.00", T0 + timedelta(seconds=i)) for i in range(42)]
    rows += [_recharge(a, "6000.00", T0 + timedelta(seconds=100)) for _ in range(3)]
    _seed(rows)

    pages = [service.list_movements(1, p) for p in (1, 2, 3)]

    sizes = [len(p.items) for p in pages]
    assert sizes == [20, 20, 5]
    assert all(p.total == 45 for p in pages)
    ids = [m.id for p in pages for m in p.items]
    assert len(set(ids)) == 45
    keys = [(m.created_at, m.id) for p in pages for m in p.items]
    assert keys == sorted(keys, reverse=True)
    assert service.list_movements(1, 9).items == []
    assert SqlMovementsRepository().count_for_wallet(a, MovementsFilter()) == 45


def test_user_without_movements_or_wallet_gets_empty_page(
    app: Flask, seeded_users: list[SeededUser], caplog: pytest.LogCaptureFixture
) -> None:
    """HU-09 CA-7 y edge case sin billetera."""
    wallet_service.create_wallet(1)

    with_wallet = service.list_movements(1, 1)
    with caplog.at_level(logging.WARNING, logger="app.movements"):
        without_wallet = service.list_movements(2, 1)

    assert (with_wallet.items, with_wallet.total) == ([], 0)
    assert (without_wallet.items, without_wallet.total) == ([], 0)
    assert any(r.message == "movements.wallet_missing" for r in caplog.records)
    assert wallet_service.get_wallet_id(2) is None
