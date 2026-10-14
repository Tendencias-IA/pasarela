"""Cabeceras de seguridad y X-Requested-With (security.md)."""

from __future__ import annotations

from flask import Flask
from flask.testing import FlaskClient


def test_every_response_carries_security_headers(client: FlaskClient) -> None:
    headers = client.get("/health").headers

    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["Content-Security-Policy"] == "default-src 'self'"
    assert headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


def test_mutation_without_requested_with_is_rejected(app: Flask, client: FlaskClient) -> None:
    @app.post("/_mutacion")
    def mutacion() -> dict[str, bool]:
        return {"ok": True}

    rejected = client.post("/_mutacion")
    accepted = client.post("/_mutacion", headers={"X-Requested-With": "fetch"})

    assert rejected.status_code == 403
    assert rejected.get_json()["code"] == "missing_requested_with"
    assert accepted.status_code == 200
