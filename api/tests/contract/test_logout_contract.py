"""HU-03 CA-1/CA-2: respuestas contra OpenAPI, sin valores de sesión en JSON."""

from datetime import datetime
from pathlib import Path

import yaml
from flask.testing import FlaskClient
from jsonschema import validate
from pytest_mock import MockerFixture

HEADERS = {"X-Requested-With": "fetch"}
CONTRACT = yaml.safe_load((Path(__file__).resolve().parents[2] / "openapi.yaml").read_text())


def test_logout_success_matches_no_content_contract(
    client: FlaskClient, mocker: MockerFixture
) -> None:
    mocker.patch("app.common.auth.current_user_id", return_value=1)
    revoke = mocker.patch("app.modules.auth.service.logout")
    response = client.post("/api/v1/auth/logout", headers=HEADERS)
    assert (
        str(response.status_code) in CONTRACT["paths"]["/api/v1/auth/logout"]["post"]["responses"]
    )
    assert response.status_code == 204
    assert response.data == b""
    assert "Max-Age=0" in response.headers["Set-Cookie"]
    revoke.assert_called_once()


def test_session_status_matches_schema(client: FlaskClient, mocker: MockerFixture) -> None:
    mocker.patch("app.common.auth.current_user_id", return_value=1)
    mocker.patch("app.modules.auth.routes.current_user_id", return_value=1)
    mocker.patch(
        "app.modules.auth.routes.current_session_expires_at", return_value=datetime(2099, 1, 1)
    )
    response = client.get("/api/v1/auth/session")
    assert response.status_code == 200
    validate(response.get_json(), CONTRACT["components"]["schemas"]["SessionOut"])


def test_logout_unauthenticated_matches_problem_schema(client: FlaskClient) -> None:
    response = client.post("/api/v1/auth/logout", headers=HEADERS)
    assert response.status_code == 401
    validate(response.get_json(), CONTRACT["components"]["schemas"]["Problem"])
