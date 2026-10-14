"""Contrato de /transfers/preview: las respuestas reales cumplen api/openapi.yaml."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
import yaml
from flask.testing import FlaskClient
from jsonschema import Draft202012Validator, RefResolver
from sqlalchemy import select

from app.extensions import db
from app.modules.wallet import service as wallet_service
from app.modules.wallet.models import Wallet
from tests.factories import SeededUser

OPENAPI = Path(__file__).resolve().parents[2] / "openapi.yaml"
HEADERS = {"X-Requested-With": "fetch"}


@pytest.fixture(scope="module")
def spec() -> dict[str, Any]:
    return yaml.safe_load(OPENAPI.read_text())


def _validate(spec: dict[str, Any], schema_name: str, body: Any) -> None:
    schema = spec["components"]["schemas"][schema_name]
    Draft202012Validator(schema, resolver=RefResolver.from_schema(spec)).validate(body)


def _post(client: FlaskClient, phone: str, amount: str) -> Any:
    return client.post(
        "/api/v1/transfers/preview",
        json={"recipient_phone": phone, "amount": amount},
        headers=HEADERS,
    )


@pytest.fixture
def two_wallets(seeded_users: list[SeededUser]) -> list[SeededUser]:
    wallet_service.create_wallet(1)
    wallet_service.create_wallet(2)
    wallet = db.session.execute(select(Wallet).where(Wallet.user_id == 1)).scalar_one()
    wallet.balance = Decimal("50000.00")
    db.session.commit()
    return seeded_users


@pytest.mark.mysql
def test_preview_200_matches_schema(
    logged_in_client: FlaskClient, two_wallets: list[SeededUser], spec: dict[str, Any]
) -> None:
    response = _post(logged_in_client, two_wallets[1].phone, "1000.00")

    assert response.status_code == 200
    _validate(spec, "TransferPreviewOut", response.get_json())


@pytest.mark.mysql
@pytest.mark.parametrize(
    ("phone", "amount", "status"), [("3999999999", "1000.00", 404), ("x", "1", 422)]
)
def test_preview_errors_match_problem_schema(
    logged_in_client: FlaskClient,
    two_wallets: list[SeededUser],
    spec: dict[str, Any],
    phone: str,
    amount: str,
    status: int,
) -> None:
    response = _post(logged_in_client, phone, amount)

    assert response.status_code == status
    assert response.mimetype == "application/problem+json"
    _validate(spec, "Problem", response.get_json())
    assert str(status) in spec["paths"]["/api/v1/transfers/preview"]["post"]["responses"]


def test_preview_contract_is_a_pure_query(spec: dict[str, Any]) -> None:
    """HU-06 CA-8: sin Idempotency-Key; el cuerpo no admite campos extra."""
    operation = spec["paths"]["/api/v1/transfers/preview"]["post"]
    names = {p["name"] for p in operation["parameters"]}

    assert names == {"X-Requested-With"}
    assert spec["components"]["schemas"]["TransferIn"]["additionalProperties"] is False


def _confirm(client: FlaskClient, phone: str, amount: str) -> Any:
    return client.post(
        "/api/v1/transfers",
        json={"recipient_phone": phone, "amount": amount},
        headers={**HEADERS, "Idempotency-Key": "00000000-0000-4000-8000-0000000000d1"},
    )


@pytest.mark.mysql
def test_confirm_201_matches_transfer_out_schema(
    logged_in_client: FlaskClient, two_wallets: list[SeededUser], spec: dict[str, Any]
) -> None:
    """HU-07 CA-7."""
    response = _confirm(logged_in_client, two_wallets[1].phone, "1000.00")

    assert response.status_code == 201
    _validate(spec, "TransferOut", response.get_json())
    assert "201" in spec["paths"]["/api/v1/transfers"]["post"]["responses"]


@pytest.mark.mysql
def test_confirm_422_matches_problem_schema(
    logged_in_client: FlaskClient, two_wallets: list[SeededUser], spec: dict[str, Any]
) -> None:
    response = _confirm(logged_in_client, two_wallets[1].phone, "900000.00")

    assert response.status_code == 422
    assert response.mimetype == "application/problem+json"
    _validate(spec, "Problem", response.get_json())


def test_confirm_contract_requires_idempotency_key_and_declares_errors(
    spec: dict[str, Any],
) -> None:
    """HU-07 CA-8, ADR-0005."""
    operation = spec["paths"]["/api/v1/transfers"]["post"]
    params = {p["name"]: p for p in operation["parameters"]}

    assert params["Idempotency-Key"]["required"] is True
    assert params["X-Requested-With"]["required"] is True
    assert {"201", "400", "401", "404", "422"} <= set(operation["responses"])
    assert spec["components"]["schemas"]["TransferOut"]["properties"]["status"]["enum"] == [
        "exitosa"
    ]
