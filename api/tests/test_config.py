"""Selección de configuración y variables obligatorias (api.md)."""

from __future__ import annotations

import pytest

from app import create_app
from app.config import ConfigError, get_config


def test_create_app_reads_app_config_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_CONFIG", "e2e")

    app = create_app()

    assert app.config["SESSION_COOKIE_SECURE"] is False
    assert app.config["RATELIMIT_ENABLED"] is False
    assert app.config["TESTING"] is False


def test_create_app_defaults_to_development(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("APP_CONFIG", raising=False)

    assert create_app().config["DEBUG"] is True


def test_production_config_uses_secure_cookie() -> None:
    config = get_config("production")

    assert config.SESSION_COOKIE_SECURE is True
    assert config.SESSION_COOKIE_HTTPONLY is True
    assert config.SESSION_COOKIE_SAMESITE == "Lax"


def test_unknown_config_name_fails_loudly() -> None:
    with pytest.raises(ConfigError, match="desconocido"):
        get_config("staging")


def test_missing_secret_key_prevents_startup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SECRET_KEY")

    with pytest.raises(ConfigError, match="SECRET_KEY"):
        create_app("testing")
