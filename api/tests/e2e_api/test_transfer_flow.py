"""HU-07 por HTTP contra MySQL: transferir, idempotencia e historial de ambos participantes."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest
from flask import Flask, g
from flask.testing import FlaskClient
from sqlalchemy import func, select

from app.common.models.transaction import Transaction
from app.extensions import db
from app.modules.wallet import service as wallet_service
from app.modules.wallet.models import Wallet
from tests.factories import SeededUser

URL = "/api/v1/transfers"
KEY_A = "00000000-0000-4000-8000-00000000000a"
KEY_B = "00000000-0000-4000-8000-00000000000b"

pytestmark = pytest.mark.mysql


@pytest.fixture
def funded(seeded_users: list[SeededUser]) -> list[SeededUser]:
    """Billeteras de 1 (500.000) y 2 (0), sembradas sin sesión HTTP."""
    wallet_service.create_wallet(1)
    wallet_service.create_wallet(2)
    wallet = db.session.execute(select(Wallet).where(Wallet.user_id == 1)).scalar_one()
    wallet.balance = Decimal("500000.00")
    db.session.commit()
    return seeded_users


def _post(
    client: FlaskClient, phone: str, amount: Any, key: str | None = KEY_A, **extra: Any
) -> Any:
    headers = {"X-Requested-With": "fetch"}
    if key is not None:
        headers["Idempotency-Key"] = key
    return client.post(
        URL, json={"recipient_phone": phone, "amount": amount, **extra}, headers=headers
    )


def _balance(user_id: int) -> Decimal:
    db.session.expire_all()
    return Decimal(
        db.session.execute(select(Wallet.balance).where(Wallet.user_id == user_id)).scalar_one()
    )


def _count() -> int:
    db.session.expire_all()
    return db.session.execute(select(func.count()).select_from(Transaction)).scalar_one()


def _history(client: FlaskClient) -> dict[str, Any]:
    # La fixture `app` mantiene un contexto abierto y `g` se comparte entre peticiones del test
    # client; en producción cada petición tiene su propio `g`.
    g.pop("user_id", None)
    return client.get("/api/v1/movements").get_json()  # type: ignore[no-any-return]


def _login(app: Flask, user: SeededUser) -> FlaskClient:
    client = app.test_client()
    g.pop("user_id", None)
    response = client.post(
        "/api/v1/auth/login",
        json={"phone": user.phone, "password": user.password},
        headers={"X-Requested-With": "fetch"},
    )
    assert response.status_code == 204
    return client


def test_valid_transfer_returns_the_documented_body_and_updates_both_balances(
    logged_in_client: FlaskClient, funded: list[SeededUser]
) -> None:
    """HU-07 CA-1, CA-3, CA-7."""
    response = _post(logged_in_client, funded[1].phone, "150000.00")

    assert response.status_code == 201
    body = response.get_json()
    assert body["type"] == "transferencia" and body["status"] == "exitosa"
    assert body["amount"] == "150000.00" and body["balance_after"] == "350000.00"
    assert body["recipient"] == {"name_masked": None, "phone_masked": "***" + funded[1].phone[-4:]}
    assert body["created_at"].endswith("Z") and isinstance(body["id"], int)
    assert funded[1].phone not in response.get_data(as_text=True)
    assert (_balance(1), _balance(2)) == (Decimal("350000.00"), Decimal("150000.00"))
    assert response.headers.get("Idempotent-Replayed") is None


@pytest.mark.parametrize(
    ("phone_of", "amount", "status", "code", "rows"),
    [
        (1, "99.00", 422, "amount_out_of_range", 1),
        (1, "3000000.01", 422, "amount_out_of_range", 1),
        (None, "1000.00", 404, "recipient_not_found", 0),
        (0, "1000.00", 422, "self_transfer", 1),
        (1, "500000.01", 422, "insufficient_balance", 1),
    ],
)
def test_business_rejections_keep_balances_and_record_rejected_rows(
    logged_in_client: FlaskClient,
    funded: list[SeededUser],
    phone_of: int | None,
    amount: str,
    status: int,
    code: str,
    rows: int,
) -> None:
    """HU-07 CA-2, CA-6."""
    phone = "3999999999" if phone_of is None else funded[phone_of].phone

    response = _post(logged_in_client, phone, amount)

    assert response.status_code == status and response.mimetype == "application/problem+json"
    assert response.get_json()["code"] == code
    assert (_balance(1), _balance(2)) == (Decimal("500000.00"), Decimal("0.00"))
    assert _count() == rows


def test_format_error_creates_no_record(
    logged_in_client: FlaskClient, funded: list[SeededUser]
) -> None:
    """HU-07 CA-2: los errores de formato no crean registros."""
    response = _post(logged_in_client, "12", "abc")

    body = response.get_json()
    assert response.status_code == 422 and body["code"] == "validation"
    assert {e["field"] for e in body["errors"]} == {"recipient_phone", "amount"}
    assert _count() == 0


def test_same_key_and_body_is_replayed_without_a_second_debit(
    logged_in_client: FlaskClient, funded: list[SeededUser]
) -> None:
    """HU-07 CA-8, RNF-04.4."""
    first = _post(logged_in_client, funded[1].phone, "20000.00")
    replay = _post(logged_in_client, funded[1].phone, "20000.00")

    assert (first.status_code, replay.status_code) == (201, 201)
    assert replay.headers["Idempotent-Replayed"] == "true"
    assert replay.get_json() == first.get_json()
    assert (_balance(1), _balance(2)) == (Decimal("480000.00"), Decimal("20000.00"))
    assert _count() == 1


def test_same_key_with_another_body_is_a_conflict(
    logged_in_client: FlaskClient, funded: list[SeededUser]
) -> None:
    """HU-07 CA-8, ADR-0005."""
    _post(logged_in_client, funded[1].phone, "20000.00")

    response = _post(logged_in_client, funded[1].phone, "30000.00")

    assert response.status_code == 422
    assert response.get_json()["code"] == "idempotency_key_mismatch"
    assert _balance(2) == Decimal("20000.00")


def test_rejected_transfer_is_replayed_as_the_same_problem(
    logged_in_client: FlaskClient, funded: list[SeededUser]
) -> None:
    """ADR-0005: los rechazos también se reproducen y no duplican la fila."""
    first = _post(logged_in_client, funded[1].phone, "900000.00")

    replay = _post(logged_in_client, funded[1].phone, "900000.00")

    assert replay.status_code == first.status_code == 422
    assert replay.headers["Idempotent-Replayed"] == "true"
    assert replay.mimetype == "application/problem+json"
    assert _count() == 1


def test_unknown_recipient_is_replayed_without_any_row(
    logged_in_client: FlaskClient, funded: list[SeededUser]
) -> None:
    first = _post(logged_in_client, "3999999999", "1000.00")
    replay = _post(logged_in_client, "3999999999", "1000.00")

    assert (first.status_code, replay.status_code) == (404, 404)
    assert replay.headers["Idempotent-Replayed"] == "true"
    assert _count() == 0


def test_missing_key_is_rejected_before_touching_any_wallet(
    logged_in_client: FlaskClient, funded: list[SeededUser]
) -> None:
    """HU-07 CA-8."""
    response = _post(logged_in_client, funded[1].phone, "1000.00", key=None)

    assert response.status_code == 400
    assert response.get_json()["code"] == "missing_idempotency_key"
    assert (_balance(1), _count()) == (Decimal("500000.00"), 0)


def test_two_different_keys_apply_two_transfers(
    logged_in_client: FlaskClient, funded: list[SeededUser]
) -> None:
    """ADR-0005: claves distintas son solicitudes distintas."""
    _post(logged_in_client, funded[1].phone, "1000.00", KEY_A)
    _post(logged_in_client, funded[1].phone, "1000.00", KEY_B)

    assert (_balance(1), _balance(2)) == (Decimal("498000.00"), Decimal("2000.00"))


def test_sender_fields_in_the_body_are_rejected(
    logged_in_client: FlaskClient, funded: list[SeededUser]
) -> None:
    """HU-07 CA-2, RNF-01.4."""
    response = _post(logged_in_client, funded[1].phone, "1000.00", sender_wallet_id=2)

    assert response.status_code == 422
    assert response.get_json()["errors"][0]["field"] == "sender_wallet_id"
    assert _count() == 0


def test_real_login_transfers_and_both_histories_show_it(
    app: Flask, funded: list[SeededUser]
) -> None:
    """HU-07 CA-1, CA-5 + HU-09: enviada para el emisor y recibida para el destinatario."""
    sender = _login(app, funded[0])
    receiver = _login(app, funded[1])

    g.pop("user_id", None)
    response = _post(sender, funded[1].phone, "150000.00")
    assert response.status_code == 201

    sent, received = _history(sender), _history(receiver)
    [sent_item], [received_item] = sent["items"], received["items"]
    assert (sent_item["direction"], received_item["direction"]) == ("enviada", "recibida")
    assert sent_item["id"] == received_item["id"] == response.get_json()["id"]
    assert sent_item["counterparty"]["phone_masked"] == "***" + funded[1].phone[-4:]
    assert received_item["counterparty"]["phone_masked"] == "***" + funded[0].phone[-4:]
    assert funded[0].phone not in str(received) and funded[1].phone not in str(sent)


def test_rejected_transfer_is_in_the_senders_history_but_not_the_receivers(
    app: Flask, funded: list[SeededUser]
) -> None:
    """HU-07 CA-6 + HU-09 CA-5: el destinatario no ve una transferencia que nunca le llegó."""
    sender = _login(app, funded[0])
    receiver = _login(app, funded[1])

    g.pop("user_id", None)
    _post(sender, funded[1].phone, "900000.00")

    [item] = _history(sender)["items"]
    assert (item["status"], item["rejection_reason"]) == ("rechazada", "insufficient_balance")
    assert _history(receiver)["items"] == []


def test_without_session_nothing_is_written(client: FlaskClient, funded: list[SeededUser]) -> None:
    """HU-07 CA-2, RNF-01.1."""
    response = _post(client, funded[1].phone, "1000.00")

    assert response.status_code == 401
    assert response.get_json()["code"] == "invalid_session"
    assert _count() == 0
