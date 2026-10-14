"""HU-06 por HTTP contra MySQL: preparar no escribe nada y enmascara al destinatario."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Any

import pytest
from flask.testing import FlaskClient
from sqlalchemy import func, select

from app.common.models.idempotency_key import IdempotencyKey
from app.common.models.transaction import Transaction
from app.extensions import db
from app.modules.wallet import service as wallet_service
from app.modules.wallet.models import Wallet
from tests.factories import SeededUser

URL = "/api/v1/transfers/preview"
HEADERS = {"X-Requested-With": "fetch"}

pytestmark = pytest.mark.mysql


@pytest.fixture
def funded(seeded_users: list[SeededUser]) -> list[SeededUser]:
    """Billeteras de los usuarios 1 (500.000) y 2 (0), sembradas sin sesión HTTP."""
    wallet_service.create_wallet(1)
    wallet_service.create_wallet(2)
    wallet = db.session.execute(select(Wallet).where(Wallet.user_id == 1)).scalar_one()
    wallet.balance = Decimal("500000.00")
    db.session.commit()
    return seeded_users


def _preview(client: FlaskClient, phone: str, amount: Any) -> Any:
    return client.post(URL, json={"recipient_phone": phone, "amount": amount}, headers=HEADERS)


def _snapshot() -> tuple[list[Decimal], int, int]:
    db.session.expire_all()
    balances = [
        Decimal(b) for b in db.session.execute(select(Wallet.balance).order_by(Wallet.id)).scalars()
    ]
    transactions = db.session.execute(select(func.count()).select_from(Transaction)).scalar_one()
    keys = db.session.execute(select(func.count()).select_from(IdempotencyKey)).scalar_one()
    return balances, transactions, keys


def test_valid_preview_returns_masked_summary_and_writes_nothing(
    logged_in_client: FlaskClient, funded: list[SeededUser]
) -> None:
    """HU-06 CA-1, CA-7, CA-8; SC-004."""
    before = _snapshot()

    response = _preview(logged_in_client, funded[1].phone, "150000.00")

    assert response.status_code == 200
    body = response.get_json()
    assert body == {
        "amount": "150000.00",
        "recipient": {"name_masked": None, "phone_masked": "***" + funded[1].phone[-4:]},
        "balance_after": "350000.00",
    }
    assert not re.search(r"\d{10}", response.get_data(as_text=True))
    assert _snapshot() == before


@pytest.mark.parametrize(
    ("phone_of", "amount", "status", "code"),
    [
        (1, "99.00", 422, "amount_out_of_range"),
        (1, "3000000.01", 422, "amount_out_of_range"),
        (None, "1000.00", 404, "recipient_not_found"),
        (0, "1000.00", 422, "self_transfer"),
        (1, "500000.01", 422, "insufficient_balance"),
    ],
)
def test_business_rejections_do_not_write_anything(
    logged_in_client: FlaskClient,
    funded: list[SeededUser],
    phone_of: int | None,
    amount: str,
    status: int,
    code: str,
) -> None:
    """HU-06 CA-2, CA-4, CA-5, CA-6, CA-8."""
    before = _snapshot()
    phone = "3999999999" if phone_of is None else funded[phone_of].phone

    response = _preview(logged_in_client, phone, amount)

    assert response.status_code == status
    assert response.mimetype == "application/problem+json"
    assert response.get_json()["code"] == code
    assert _snapshot() == before


def test_range_error_mentions_transfer_limits(
    logged_in_client: FlaskClient, funded: list[SeededUser]
) -> None:
    """HU-06 CA-2."""
    body = _preview(logged_in_client, funded[1].phone, "99.00").get_json()

    assert body["errors"] == [
        {"field": "amount", "message": "Debe estar entre 100.00 y 3000000.00"}
    ]


def test_format_errors_list_both_fields(
    logged_in_client: FlaskClient, funded: list[SeededUser]
) -> None:
    """HU-06 CA-3, CA-4, RNF-03.2."""
    response = _preview(logged_in_client, "12", "abc")

    body = response.get_json()
    assert response.status_code == 422 and body["code"] == "validation"
    assert {e["field"] for e in body["errors"]} == {"recipient_phone", "amount"}


def test_without_session_is_rejected_and_does_not_reveal_the_recipient(
    client: FlaskClient, funded: list[SeededUser]
) -> None:
    """RNF-01.1, RNF-06.1."""
    known = _preview(client, funded[1].phone, "1000.00")
    unknown = _preview(client, "3999999999", "1000.00")

    assert (known.status_code, unknown.status_code) == (401, 401)
    assert known.get_json()["code"] == unknown.get_json()["code"] == "invalid_session"


def test_sender_wallet_in_body_is_rejected(
    logged_in_client: FlaskClient, funded: list[SeededUser]
) -> None:
    """RNF-01.4."""
    response = logged_in_client.post(
        URL,
        json={"recipient_phone": funded[1].phone, "amount": "1000.00", "sender_wallet_id": 2},
        headers=HEADERS,
    )

    assert response.status_code == 422
    assert response.get_json()["errors"][0]["field"] == "sender_wallet_id"


def test_sender_without_wallet_is_a_404(
    logged_in_client: FlaskClient, seeded_users: list[SeededUser]
) -> None:
    wallet_service.create_wallet(2)

    response = _preview(logged_in_client, seeded_users[1].phone, "1000.00")

    assert (response.status_code, response.get_json()["code"]) == (404, "wallet_not_found")


def test_real_login_cookie_authorizes_the_preview(
    client: FlaskClient, funded: list[SeededUser]
) -> None:
    """HU-02 + HU-06: la cookie de sesión real autoriza la preparación."""
    login = client.post(
        "/api/v1/auth/login",
        json={"phone": funded[0].phone, "password": funded[0].password},
        headers=HEADERS,
    )
    assert login.status_code == 204

    response = _preview(client, funded[1].phone, "1000.00")

    assert response.status_code == 200
    assert response.get_json()["balance_after"] == "499000.00"
