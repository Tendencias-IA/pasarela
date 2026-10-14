"""Contrato: GET /api/v1/wallet cumple api/openapi.yaml (HU-05, FR-002)."""

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
KEY = "00000000-0000-4000-8000-000000000031"

pytestmark = pytest.mark.mysql


@pytest.fixture(scope="module")
def spec() -> dict[str, Any]:
    return yaml.safe_load(OPENAPI.read_text())


def _validate(spec: dict[str, Any], schema_name: str, body: Any) -> None:
    schema = spec["components"]["schemas"][schema_name]
    resolver = RefResolver.from_schema(spec)
    Draft202012Validator(schema, resolver=resolver).validate(body)


def test_wallet_200_matches_wallet_out_schema(
    logged_in_client: FlaskClient, seeded_users: list[SeededUser], spec: dict[str, Any]
) -> None:
    """HU-05 CA-1, CA-2."""
    wallet_service.create_wallet(1)
    logged_in_client.post(
        "/api/v1/wallet/recharges",
        json={"amount": "50000.00"},
        headers={"X-Requested-With": "fetch", "Idempotency-Key": KEY},
    )

    response = logged_in_client.get("/api/v1/wallet")

    assert response.status_code == 200
    body = response.get_json()
    _validate(spec, "WalletOut", body)
    assert body == {"balance": "50000.00"}


def test_wallet_404_matches_problem_schema(
    logged_in_client: FlaskClient, seeded_users: list[SeededUser], spec: dict[str, Any]
) -> None:
    """HU-05 CA-5."""
    response = logged_in_client.get("/api/v1/wallet")

    assert response.status_code == 404
    _validate(spec, "Problem", response.get_json())


def test_path_declares_get_with_200_401_and_404(spec: dict[str, Any]) -> None:
    responses = spec["paths"]["/api/v1/wallet"]["get"]["responses"]

    assert {"200", "401", "404"} <= set(responses)
