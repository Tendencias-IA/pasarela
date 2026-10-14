"""GET /health (observability.md)."""

from __future__ import annotations

from flask.testing import FlaskClient
from pytest_mock import MockerFixture
from sqlalchemy.exc import OperationalError

from app.extensions import db


def test_health_returns_ok_when_database_answers(client: FlaskClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "db": "ok"}


def test_health_returns_503_when_database_fails(client: FlaskClient, mocker: MockerFixture) -> None:
    mocker.patch.object(
        db.session, "execute", side_effect=OperationalError("SELECT 1", {}, Exception())
    )

    response = client.get("/health")

    assert response.status_code == 503
    assert response.get_json() == {"status": "degraded", "db": "error"}
