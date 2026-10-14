"""HU-08 por HTTP contra MySQL con la sesión simulada por `logged_in_client`."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest
from flask import g
from flask.testing import FlaskClient
from sqlalchemy import select

from app.common.models.idempotency_key import IdempotencyKey
from app.common.models.transaction import Transaction, TransactionStatus
from app.extensions import db
from app.modules.wallet import service
from app.modules.wallet.models import Wallet
from tests.factories import SeededUser

URL = "/api/v1/wallet/recharges"
KEY_A = "00000000-0000-4000-8000-00000000000a"
KEY_B = "00000000-0000-4000-8000-00000000000b"

pytestmark = pytest.mark.mysql


def _post(client: FlaskClient, amount: Any, key: str | None = KEY_A, **extra: Any) -> Any:
    headers = {"X-Requested-With": "fetch"}
    if key is not None:
        headers["Idempotency-Key"] = key
    return client.post(URL, json={"amount": amount, **extra}, headers=headers)


def _balance(user_id: int) -> Decimal:
    db.session.expire_all()
    wallet = db.session.execute(select(Wallet).where(Wallet.user_id == user_id)).scalar_one()
    return Decimal(wallet.balance)


def _transactions() -> list[Transaction]:
    db.session.expire_all()
    return list(db.session.execute(select(Transaction).order_by(Transaction.id)).scalars())


def test_valid_recharges_increase_balance_and_are_recorded(
    logged_in_client: FlaskClient, seeded_users: list[SeededUser]
) -> None:
    """HU-08 CA-3, CA-4, RNF-05.1."""
    service.create_wallet(1)

    first = _post(logged_in_client, "50000.00", KEY_A)
    second = _post(logged_in_client, "20000.00", KEY_B)

    assert first.status_code == 201
    assert first.get_json()["balance_after"] == "50000.00"
    assert second.get_json()["balance_after"] == "70000.00"
    assert _balance(1) == Decimal("70000.00")
    assert [t.status for t in _transactions()] == [TransactionStatus.EXITOSA] * 2
    assert first.headers.get("Idempotent-Replayed") is None


def test_out_of_range_is_rejected_and_recorded_as_rechazada(
    logged_in_client: FlaskClient, seeded_users: list[SeededUser]
) -> None:
    """HU-08 CA-2, CA-5."""
    service.create_wallet(1)
    _post(logged_in_client, "10000.00", KEY_B)

    response = _post(logged_in_client, "4999.00", KEY_A)

    body = response.get_json()
    assert response.status_code == 422
    assert body["code"] == "amount_out_of_range"
    assert "5000.00" in body["errors"][0]["message"]
    assert "5000000.00" in body["errors"][0]["message"]
    assert _balance(1) == Decimal("10000.00")
    rejected = [t for t in _transactions() if t.status is TransactionStatus.RECHAZADA]
    assert len(rejected) == 1
    assert rejected[0].rejection_reason == "amount_out_of_range"


def test_format_error_creates_no_transaction(
    logged_in_client: FlaskClient, seeded_users: list[SeededUser]
) -> None:
    """HU-08 CA-2, CA-5."""
    service.create_wallet(1)

    response = _post(logged_in_client, "abc")

    assert response.status_code == 422
    assert response.get_json()["code"] == "validation"
    assert _transactions() == []
    assert _balance(1) == Decimal("0.00")


def test_same_key_and_body_is_replayed_once(
    logged_in_client: FlaskClient, seeded_users: list[SeededUser]
) -> None:
    """HU-08 CA-6, FR-007."""
    service.create_wallet(1)

    first = _post(logged_in_client, "20000.00", KEY_A)
    replay = _post(logged_in_client, "20000.00", KEY_A)

    assert (first.status_code, replay.status_code) == (201, 201)
    assert replay.headers["Idempotent-Replayed"] == "true"
    assert replay.get_json() == first.get_json()
    assert _balance(1) == Decimal("20000.00")
    assert len(_transactions()) == 1


def test_same_key_with_different_body_is_a_conflict(
    logged_in_client: FlaskClient, seeded_users: list[SeededUser]
) -> None:
    """HU-08 CA-6."""
    service.create_wallet(1)
    _post(logged_in_client, "20000.00", KEY_A)

    response = _post(logged_in_client, "30000.00", KEY_A)

    assert response.status_code == 422
    assert response.get_json()["code"] == "idempotency_key_mismatch"
    assert _balance(1) == Decimal("20000.00")


def test_rejected_recharge_is_replayed_as_the_same_problem(
    logged_in_client: FlaskClient, seeded_users: list[SeededUser]
) -> None:
    """ADR-0005: los rechazos también se reproducen."""
    service.create_wallet(1)
    first = _post(logged_in_client, "4999.00", KEY_A)

    replay = _post(logged_in_client, "4999.00", KEY_A)

    assert replay.status_code == first.status_code == 422
    assert replay.headers["Idempotent-Replayed"] == "true"
    assert replay.mimetype == "application/problem+json"
    assert len(_transactions()) == 1


def test_missing_key_is_rejected_before_touching_the_wallet(
    logged_in_client: FlaskClient, seeded_users: list[SeededUser]
) -> None:
    """HU-08 CA-6."""
    service.create_wallet(1)

    response = _post(logged_in_client, "5000.00", key=None)

    assert response.status_code == 400
    assert response.get_json()["code"] == "missing_idempotency_key"
    assert _transactions() == []


def test_without_session_is_rejected_and_nothing_is_written(
    client: FlaskClient, seeded_users: list[SeededUser]
) -> None:
    """RNF-01.1."""
    service.create_wallet(1)

    response = _post(client, "5000.00")

    assert response.status_code == 401
    assert response.get_json()["code"] == "unauthenticated"
    assert _transactions() == []


def test_user_id_in_body_is_rejected_and_other_wallet_untouched(
    logged_in_client: FlaskClient, seeded_users: list[SeededUser]
) -> None:
    """RNF-01.4, RNF-06.1."""
    service.create_wallet(1)
    service.create_wallet(2)

    response = _post(logged_in_client, "5000.00", user_id=2)

    assert response.status_code == 422
    assert response.get_json()["errors"][0]["field"] == "user_id"
    assert _balance(2) == Decimal("0.00")


def test_idempotency_key_rows_store_status_and_body(
    logged_in_client: FlaskClient, seeded_users: list[SeededUser]
) -> None:
    service.create_wallet(1)
    _post(logged_in_client, "5000.00", KEY_A)

    row = db.session.execute(select(IdempotencyKey)).scalar_one()

    assert row.user_id == 1
    assert row.status_code == 201
    assert row.response_body["balance_after"] == "5000.00"


def test_wallet_missing_returns_404_without_rows(
    logged_in_client: FlaskClient, seeded_users: list[SeededUser]
) -> None:
    response = _post(logged_in_client, "5000.00")

    assert response.status_code == 404
    assert response.get_json()["code"] == "wallet_not_found"
    assert g is not None


def test_real_login_cookie_authorizes_the_recharge(
    client: FlaskClient, seeded_users: list[SeededUser]
) -> None:
    """HU-02 + HU-08: la cookie de sesión real (sin g.user_id simulado) autoriza la recarga."""
    service.create_wallet(1)
    login = client.post(
        "/api/v1/auth/login",
        json={"phone": seeded_users[0].phone, "password": seeded_users[0].password},
        headers={"X-Requested-With": "fetch"},
    )
    assert login.status_code == 204

    response = _post(client, "5000.00")

    assert response.status_code == 201
    assert response.get_json()["balance_after"] == "5000.00"
    assert _balance(1) == Decimal("5000.00")
