"""Rama de carrera en la ruta: la clave ya fue guardada por otra petición (HU-07 CA-8)."""

from __future__ import annotations

from typing import Any

import pytest
from flask.testing import FlaskClient
from pytest_mock import MockerFixture

from app.common.idempotency import StoredResponse, request_hash
from app.modules.transfers import routes, service
from app.modules.wallet.service import DuplicateIdempotencyKeyError

KEY = "00000000-0000-4000-8000-0000000000c3"
PATH = "/api/v1/transfers"
HEADERS = {"X-Requested-With": "fetch", "Idempotency-Key": KEY}
BODY = {"recipient_phone": "3001234567", "amount": "5000.00"}
RAW = b'{"recipient_phone": "3001234567", "amount": "5000.00"}'


@pytest.fixture
def lost_race(mocker: MockerFixture) -> dict[tuple[int, str], StoredResponse]:
    """El decorador no encuentra la clave; el servicio pierde la carrera al insertarla."""
    store: dict[tuple[int, str], StoredResponse] = {}
    mocker.patch.object(routes, "find_existing", side_effect=lambda u, k: store.get((u, k)))
    mocker.patch("app.common.idempotency.find_existing", return_value=None)
    mocker.patch.object(
        service, "confirm_transfer", side_effect=DuplicateIdempotencyKeyError("en curso")
    )
    return store


def test_replays_the_winner_response(
    logged_in_client: FlaskClient, lost_race: dict[tuple[int, str], StoredResponse]
) -> None:
    lost_race[(1, KEY)] = StoredResponse(request_hash("POST", PATH, RAW), 201, {"id": 7})

    response = logged_in_client.post(PATH, json=BODY, headers=HEADERS)

    assert response.status_code == 201
    assert response.headers["Idempotent-Replayed"] == "true"
    assert response.get_json() == {"id": 7}


def test_without_stored_response_returns_409(
    logged_in_client: FlaskClient, lost_race: dict[tuple[int, str], Any]
) -> None:
    response = logged_in_client.post(PATH, json=BODY, headers=HEADERS)

    assert response.status_code == 409
    assert response.get_json()["code"] == "idempotency_key_in_progress"
