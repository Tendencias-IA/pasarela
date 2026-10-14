"""Decorador @idempotent (HU-08 CA-6, FR-007, ADR-0005)."""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from flask import Flask, g, jsonify
from flask.testing import FlaskClient
from pytest_mock import MockerFixture

from app.common import idempotency
from app.common.idempotency import StoredResponse, idempotent, request_hash

KEY = "00000000-0000-4000-8000-000000000001"


@pytest.fixture
def route(app: Flask, mocker: MockerFixture) -> dict[str, Any]:
    """Ruta de prueba con el almacén de claves simulado."""
    store: dict[tuple[int, str], StoredResponse] = {}
    mocker.patch.object(idempotency, "find_existing", side_effect=lambda u, k: store.get((u, k)))
    calls: list[Any] = []

    @app.post("/_idem")
    @idempotent
    def view() -> Any:
        calls.append(g.idempotency)
        return jsonify({"ok": True}), 201

    return {"store": store, "calls": calls}


def _post(client: FlaskClient, key: str | None, body: dict[str, Any]) -> Any:
    headers = {"X-Requested-With": "fetch"}
    if key is not None:
        headers["Idempotency-Key"] = key
    return client.post("/_idem", json=body, headers=headers)


def test_missing_header_is_rejected_before_running_the_view(
    logged_in_client: FlaskClient, route: dict[str, Any]
) -> None:
    response = _post(logged_in_client, None, {"amount": "5000.00"})

    assert response.status_code == 400
    assert response.get_json()["code"] == "missing_idempotency_key"
    assert route["calls"] == []


def test_non_uuid_header_is_rejected(logged_in_client: FlaskClient, route: dict[str, Any]) -> None:
    response = _post(logged_in_client, "no-es-uuid", {"amount": "5000.00"})

    assert response.status_code == 400
    assert route["calls"] == []


def test_new_key_runs_view_and_exposes_context(
    logged_in_client: FlaskClient, route: dict[str, Any]
) -> None:
    response = _post(logged_in_client, KEY, {"amount": "5000.00"})

    assert response.status_code == 201
    context = route["calls"][0]
    assert context.key == str(uuid.UUID(KEY))
    assert context.request_hash == request_hash("POST", "/_idem", b'{"amount": "5000.00"}')


def test_same_key_and_body_replays_stored_response_without_running_view(
    logged_in_client: FlaskClient, route: dict[str, Any]
) -> None:
    digest = request_hash("POST", "/_idem", b'{"amount":"5000.00"}')
    route["store"][(1, KEY)] = StoredResponse(digest, 201, {"id": 42, "replayed": "sí"})

    response = _post(logged_in_client, KEY, {"amount": "5000.00"})

    assert response.status_code == 201
    assert response.headers["Idempotent-Replayed"] == "true"
    assert response.get_json() == {"id": 42, "replayed": "sí"}
    assert route["calls"] == []


def test_same_key_with_different_body_is_a_conflict(
    logged_in_client: FlaskClient, route: dict[str, Any]
) -> None:
    route["store"][(1, KEY)] = StoredResponse("otro-hash", 201, {"id": 42})

    response = _post(logged_in_client, KEY, {"amount": "9999.00"})

    assert response.status_code == 422
    assert response.get_json()["code"] == "idempotency_key_mismatch"
    assert route["calls"] == []


def test_replayed_problem_keeps_problem_mimetype(
    logged_in_client: FlaskClient, route: dict[str, Any]
) -> None:
    digest = request_hash("POST", "/_idem", b'{"amount":"1.00"}')
    route["store"][(1, KEY)] = StoredResponse(digest, 422, {"code": "amount_out_of_range"})

    response = _post(logged_in_client, KEY, {"amount": "1.00"})

    assert response.status_code == 422
    assert response.mimetype == "application/problem+json"


def test_request_hash_is_canonical_and_tolerates_non_json() -> None:
    assert request_hash("post", "/x", b'{"b":1,"a":2}') == request_hash(
        "POST", "/x", b'{ "a": 2, "b": 1 }'
    )
    assert request_hash("POST", "/x", b"no-json") != request_hash("POST", "/x", b"")


def test_requires_session(client: FlaskClient, route: dict[str, Any]) -> None:
    response = _post(client, KEY, {"amount": "5000.00"})

    assert response.status_code == 401
