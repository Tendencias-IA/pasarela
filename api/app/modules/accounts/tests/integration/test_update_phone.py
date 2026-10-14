"""HU-12: persistencia y acceso real por teléfono nuevo contra MySQL."""

from decimal import Decimal

from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy import func, select

from app.extensions import db
from app.modules.accounts.models import User
from app.modules.wallet.models import Wallet

HEADERS = {"X-Requested-With": "fetch"}


def test_update_phone_changes_login_and_releases_old_number(
    integration_app: Flask,
    integration_client: FlaskClient,
    db_session: object,
) -> None:
    """HU-12 CA-3, CA-4, CA-5, CA-6, CA-7; solo cuenta propia."""
    payload = {
        "full_name": "Persona Perfil",
        "phone": "3005550001",
        "national_id": "PERFIL001",
        "email": "perfil@example.test",
        "password": "Clave1234",
    }
    created = integration_client.post("/api/v1/accounts", json=payload, headers=HEADERS)
    assert created.status_code == 201
    user_id = created.get_json()["account_id"]
    db.session.remove()
    assert (
        integration_client.post(
            "/api/v1/auth/login",
            json={"phone": payload["phone"], "password": payload["password"]},
            headers=HEADERS,
        ).status_code
        == 204
    )
    db.session.remove()

    updated = integration_client.patch(
        "/api/v1/profile",
        json={"phone": "3005550002"},
        headers=HEADERS,
    )
    assert updated.status_code == 200
    assert updated.get_json()["national_id"] == "PERFIL001"
    assert "password" not in updated.get_json()
    db.session.remove()
    assert integration_client.get("/api/v1/profile").get_json()["phone"] == "3005550002"
    db.session.remove()
    assert (
        integration_client.post(
            "/api/v1/auth/login",
            json={"phone": "3005550001", "password": "Clave1234"},
            headers=HEADERS,
        ).status_code
        == 401
    )
    db.session.remove()
    assert (
        integration_client.post(
            "/api/v1/auth/login",
            json={"phone": "3005550002", "password": "Clave1234"},
            headers=HEADERS,
        ).status_code
        == 204
    )
    db.session.remove()
    wallet = db.session.scalar(select(Wallet).where(Wallet.user_id == user_id))
    assert wallet is not None and wallet.balance == Decimal("0.00")
    assert db.session.scalar(select(User.national_id).where(User.id == user_id)) == "PERFIL001"
    db.session.remove()

    payload.update(national_id="PERFIL002", email="otra@example.test")
    assert (
        integration_client.post("/api/v1/accounts", json=payload, headers=HEADERS).status_code
        == 201
    )
    db.session.remove()
    assert (
        db.session.scalar(select(func.count()).select_from(User).where(User.phone == "3005550001"))
        == 1
    )


def test_duplicate_phone_rejects_without_changing_current_profile(
    integration_app: Flask,
    integration_client: FlaskClient,
    db_session: object,
) -> None:
    """HU-12 CA-2 y CA-8."""
    for index in (3, 4):
        payload = {
            "full_name": "Persona Perfil",
            "phone": f"300555000{index}",
            "national_id": f"PERFIL00{index}",
            "email": f"perfil{index}@example.test",
            "password": "Clave1234",
        }
        assert (
            integration_client.post("/api/v1/accounts", json=payload, headers=HEADERS).status_code
            == 201
        )
        db.session.remove()
    assert (
        integration_client.post(
            "/api/v1/auth/login",
            json={"phone": "3005550003", "password": "Clave1234"},
            headers=HEADERS,
        ).status_code
        == 204
    )
    db.session.remove()
    response = integration_client.patch(
        "/api/v1/profile", json={"phone": "3005550004"}, headers=HEADERS
    )
    assert response.status_code == 409
    db.session.remove()
    assert integration_client.get("/api/v1/profile").get_json()["phone"] == "3005550003"
