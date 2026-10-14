"""request_id y log de acceso (observability.md)."""

from __future__ import annotations

import logging

import pytest
from flask import Flask
from flask.testing import FlaskClient


def test_request_id_is_echoed_when_provided(client: FlaskClient) -> None:
    response = client.get("/health", headers={"X-Request-Id": "abc123"})

    assert response.headers["X-Request-Id"] == "abc123"


def test_request_id_is_generated_when_absent(client: FlaskClient) -> None:
    response = client.get("/health")

    assert len(response.headers["X-Request-Id"]) == 12


def test_slow_request_is_logged_as_warning(
    app: Flask, client: FlaskClient, caplog: pytest.LogCaptureFixture
) -> None:
    """Estable de nuevo: migrations/env.py ya no desactiva los loggers existentes."""
    app.config["SLOW_REQUEST_MS"] = -1

    with caplog.at_level(logging.INFO, logger="app.access"):
        client.get("/health")

    records = [r for r in caplog.records if r.name == "app.access"]
    assert records[-1].levelno == logging.WARNING
    assert records[-1].getMessage() == "request.slow"
