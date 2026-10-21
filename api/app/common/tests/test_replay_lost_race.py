"""Carrera por la misma Idempotency-Key en las rutas de dinero (HU-07 CA-8, HU-08 CA-6)."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import pytest
from flask.testing import FlaskClient
from pytest_mock import MockerFixture

from app.common.idempotency import StoredResponse, request_hash
from app.common.idempotency_store import DuplicateIdempotencyKeyError
from app.modules.transfers import service as transfers_service
from app.modules.wallet import service as wallet_service

KEY = "00000000-0000-4000-8000-0000000000c3"
HEADERS = {"X-Requested-With": "fetch", "Idempotency-Key": KEY}

# (ruta, módulo del servicio, función que pierde la carrera, cuerpo)
ROUTES = [
    ("/api/v1/wallet/recharges", wallet_service, "recharge", {"amount": "5000.00"}),
    (
        "/api/v1/transfers",
        transfers_service,
        "confirm_transfer",
        {"recipient_phone": "3001234567", "amount": "5000.00"},
    ),
]


@pytest.fixture(params=ROUTES, ids=["recharge", "transfer"])
def money_route(
    request: pytest.FixtureRequest, mocker: MockerFixture
) -> tuple[str, dict[str, Any], Callable[[StoredResponse | None], None]]:
    path, module, function, body = request.param

    def lose_race(winner: StoredResponse | None) -> None:
        """El decorador no encuentra la clave; el servicio pierde la carrera al insertarla."""
        mocker.patch.object(module, function, side_effect=DuplicateIdempotencyKeyError("en curso"))
        mocker.patch("app.common.idempotency.find_existing", side_effect=[None, winner])

    return path, body, lose_race


def _stored(
    path: str, body: dict[str, Any], status: int, payload: dict[str, Any]
) -> StoredResponse:
    return StoredResponse(request_hash("POST", path, json.dumps(body).encode()), status, payload)


def test_replays_the_winner_response(
    logged_in_client: FlaskClient,
    money_route: tuple[str, dict[str, Any], Callable[[StoredResponse | None], None]],
) -> None:
    path, body, lose_race = money_route
    lose_race(_stored(path, body, 201, {"id": 7}))

    response = logged_in_client.post(path, json=body, headers=HEADERS)

    assert response.status_code == 201
    assert response.headers["Idempotent-Replayed"] == "true"
    assert response.get_json() == {"id": 7}


def test_replayed_problem_keeps_problem_mimetype(
    logged_in_client: FlaskClient,
    money_route: tuple[str, dict[str, Any], Callable[[StoredResponse | None], None]],
) -> None:
    path, body, lose_race = money_route
    lose_race(_stored(path, body, 422, {"code": "insufficient_balance"}))

    response = logged_in_client.post(path, json=body, headers=HEADERS)

    assert response.status_code == 422
    assert response.mimetype == "application/problem+json"
    assert response.headers["Idempotent-Replayed"] == "true"


def test_without_stored_response_returns_409(
    logged_in_client: FlaskClient,
    money_route: tuple[str, dict[str, Any], Callable[[StoredResponse | None], None]],
) -> None:
    path, body, lose_race = money_route
    lose_race(None)

    response = logged_in_client.post(path, json=body, headers=HEADERS)

    assert response.status_code == 409
    assert response.get_json()["code"] == "idempotency_key_in_progress"
