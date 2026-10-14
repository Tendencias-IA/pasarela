"""Interfaz de sesión (RNF-01.1, FR-012)."""

from __future__ import annotations

from flask import Flask, g
from flask.testing import FlaskClient

from app.common.auth import current_user_id, login_required


def _register_private_route(app: Flask) -> None:
    @app.get("/_privada")
    @login_required
    def privada() -> dict[str, int]:
        return {"user_id": current_user_id()}


def test_private_route_rejects_requests_without_session(app: Flask, client: FlaskClient) -> None:
    _register_private_route(app)

    response = client.get("/_privada")

    assert response.status_code == 401
    assert response.get_json()["code"] == "invalid_session"


def test_private_route_uses_user_id_set_by_auth_layer(app: Flask, client: FlaskClient) -> None:
    _register_private_route(app)

    @app.before_request
    def fake_session() -> None:
        g.user_id = 7

    response = client.get("/_privada")

    assert response.status_code == 200
    assert response.get_json() == {"user_id": 7}


def test_logged_in_client_fixture_sets_user(logged_in_client: FlaskClient, app: Flask) -> None:
    _register_private_route(app)

    assert logged_in_client.get("/_privada").get_json() == {"user_id": 1}
