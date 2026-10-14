"""Contrato de /api/v1/auth/login contra api/openapi.yaml (testing.md)."""

from __future__ import annotations

from flask.testing import FlaskClient
from sqlalchemy.orm import Session as SqlAlchemySession

from tests.factories import make_phone, make_user

_HEADERS = {"X-Requested-With": "fetch"}


def test_login_success_response_matches_contract(
    integration_client: FlaskClient, db_session: SqlAlchemySession
) -> None:
    seeded = make_user(password="Clave1234")
    db_session.add(seeded.user)
    db_session.commit()

    response = integration_client.post(
        "/api/v1/auth/login",
        json={"phone": seeded.phone, "password": seeded.password},
        headers=_HEADERS,
    )

    assert response.status_code == 204
    assert response.data == b""


def test_login_error_response_matches_problem_schema(integration_client: FlaskClient) -> None:
    response = integration_client.post(
        "/api/v1/auth/login",
        json={"phone": make_phone(), "password": "cualquiera123"},
        headers=_HEADERS,
    )

    body = response.get_json()

    assert response.status_code == 401
    assert response.mimetype == "application/problem+json"
    for field in ("type", "title", "status", "instance", "code"):
        assert field in body


def test_login_invalid_phone_format_returns_validation_errors(
    integration_client: FlaskClient,
) -> None:
    response = integration_client.post(
        "/api/v1/auth/login",
        json={"phone": "123", "password": "cualquiera123"},
        headers=_HEADERS,
    )

    body = response.get_json()

    assert response.status_code == 422
    assert body["code"] == "validation"
    assert any(error["field"] == "phone" for error in body["errors"])
