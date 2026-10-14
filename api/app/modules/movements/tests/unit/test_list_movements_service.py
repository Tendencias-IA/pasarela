"""Reglas del historial sin base de datos (HU-09)."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from app.common.models.transaction import TransactionStatus, TransactionType
from app.modules.movements import service
from app.modules.movements.service import Direction
from app.modules.movements.tests.unit.fakes import (
    FakeMovementsRepository,
    FakeOwners,
    owner,
    row,
)

T0 = datetime(2026, 10, 14, 21, 40, 0)
MY_WALLET = 1


def _list(
    rows: list,  # type: ignore[type-arg]
    page: int = 1,
    *,
    wallet_id: int | None = MY_WALLET,
    owners: FakeOwners | None = None,
) -> service.MovementsPage:
    return service.list_movements(
        7,
        page,
        repo=FakeMovementsRepository(rows),
        wallet_id_for=lambda _user_id: wallet_id,
        owners_for=owners or FakeOwners(),
    )


def test_recharges_are_listed_with_status_and_reason() -> None:
    """HU-09 CA-1, CA-2: recargas exitosas y rechazadas con su estado."""
    rows = [
        row(1, amount="50000.00", created_at=T0),
        row(
            2,
            status=TransactionStatus.RECHAZADA,
            amount="4999.00",
            reason="amount_out_of_range",
            created_at=T0 + timedelta(seconds=1),
        ),
    ]

    page = _list(rows)

    assert [m.id for m in page.items] == [2, 1]
    rejected, ok = page.items
    assert rejected.direction is Direction.RECARGA
    assert rejected.status is TransactionStatus.RECHAZADA
    assert rejected.rejection_reason == "amount_out_of_range"
    assert rejected.amount == Decimal("4999.00")
    assert ok.status is TransactionStatus.EXITOSA
    assert ok.rejection_reason is None
    assert ok.counterparty is None
    assert page.total == 2
    assert page.page_size == 20


def test_order_is_newest_first_with_id_tiebreak() -> None:
    """HU-09 CA-4, FR-005: orden descendente y desempate estable por id."""
    rows = [row(1, created_at=T0), row(2, created_at=T0), row(3, created_at=T0 - timedelta(days=1))]

    page = _list(rows)

    assert [m.id for m in page.items] == [2, 1, 3]


def test_transfer_direction_depends_on_wallet_role() -> None:
    """HU-09 CA-1, FR-003: enviada si soy sender, recibida si soy receiver."""
    rows = [
        row(1, type_=TransactionType.TRANSFERENCIA, sender=MY_WALLET, receiver=2, created_at=T0),
        row(
            2,
            type_=TransactionType.TRANSFERENCIA,
            sender=3,
            receiver=MY_WALLET,
            created_at=T0 + timedelta(seconds=1),
        ),
    ]
    owners = FakeOwners(
        {2: owner(2, 20, "3001112222"), 3: owner(3, 30, "3003334444", "Maria Garcia")}
    )

    page = _list(rows, owners=owners)

    received, sent = page.items
    assert sent.direction is Direction.ENVIADA
    assert sent.counterparty is not None
    assert sent.counterparty.phone_masked == "***2222"
    assert sent.counterparty.name_masked is None
    assert received.direction is Direction.RECIBIDA
    assert received.counterparty is not None
    assert received.counterparty.name_masked == "Mar** G*****"
    assert received.counterparty.phone_masked == "***4444"


def test_amounts_stay_decimal_in_the_domain() -> None:
    """RNF-04.3."""
    page = _list([row(1, amount="120500.50")])

    assert isinstance(page.items[0].amount, Decimal)
    assert page.items[0].amount == Decimal("120500.50")


def test_owners_are_resolved_once_per_page_without_my_wallet() -> None:
    """research §1: una sola llamada con las billeteras ajenas, sin duplicados ni la propia."""
    rows = [
        row(1, type_=TransactionType.TRANSFERENCIA, sender=MY_WALLET, receiver=2, created_at=T0),
        row(2, type_=TransactionType.TRANSFERENCIA, sender=2, receiver=MY_WALLET, created_at=T0),
        row(3, type_=TransactionType.TRANSFERENCIA, sender=MY_WALLET, receiver=3, created_at=T0),
        row(4, created_at=T0),
    ]
    owners = FakeOwners({2: owner(2, 20, "3001112222"), 3: owner(3, 30, "3003334444")})

    _list(rows, owners=owners)

    assert owners.calls == [{2, 3}]


def test_owners_are_not_resolved_when_page_has_only_recharges() -> None:
    owners = FakeOwners()

    _list([row(1), row(2)], owners=owners)

    assert owners.calls == []


def test_missing_owner_is_masked_as_unknown() -> None:
    """Edge case: contraparte inconsistente → '***' sin fallar (RNF-06.1)."""
    rows = [row(1, type_=TransactionType.TRANSFERENCIA, sender=MY_WALLET, receiver=9)]

    page = _list(rows, owners=FakeOwners({}))

    assert page.items[0].counterparty is not None
    assert page.items[0].counterparty.phone_masked == "***"
    assert page.items[0].counterparty.name_masked is None


def test_pagination_is_fixed_at_twenty() -> None:
    """HU-09 CA-6, FR-007, FR-009: 45 filas → 20, 20, 5; página 9 vacía con total 45."""
    rows = [row(i, created_at=T0 + timedelta(seconds=i)) for i in range(1, 46)]

    first, third, beyond = _list(rows, 1), _list(rows, 3), _list(rows, 9)

    assert [m.id for m in first.items] == list(range(45, 25, -1))
    assert (first.page, first.page_size, first.total) == (1, 20, 45)
    assert [m.id for m in third.items] == [5, 4, 3, 2, 1]
    assert beyond.items == [] and beyond.total == 45 and beyond.page == 9


def test_user_without_wallet_gets_empty_page_and_warning(caplog: pytest.LogCaptureFixture) -> None:
    """HU-09 CA-7 y edge case: sin billetera → vacío, sin crearla, con WARNING."""
    with caplog.at_level(logging.WARNING, logger="app.movements"):
        page = _list([row(1)], wallet_id=None)

    assert page.items == [] and page.total == 0
    assert any(r.message == "movements.wallet_missing" for r in caplog.records)


def test_user_with_wallet_and_no_movements_gets_empty_page() -> None:
    """HU-09 CA-7."""
    page = _list([])

    assert page.items == [] and page.total == 0 and page.page == 1


def test_rejected_transfer_is_visible_only_to_the_sender() -> None:
    """HU-09 CA-1, CA-5 (edge case): la billetera destino nunca la recibió."""
    rows = [
        row(
            1,
            type_=TransactionType.TRANSFERENCIA,
            status=TransactionStatus.RECHAZADA,
            sender=2,
            receiver=MY_WALLET,
            reason="insufficient_balance",
            created_at=T0,
        ),
        row(
            2,
            type_=TransactionType.TRANSFERENCIA,
            status=TransactionStatus.RECHAZADA,
            sender=MY_WALLET,
            receiver=2,
            reason="insufficient_balance",
            created_at=T0,
        ),
    ]

    page = _list(rows, owners=FakeOwners({2: owner(2, 20, "3001112222")}))

    assert [m.id for m in page.items] == [2]
    assert page.items[0].direction is Direction.ENVIADA
