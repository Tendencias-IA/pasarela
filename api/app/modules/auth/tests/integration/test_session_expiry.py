"""Integración de HU-04 contra MySQL (marker `mysql`): login real y expiración deslizante.

Criterios: HU-04 CA-1 a CA-4 (docs/referencia/requisitos-billetera-v1.0.md).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy import func, select

from app.common.clock import utcnow
from app.common.models.transaction import Transaction
from app.extensions import db
from app.modules.auth.models import Session
from app.modules.wallet import service as wallet_service
from app.modules.wallet.models import Wallet
from tests.factories import SeededUser

pytestmark = pytest.mark.mysql

SESSION_URL = "/api/v1/auth/session"
_HEADERS = {"X-Requested-With": "fetch"}
IDLE = timedelta(minutes=5)


def _login(client: FlaskClient, seeded: SeededUser) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"phone": seeded.phone, "password": seeded.password},
        headers=_HEADERS,
    )
    assert response.status_code == 204


def _the_session() -> Session:
    db.session.expire_all()
    return db.session.execute(select(Session).order_by(Session.id.desc())).scalars().first()  # type: ignore[return-value]


def _update_session(**values: Any) -> None:
    db.session.query(Session).update(values)  # type: ignore[arg-type]
    db.session.commit()


def _parse_iso_z(value: str) -> datetime:
    assert value.endswith("Z")
    return datetime.fromisoformat(value[:-1])


# --- US1 --------------------------------------------------------------------------------


def test_expired_session_is_rejected_and_revoked(
    client: FlaskClient, seeded_users: list[SeededUser]
) -> None:
    """HU-04 CA-1, CA-2."""
    _login(client, seeded_users[0])
    _update_session(expires_at=utcnow() - timedelta(minutes=1))

    rejected = client.get(SESSION_URL)

    assert rejected.status_code == 401
    assert rejected.get_json()["code"] == "invalid_session"
    assert _the_session().revoked_at is not None

    assert client.get(SESSION_URL).status_code == 401

    _login(client, seeded_users[0])
    assert client.get(SESSION_URL).status_code == 200


def test_expired_session_is_not_revived_by_moving_expires_at(
    client: FlaskClient, seeded_users: list[SeededUser]
) -> None:
    """HU-04 CA-1 (spec SC-005, FR-003)."""
    _login(client, seeded_users[0])
    _update_session(expires_at=utcnow() - timedelta(minutes=1))
    assert client.get(SESSION_URL).status_code == 401

    _update_session(expires_at=utcnow() + timedelta(minutes=10))

    assert client.get(SESSION_URL).status_code == 401


# --- US2 --------------------------------------------------------------------------------


def test_private_request_extends_expiry_and_renews_cookie(
    client: FlaskClient, seeded_users: list[SeededUser]
) -> None:
    """HU-04 CA-4, FR-008."""
    _login(client, seeded_users[0])
    _update_session(
        last_activity_at=utcnow() - timedelta(seconds=60),
        expires_at=utcnow() + timedelta(minutes=4),
    )

    before = utcnow()
    response = client.get(SESSION_URL)
    after = utcnow()

    assert response.status_code == 200
    expires_at = _parse_iso_z(response.get_json()["expires_at"])
    assert before + IDLE - timedelta(seconds=5) <= expires_at <= after + IDLE + timedelta(seconds=5)
    row = _the_session()
    # MySQL redondea los microsegundos al guardar (DATETIME sin fracción) y la API los trunca.
    assert abs(row.expires_at - expires_at) <= timedelta(seconds=1)
    assert row.last_activity_at >= before - timedelta(seconds=1)
    set_cookie = "; ".join(response.headers.getlist("Set-Cookie"))
    assert "session=" in set_cookie
    assert "Max-Age=300" in set_cookie
    assert "HttpOnly" in set_cookie


def test_rejected_request_does_not_touch_session(
    app: Flask, client: FlaskClient, seeded_users: list[SeededUser]
) -> None:
    """HU-04 CA-4 (FR-004): solo la actividad válida cuenta."""
    _login(client, seeded_users[0])
    row = _the_session()
    last_activity_at, expires_at = row.last_activity_at, row.expires_at

    anonymous = app.test_client()
    response = anonymous.get(SESSION_URL)

    assert response.status_code == 401
    assert response.headers.getlist("Set-Cookie") == []
    row = _the_session()
    assert (row.last_activity_at, row.expires_at) == (last_activity_at, expires_at)


# --- US3 --------------------------------------------------------------------------------


def test_recharge_with_expired_session_creates_no_transaction(
    client: FlaskClient, seeded_users: list[SeededUser]
) -> None:
    """HU-04 CA-3."""
    _login(client, seeded_users[0])
    wallet_service.create_wallet(1)
    _update_session(expires_at=utcnow() - timedelta(minutes=1))

    response = client.post(
        "/api/v1/wallet/recharges",
        json={"amount": "50000.00"},
        headers={**_HEADERS, "Idempotency-Key": "00000000-0000-4000-8000-000000000004"},
    )

    assert response.status_code == 401
    assert response.get_json()["code"] == "invalid_session"
    db.session.expire_all()
    assert db.session.execute(select(func.count()).select_from(Transaction)).scalar_one() == 0
    wallet = db.session.execute(select(Wallet).where(Wallet.user_id == 1)).scalar_one()
    assert str(wallet.balance) == "0.00"
