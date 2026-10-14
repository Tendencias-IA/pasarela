"""Filtros del historial contra MySQL real (HU-10)."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from flask import Flask

from app.common.models.transaction import Transaction, TransactionStatus, TransactionType
from app.extensions import db
from app.modules.movements import service
from app.modules.movements.repository import MovementsFilter, MovementType, SqlMovementsRepository
from app.modules.wallet import service as wallet_service
from tests.factories import SeededUser, make_transaction

pytestmark = pytest.mark.mysql

DAY1 = datetime(2026, 10, 10, 0, 0, 0)  # primer segundo del día
DAY2 = datetime(2026, 10, 15, 12, 0, 0)
DAY3 = datetime(2026, 10, 20, 23, 59, 59)  # último segundo del día


def _seed(rows: list[Transaction]) -> None:
    db.session.add_all(rows)
    db.session.commit()


def _tx(
    type_: TransactionType,
    at: datetime,
    *,
    receiver: int,
    sender: int | None = None,
    ok: bool = True,
) -> Transaction:
    return make_transaction(
        type_=type_,
        status=TransactionStatus.EXITOSA if ok else TransactionStatus.RECHAZADA,
        amount=Decimal("10000.00"),
        receiver_wallet_id=receiver,
        sender_wallet_id=sender,
        rejection_reason=None if ok else "insufficient_balance",
        created_at=at,
    )


@pytest.fixture
def seeded(app: Flask, seeded_users: list[SeededUser]) -> dict[str, list[int]]:
    """A (billetera 1) y B (billetera 2) con una fila de cada clase; devuelve ids por clase."""
    a, b = wallet_service.create_wallet(1), wallet_service.create_wallet(2)
    t, r = TransactionType.TRANSFERENCIA, TransactionType.RECARGA
    rows = {
        "recharge_ok": _tx(r, DAY1, receiver=a),
        "recharge_rejected": _tx(r, DAY2, receiver=a, ok=False),
        "sent_ok": _tx(t, DAY2, receiver=b, sender=a),
        "sent_rejected": _tx(t, DAY3, receiver=b, sender=a, ok=False),
        "received_ok": _tx(t, DAY3, receiver=a, sender=b),
        "received_rejected": _tx(t, DAY3, receiver=a, sender=b, ok=False),  # B la intentó
        "foreign_recharge": _tx(r, DAY2, receiver=b),
    }
    _seed(list(rows.values()))
    return {name: [row.id] for name, row in rows.items()}


def _ids(page: service.MovementsPage) -> set[int]:
    return {m.id for m in page.items}


@pytest.mark.parametrize(
    ("type_", "names"),
    [
        (
            MovementType.ALL,
            {"recharge_ok", "recharge_rejected", "sent_ok", "sent_rejected", "received_ok"},
        ),
        (MovementType.SENT, {"sent_ok", "sent_rejected"}),
        (MovementType.RECEIVED, {"received_ok"}),
        (MovementType.RECHARGE, {"recharge_ok", "recharge_rejected"}),
    ],
)
def test_each_type_returns_only_its_own_rows(
    seeded: dict[str, list[int]], type_: MovementType, names: set[str]
) -> None:
    """HU-10 CA-3, SC-001: cada tipo devuelve solo lo suyo y el total coincide."""
    page = service.list_movements(1, 1, MovementsFilter(type_=type_))

    assert _ids(page) == {seeded[n][0] for n in names}
    assert page.total == len(names)


def test_other_user_sees_the_mirror_image(seeded: dict[str, list[int]]) -> None:
    """HU-10 CA-3, HU-09 CA-5: B recibe lo que A envió con éxito, sin lo rechazado."""
    received = service.list_movements(2, 1, MovementsFilter(type_=MovementType.RECEIVED))
    sent = service.list_movements(2, 1, MovementsFilter(type_=MovementType.SENT))

    assert _ids(received) == {seeded["sent_ok"][0]}
    assert _ids(sent) == {seeded["received_ok"][0], seeded["received_rejected"][0]}


def test_date_range_is_inclusive_at_both_ends(seeded: dict[str, list[int]]) -> None:
    """HU-10 CA-1, SC-002: 00:00:00 del primer día y 23:59:59 del último entran."""
    page = service.list_movements(
        1, 1, MovementsFilter(from_=date(2026, 10, 10), to=date(2026, 10, 20))
    )

    assert page.total == 5


def test_range_excludes_neighbouring_days(seeded: dict[str, list[int]]) -> None:
    """HU-10 CA-1."""
    only_first = service.list_movements(1, 1, MovementsFilter(to=date(2026, 10, 10)))
    middle = service.list_movements(
        1, 1, MovementsFilter(from_=date(2026, 10, 11), to=date(2026, 10, 19))
    )
    after = service.list_movements(1, 1, MovementsFilter(from_=date(2026, 10, 21)))

    assert _ids(only_first) == {seeded["recharge_ok"][0]}
    assert _ids(middle) == {seeded["recharge_rejected"][0], seeded["sent_ok"][0]}
    assert after.items == [] and after.total == 0


def test_single_end_ranges(seeded: dict[str, list[int]]) -> None:
    """HU-10 CA-1: solo desde / solo hasta."""
    since = service.list_movements(1, 1, MovementsFilter(from_=date(2026, 10, 20)))

    assert _ids(since) == {seeded["sent_rejected"][0], seeded["received_ok"][0]}


def test_date_and_type_combine(seeded: dict[str, list[int]]) -> None:
    """HU-10 CA-4."""
    page = service.list_movements(
        1,
        1,
        MovementsFilter(
            from_=date(2026, 10, 15), to=date(2026, 10, 15), type_=MovementType.RECHARGE
        ),
    )

    assert _ids(page) == {seeded["recharge_rejected"][0]}
    assert page.total == 1


def test_filtered_pagination_keeps_order_and_pages_of_twenty(
    app: Flask, seeded_users: list[SeededUser]
) -> None:
    """HU-10 CA-5, SC-003: 45 coincidencias → 20, 20, 5 sin repetidos, descendentes."""
    a, b = wallet_service.create_wallet(1), wallet_service.create_wallet(2)
    base = datetime(2026, 10, 14, 12, 0, 0)
    rows = [
        _tx(TransactionType.RECARGA, base + timedelta(seconds=i), receiver=a) for i in range(42)
    ]
    rows += [
        _tx(TransactionType.RECARGA, base + timedelta(seconds=100), receiver=a) for _ in range(3)
    ]
    rows += [_tx(TransactionType.TRANSFERENCIA, base, receiver=b, sender=a) for _ in range(7)]
    _seed(rows)
    filters = MovementsFilter(
        from_=date(2026, 10, 14), to=date(2026, 10, 14), type_=MovementType.RECHARGE
    )

    pages = [service.list_movements(1, p, filters) for p in (1, 2, 3)]

    assert [len(p.items) for p in pages] == [20, 20, 5]
    assert all(p.total == 45 for p in pages)
    keys = [(m.created_at, m.id) for p in pages for m in p.items]
    assert len(set(keys)) == 45 and keys == sorted(keys, reverse=True)
    assert SqlMovementsRepository().count_for_wallet(a, filters) == 45


def test_reversed_range_is_rejected(seeded: dict[str, list[int]]) -> None:
    """HU-10 CA-2."""
    with pytest.raises(service.InvalidDateRangeError):
        service.list_movements(1, 1, MovementsFilter(from_=date(2026, 12, 1), to=date(2026, 1, 1)))
