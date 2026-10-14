"""Reglas del historial sin base de datos (HU-09)."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest

from app.common.models.transaction import TransactionStatus, TransactionType
from app.modules.movements import service
from app.modules.movements.repository import MovementsFilter, MovementType
from app.modules.movements.service import Direction, InvalidDateRangeError
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
    filters: MovementsFilter | None = None,
) -> service.MovementsPage:
    return service.list_movements(
        7,
        page,
        filters or MovementsFilter(),
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


# --- HU-10: filtros -------------------------------------------------------------------

OTHER = 2


def _mixed_rows() -> list:  # type: ignore[type-arg]
    """Una fila de cada clase, ids 1..7, todas visibles para MY_WALLET salvo la 7."""
    transfer = TransactionType.TRANSFERENCIA
    rejected = TransactionStatus.RECHAZADA
    return [
        row(1, created_at=T0),  # recarga exitosa
        row(2, status=rejected, reason="amount_out_of_range", created_at=T0),  # recarga rechazada
        row(3, type_=transfer, sender=MY_WALLET, receiver=OTHER, created_at=T0),  # enviada
        row(
            4,
            type_=transfer,
            status=rejected,
            sender=MY_WALLET,
            receiver=OTHER,
            reason="insufficient_balance",
            created_at=T0,
        ),  # enviada rechazada
        row(5, type_=transfer, sender=OTHER, receiver=MY_WALLET, created_at=T0),  # recibida
        row(
            6,
            type_=transfer,
            status=rejected,
            sender=OTHER,
            receiver=MY_WALLET,
            reason="insufficient_balance",
            created_at=T0,
        ),  # recibida rechazada: nunca llegó
        row(7, receiver=OTHER, created_at=T0),  # recarga ajena
    ]


@pytest.mark.parametrize(
    ("type_", "expected"),
    [
        (MovementType.ALL, [5, 4, 3, 2, 1]),
        (MovementType.SENT, [4, 3]),
        (MovementType.RECEIVED, [5]),
        (MovementType.RECHARGE, [2, 1]),
    ],
)
def test_each_type_returns_only_its_own_movements(type_: MovementType, expected: list[int]) -> None:
    """HU-10 CA-3: cada tipo devuelve solo lo suyo, con total del resultado filtrado."""
    owners = FakeOwners({OTHER: owner(OTHER, 20, "3001112222")})

    page = _list(_mixed_rows(), owners=owners, filters=MovementsFilter(type_=type_))

    assert [m.id for m in page.items] == expected
    assert page.total == len(expected)


def test_default_filter_equals_the_unfiltered_history() -> None:
    """HU-10 CA-3: "all" es exactamente el historial de HU-09."""
    owners = FakeOwners({OTHER: owner(OTHER, 20, "3001112222")})
    rows = _mixed_rows()

    assert _list(rows, owners=owners) == _list(
        rows, owners=owners, filters=MovementsFilter(type_=MovementType.ALL)
    )


def test_date_range_is_inclusive_on_both_ends() -> None:
    """HU-10 CA-1: 00:00:00 del día inicial y 23:59:59 del final entran; los vecinos no."""
    rows = [
        row(1, created_at=datetime(2026, 10, 9, 23, 59, 59)),
        row(2, created_at=datetime(2026, 10, 10, 0, 0, 0)),
        row(3, created_at=datetime(2026, 10, 15, 12, 0, 0)),
        row(4, created_at=datetime(2026, 10, 20, 23, 59, 59)),
        row(5, created_at=datetime(2026, 10, 21, 0, 0, 0)),
    ]

    page = _list(rows, filters=MovementsFilter(from_=date(2026, 10, 10), to=date(2026, 10, 20)))

    assert [m.id for m in page.items] == [4, 3, 2]
    assert page.total == 3


def test_open_ended_ranges() -> None:
    """HU-10 CA-1: solo "desde" o solo "hasta"."""
    rows = [row(i, created_at=datetime(2026, 10, i, 12)) for i in (1, 15, 30)]

    since = _list(rows, filters=MovementsFilter(from_=date(2026, 10, 15)))
    until = _list(rows, filters=MovementsFilter(to=date(2026, 10, 15)))

    assert [m.id for m in since.items] == [30, 15]
    assert [m.id for m in until.items] == [15, 1]


def test_same_day_range_returns_that_day() -> None:
    """HU-10 CA-1 (spec US2 escenario 6): desde == hasta."""
    rows = [row(1, created_at=datetime(2026, 10, 14, 8)), row(2, created_at=datetime(2026, 10, 15))]
    day = date(2026, 10, 14)

    page = _list(rows, filters=MovementsFilter(from_=day, to=day))

    assert [m.id for m in page.items] == [1]


def test_date_and_type_filters_combine() -> None:
    """HU-10 CA-4: ambas condiciones a la vez."""
    rows = [
        row(1, created_at=datetime(2026, 10, 1, 12)),
        row(2, created_at=datetime(2026, 10, 15, 12)),
        row(
            3,
            type_=TransactionType.TRANSFERENCIA,
            sender=MY_WALLET,
            receiver=OTHER,
            created_at=datetime(2026, 10, 15, 13),
        ),
    ]
    filters = MovementsFilter(
        from_=date(2026, 10, 10), to=date(2026, 10, 20), type_=MovementType.RECHARGE
    )

    page = _list(rows, filters=filters, owners=FakeOwners())

    assert [m.id for m in page.items] == [2]


def test_filtered_results_keep_order_and_pages_of_twenty() -> None:
    """HU-10 CA-5: 45 coincidencias → 20, 20, 5 en orden descendente."""
    rows = [row(i, created_at=T0 + timedelta(seconds=i)) for i in range(1, 46)]
    rows += [row(100, type_=TransactionType.TRANSFERENCIA, sender=MY_WALLET, receiver=OTHER)]
    filters = MovementsFilter(type_=MovementType.RECHARGE)

    pages = [_list(rows, p, filters=filters, owners=FakeOwners()) for p in (1, 2, 3)]

    assert [len(p.items) for p in pages] == [20, 20, 5]
    assert all(p.total == 45 for p in pages)
    ids = [m.id for p in pages for m in p.items]
    assert ids == list(range(45, 0, -1))


def test_reversed_range_is_rejected_before_querying() -> None:
    """HU-10 CA-2, RNF-01.4: from > to → invalid_date_range sin tocar el repositorio."""
    repo = FakeMovementsRepository([row(1)])

    with pytest.raises(InvalidDateRangeError) as excinfo:
        service.list_movements(
            7,
            1,
            MovementsFilter(from_=date(2026, 12, 31), to=date(2026, 1, 1)),
            repo=repo,
            wallet_id_for=lambda _u: MY_WALLET,
            owners_for=FakeOwners(),
        )

    assert excinfo.value.code == "invalid_date_range"
    assert excinfo.value.status == 422
    assert excinfo.value.detail == "La fecha inicial no puede ser posterior a la final."
    assert repo.calls == []


def test_filter_log_has_type_and_range_flag_but_no_dates(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """FR-013, RNF-06.2: el log dice qué filtros, no los valores."""
    with caplog.at_level(logging.INFO, logger="app.movements"):
        _list([row(1)], filters=MovementsFilter(from_=date(2026, 10, 1), type_=MovementType.SENT))

    record = next(r for r in caplog.records if r.message == "movements.listed")
    assert record.type == "sent"  # type: ignore[attr-defined]
    assert record.date_range is True  # type: ignore[attr-defined]
    assert "2026-10-01" not in str(record.__dict__)
