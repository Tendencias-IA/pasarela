"""HU-13: correo persistente, unicidad y datos de cuenta intactos en MySQL."""

from decimal import Decimal

from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy import select

from app.extensions import db
from app.modules.wallet.models import Wallet

HEADERS = {"X-Requested-With": "fetch"}


def test_email_update_persists_without_changing_account_and_rejects_duplicates(
    integration_app: Flask,
    integration_client: FlaskClient,
    db_session: object,
) -> None:
    """HU-13 CA-1, CA-2, CA-3, CA-4, CA-5, CA-6."""
    ids: list[int] = []
    for index in (1, 2):
        response = integration_client.post(
            "/api/v1/accounts",
            json={
                "full_name": "Persona Correo",
                "phone": f"300666000{index}",
                "national_id": f"CORREO00{index}",
                "email": f"correo{index}@example.test",
                "password": "Clave1234",
            },
            headers=HEADERS,
        )
        assert response.status_code == 201
        ids.append(response.get_json()["account_id"])
        db.session.remove()
    wallet = db.session.scalar(select(Wallet).where(Wallet.user_id == ids[0]))
    assert wallet is not None
    wallet.balance = Decimal("12345.00")
    db.session.commit()
    db.session.remove()
    assert (
        integration_client.post(
            "/api/v1/auth/login",
            json={
                "phone": "3006660001",
                "password": "Clave1234",
            },
            headers=HEADERS,
        ).status_code
        == 204
    )
    db.session.remove()
    response = integration_client.patch(
        "/api/v1/profile",
        json={
            "email": " Nuevo@Example.test ",
        },
        headers=HEADERS,
    )
    assert response.status_code == 200
    assert response.get_json() == {
        "full_name": "Persona Correo",
        "phone": "3006660001",
        "national_id": "CORREO001",
        "email": "nuevo@example.test",
    }
    db.session.remove()
    assert integration_client.get("/api/v1/profile").get_json()["email"] == "nuevo@example.test"
    db.session.remove()
    assert (
        integration_client.patch(
            "/api/v1/profile",
            json={
                "email": "CORREO2@example.test",
            },
            headers=HEADERS,
        ).status_code
        == 409
    )
    db.session.remove()
    assert integration_client.get("/api/v1/profile").get_json()["email"] == "nuevo@example.test"
    db.session.remove()
    assert db.session.scalar(select(Wallet.balance).where(Wallet.user_id == ids[0])) == Decimal(
        "12345.00"
    )
