"""Contrato: GET /api/v1/auth/session cumple api/openapi.yaml (HU-04, FR-005)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from flask import Flask
from flask.testing import FlaskClient
from jsonschema import Draft202012Validator, RefResolver

from tests.factories import SeededUser

OPENAPI = Path(__file__).resolve().parents[2] / "openapi.yaml"
URL = "/api/v1/auth/session"

pytestmark = pytest.mark.mysql


@pytest.fixture(scope="module")
def spec() -> dict[str, Any]:
    return yaml.safe_load(OPENAPI.read_text())


def _validate(spec: dict[str, Any], schema_name: str, body: Any) -> None:
    schema = spec["components"]["schemas"][schema_name]
    resolver = RefResolver.from_schema(spec)
    Draft202012Validator(schema, resolver=resolver).validate(body)


def test_session_200_matches_session_out_schema(
    client: FlaskClient, seeded_users: list[SeededUser], spec: dict[str, Any]
) -> None:
    """HU-04 CA-4."""
    seeded = seeded_users[0]
    client.post(
        "/api/v1/auth/login",
        json={"phone": seeded.phone, "password": seeded.password},
        headers={"X-Requested-With": "fetch"},
    )

    response = client.get(URL)

    assert response.status_code == 200
    body = response.get_json()
    _validate(spec, "SessionOut", body)
    assert body["expires_at"].endswith("Z")


def test_session_401_matches_problem_schema(app: Flask, spec: dict[str, Any]) -> None:
    """HU-04 CA-2."""
    response = app.test_client().get(URL)

    assert response.status_code == 401
    assert response.mimetype == "application/problem+json"
    body = response.get_json()
    _validate(spec, "Problem", body)
    assert body["code"] == "invalid_session"


def test_path_is_declared_in_openapi(spec: dict[str, Any]) -> None:
    assert "get" in spec["paths"][URL]
    assert "SessionOut" in spec["components"]["schemas"]
