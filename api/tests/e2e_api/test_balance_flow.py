"""HU-05 por HTTP contra MySQL: el saldo pertenece solo a la sesión autenticada."""

from __future__ import annotations

from decimal import Decimal

import pytest
from flask.testing import FlaskClient
from sqlalchemy import select

from app.extensions import db
from app.modules.wallet import service
from app.modules.wallet.models import Wallet
from tests.factories import SeededUser

URL = "/api/v1/wallet"
RECHARGE_KEY = "00000000-0000-4000-8000-000000000005"

pytestmark = pytest.mark.mysql


def _balance(user_id: int) -> Decimal:
    db.session.expire_all()
    wallet = db.session.execute(select(Wallet).where(Wallet.user_id == user_id)).scalar_one()
    return Decimal(wallet.balance)


def _recharge(client: FlaskClient, amount: str) -> None:
    response = client.post(
        f"{URL}/recharges",
        json={"amount": amount},
        headers={"X-Requested-With": "fetch", "Idempotency-Key": RECHARGE_KEY},
    )
    assert response.status_code == 201


def test_real_login_reads_its_persisted_balance_and_successful_recharge_updates_it(
    client: FlaskClient, seeded_users: list[SeededUser]
) -> None:
    """HU-05 CA-1, CA-2 y CA-3; la cookie real identifica al titular."""
    service.create_wallet(1)
    login = client.post(
        "/api/v1/auth/login",
        json={"phone": seeded_users[0].phone, "password": seeded_users[0].password},
        headers={"X-Requested-With": "fetch"},
    )
    assert login.status_code == 204

    initial = client.get(URL)
    _recharge(client, "5000.00")
    updated = client.get(URL)

    assert initial.get_json() == {"balance": "0.00"}
    assert updated.get_json() == {"balance": "5000.00"}
    assert _balance(1) == Decimal("5000.00")


def test_query_parameter_cannot_read_another_users_wallet(
    logged_in_client: FlaskClient, seeded_users: list[SeededUser]
) -> None:
    """HU-05 CA-4: el identificador procede únicamente de la sesión."""
    service.create_wallet(1)
    service.create_wallet(2)
    _recharge(logged_in_client, "5000.00")

    response = logged_in_client.get(f"{URL}?user_id=2")

    assert response.status_code == 200
    assert response.get_json() == {"balance": "5000.00"}
    assert _balance(2) == Decimal("0.00")


def test_without_session_is_unauthenticated(
    client: FlaskClient, seeded_users: list[SeededUser]
) -> None:
    response = client.get(URL)

    assert response.status_code == 401
    assert response.get_json()["code"] == "unauthenticated"


def test_without_wallet_returns_not_found(
    logged_in_client: FlaskClient, seeded_users: list[SeededUser]
) -> None:
    response = logged_in_client.get(URL)

    assert response.status_code == 404
    assert response.get_json()["code"] == "wallet_not_found"
