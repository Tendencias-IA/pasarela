"""Fixtures base: app en configuración `testing` y cliente HTTP (ver testing.md)."""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app import create_app

os.environ.setdefault("SECRET_KEY", "clave-de-pruebas-no-secreta")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")


@pytest.fixture
def app() -> Iterator[Flask]:
    application = create_app("testing")
    with application.app_context():
        yield application


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()
