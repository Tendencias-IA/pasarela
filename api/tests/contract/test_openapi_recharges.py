"""Contrato: las respuestas reales cumplen api/openapi.yaml (testing.md)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from flask.testing import FlaskClient
from jsonschema import Draft202012Validator, RefResolver

from app.modules.wallet import service
from tests.factories import SeededUser

OPENAPI = Path(__file__).resolve().parents[2] / "openapi.yaml"
KEY = "00000000-0000-4000-8000-000000000011"


@pytest.fixture(scope="module")
def spec() -> dict[str, Any]:
    return yaml.safe_load(OPENAPI.read_text())


def _validate(spec: dict[str, Any], schema_name: str, body: Any) -> None:
    schema = spec["components"]["schemas"][schema_name]
    resolver = RefResolver.from_schema(spec)
    Draft202012Validator(schema, resolver=resolver).validate(body)


@pytest.mark.mysql
def test_recharge_201_matches_recharge_out_schema(
    logged_in_client: FlaskClient, seeded_users: list[SeededUser], spec: dict[str, Any]
) -> None:
    service.create_wallet(1)

    response = logged_in_client.post(
        "/api/v1/wallet/recharges",
        json={"amount": "50000.00"},
        headers={"X-Requested-With": "fetch", "Idempotency-Key": KEY},
    )

    assert response.status_code == 201
    _validate(spec, "RechargeOut", response.get_json())
    assert "201" in spec["paths"]["/api/v1/wallet/recharges"]["post"]["responses"]


@pytest.mark.mysql
def test_recharge_422_matches_problem_schema(
    logged_in_client: FlaskClient, seeded_users: list[SeededUser], spec: dict[str, Any]
) -> None:
    service.create_wallet(1)

    response = logged_in_client.post(
        "/api/v1/wallet/recharges",
        json={"amount": "4999.00"},
        headers={"X-Requested-With": "fetch", "Idempotency-Key": KEY},
    )

    assert response.status_code == 422
    assert response.mimetype == "application/problem+json"
    _validate(spec, "Problem", response.get_json())


def test_contract_declares_required_headers(spec: dict[str, Any]) -> None:
    params = {p["name"]: p for p in spec["paths"]["/api/v1/wallet/recharges"]["post"]["parameters"]}
    assert params["Idempotency-Key"]["required"] is True
    assert params["X-Requested-With"]["required"] is True
    assert spec["components"]["schemas"]["RechargeIn"]["additionalProperties"] is False
