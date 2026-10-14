"""Configuraciones por ambiente. Los secretos solo vienen de variables de entorno."""

from __future__ import annotations

import os
from datetime import timedelta


class ConfigError(RuntimeError):
    """Falta una variable de entorno obligatoria."""


def _required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        msg = f"Falta la variable de entorno obligatoria {name}"
        raise ConfigError(msg)
    return value


class BaseConfig:
    APP_NAME = "pasarela-api"
    TESTING = False
    DEBUG = False
    JSON_SORT_KEYS = False
    MAX_CONTENT_LENGTH = 16 * 1024
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_NAME = "session"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = True
    RATELIMIT_ENABLED = True
    SLOW_REQUEST_MS = 3000

    def __init__(self) -> None:
        self.SECRET_KEY = _required("SECRET_KEY")
        self.SQLALCHEMY_DATABASE_URI = _required("DATABASE_URL")
        self.SESSION_IDLE = timedelta(minutes=int(os.environ.get("SESSION_IDLE_MINUTES", "5")))
        self.LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class TestingConfig(BaseConfig):
    TESTING = True
    SESSION_COOKIE_SECURE = False
    RATELIMIT_ENABLED = False


class E2EConfig(BaseConfig):
    """Igual que producción pero sobre http://127.0.0.1: sin cookie Secure ni rate limit."""

    SESSION_COOKIE_SECURE = False
    RATELIMIT_ENABLED = False


class ProductionConfig(BaseConfig):
    pass


CONFIGS: dict[str, type[BaseConfig]] = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "e2e": E2EConfig,
    "production": ProductionConfig,
}


def get_config(name: str) -> BaseConfig:
    try:
        return CONFIGS[name]()
    except KeyError as exc:
        msg = f"APP_CONFIG desconocido: {name!r}. Opciones: {', '.join(CONFIGS)}"
        raise ConfigError(msg) from exc
