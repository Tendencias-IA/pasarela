"""Contrato: GET /api/v1/movements cumple api/openapi.yaml (HU-09, FR-007)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from flask.testing import FlaskClient
from jsonschema import Draft202012Validator, RefResolver

from app.modules.wallet import service as wallet_service
from tests.factories import SeededUser

OPENAPI = Path(__file__).resolve().parents[2] / "openapi.yaml"
KEY = "00000000-0000-4000-8000-000000000021"

pytestmark = pytest.mark.mysql


@pytest.fixture(scope="module")
def spec() -> dict[str, Any]:
    return yaml.safe_load(OPENAPI.read_text())


def _validate(spec: dict[str, Any], schema_name: str, body: Any) -> None:
    schema = spec["components"]["schemas"][schema_name]
    resolver = RefResolver.from_schema(spec)
    Draft202012Validator(schema, resolver=resolver).validate(body)


def test_movements_200_matches_movements_page_out_schema(
    logged_in_client: FlaskClient, seeded_users: list[SeededUser], spec: dict[str, Any]
) -> None:
    wallet_service.create_wallet(1)
    logged_in_client.post(
        "/api/v1/wallet/recharges",
        json={"amount": "50000.00"},
        headers={"X-Requested-With": "fetch", "Idempotency-Key": KEY},
    )

    response = logged_in_client.get("/api/v1/movements?page=1")

    assert response.status_code == 200
    body = response.get_json()
    _validate(spec, "MovementsPageOut", body)
    assert body["total"] == 1 and body["items"][0]["direction"] == "recarga"


def test_empty_history_matches_schema(
    logged_in_client: FlaskClient, seeded_users: list[SeededUser], spec: dict[str, Any]
) -> None:
    wallet_service.create_wallet(1)

    body = logged_in_client.get("/api/v1/movements").get_json()

    _validate(spec, "MovementsPageOut", body)
    assert body == {"items": [], "page": 1, "page_size": 20, "total": 0}


def test_path_is_declared_in_openapi(spec: dict[str, Any]) -> None:
    assert "get" in spec["paths"]["/api/v1/movements"]
