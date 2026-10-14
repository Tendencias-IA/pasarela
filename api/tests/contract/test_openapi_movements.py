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


def test_wallet_balance_200_matches_wallet_out_schema(
    logged_in_client: FlaskClient, seeded_users: list[SeededUser], spec: dict[str, Any]
) -> None:
    """HU-05 CA-2: el saldo viaja como cadena decimal con dos decimales."""
    wallet_service.create_wallet(1)

    response = logged_in_client.get("/api/v1/wallet")

    assert response.status_code == 200
    _validate(spec, "WalletOut", response.get_json())
    assert "get" in spec["paths"]["/api/v1/wallet"]


def _recharge(client: FlaskClient, suffix: str, amount: str = "50000.00") -> None:
    client.post(
        "/api/v1/wallet/recharges",
        json={"amount": amount},
        headers={
            "X-Requested-With": "fetch",
            "Idempotency-Key": f"00000000-0000-4000-8000-0000000000{suffix}",
        },
    )


def test_filtered_200_matches_schema(
    logged_in_client: FlaskClient, seeded_users: list[SeededUser], spec: dict[str, Any]
) -> None:
    """HU-10 CA-3, CA-4: la respuesta filtrada cumple MovementsPageOut."""
    wallet_service.create_wallet(1)
    _recharge(logged_in_client, "31")

    body = logged_in_client.get(
        "/api/v1/movements?type=recharge&from=2000-01-01&to=2999-12-31"
    ).get_json()
    empty = logged_in_client.get("/api/v1/movements?type=sent").get_json()

    _validate(spec, "MovementsPageOut", body)
    _validate(spec, "MovementsPageOut", empty)
    assert body["total"] == 1 and empty["total"] == 0


@pytest.mark.parametrize(
    ("query", "code", "fields"),
    [
        ("from=2026-12-31&to=2026-01-01", "invalid_date_range", None),
        ("from=hoy&type=foo", "validation", ["from", "type"]),
    ],
)
def test_filter_errors_match_problem_schema(
    logged_in_client: FlaskClient,
    seeded_users: list[SeededUser],
    spec: dict[str, Any],
    query: str,
    code: str,
    fields: list[str] | None,
) -> None:
    """HU-10 CA-2: los dos 422 cumplen Problem y están declarados en el contrato."""
    wallet_service.create_wallet(1)

    response = logged_in_client.get(f"/api/v1/movements?{query}")

    assert response.status_code == 422
    body = response.get_json()
    _validate(spec, "Problem", body)
    assert body["code"] == code
    if fields:
        assert [e["field"] for e in body["errors"]] == fields


def test_filter_parameters_are_declared_in_openapi(spec: dict[str, Any]) -> None:
    """HU-10: from, to y type documentados con su lista blanca."""
    params = {p["name"]: p for p in spec["paths"]["/api/v1/movements"]["get"]["parameters"]}

    assert {"page", "from", "to", "type"} <= set(params)
    assert params["type"]["schema"]["enum"] == ["all", "sent", "received", "recharge"]
    assert params["type"]["schema"]["default"] == "all"
    assert (
        "invalid_date_range"
        in spec["paths"]["/api/v1/movements"]["get"]["responses"]["422"]["description"]
    )
