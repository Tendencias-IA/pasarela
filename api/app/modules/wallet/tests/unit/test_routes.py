"""Rama de carrera en la ruta: la clave ya fue guardada por otra petición (HU-08 CA-6)."""

from __future__ import annotations

from typing import Any

import pytest
from flask.testing import FlaskClient
from pytest_mock import MockerFixture

from app.common.idempotency import StoredResponse, request_hash
from app.modules.wallet import routes, service

KEY = "00000000-0000-4000-8000-0000000000c3"
PATH = "/api/v1/wallet/recharges"
HEADERS = {"X-Requested-With": "fetch", "Idempotency-Key": KEY}


@pytest.fixture
def lost_race(mocker: MockerFixture) -> dict[str, Any]:
    """El decorador no encuentra la clave; el servicio pierde la carrera al insertarla."""
    store: dict[tuple[int, str], StoredResponse] = {}
    mocker.patch.object(routes, "find_existing", side_effect=lambda u, k: store.get((u, k)))
    mocker.patch("app.common.idempotency.find_existing", return_value=None)
    mocker.patch.object(
        service, "recharge", side_effect=service.DuplicateIdempotencyKeyError("en curso")
    )
    return {"store": store}


def test_replays_the_winner_response(
    logged_in_client: FlaskClient, lost_race: dict[str, Any]
) -> None:
    body = {"amount": "5000.00"}
    digest = request_hash("POST", PATH, b'{"amount": "5000.00"}')
    lost_race["store"][(1, KEY)] = StoredResponse(digest, 201, {"id": 7, "status": "exitosa"})

    response = logged_in_client.post(PATH, json=body, headers=HEADERS)

    assert response.status_code == 201
    assert response.headers["Idempotent-Replayed"] == "true"
    assert response.get_json() == {"id": 7, "status": "exitosa"}


def test_replayed_problem_keeps_problem_mimetype(
    logged_in_client: FlaskClient, lost_race: dict[str, Any]
) -> None:
    digest = request_hash("POST", PATH, b'{"amount": "5000.00"}')
    lost_race["store"][(1, KEY)] = StoredResponse(digest, 422, {"code": "amount_out_of_range"})

    response = logged_in_client.post(PATH, json={"amount": "5000.00"}, headers=HEADERS)

    assert response.status_code == 422
    assert response.mimetype == "application/problem+json"
    assert response.headers["Idempotent-Replayed"] == "true"


def test_without_stored_response_returns_409(
    logged_in_client: FlaskClient, lost_race: dict[str, Any]
) -> None:
    response = logged_in_client.post(PATH, json={"amount": "5000.00"}, headers=HEADERS)

    assert response.status_code == 409
    assert response.get_json()["code"] == "idempotency_key_in_progress"
