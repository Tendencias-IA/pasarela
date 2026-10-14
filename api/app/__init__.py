"""App factory de la API. Ver .claude/rules/api.md y architecture.md."""

from __future__ import annotations

import os

from flask import Flask

from app.common import errors, health, security
from app.common import logging as app_logging
from app.config import get_config
from app.extensions import db, limiter, migrate
from app.modules.accounts.routes import blueprint as accounts_bp
from app.modules.auth.routes import bp as auth_bp


def create_app(config_name: str | None = None) -> Flask:
    """Construye la aplicación. Si no se pasa `config_name`, se lee de `APP_CONFIG`."""
    config_name = config_name or os.environ.get("APP_CONFIG", "development")
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    app_logging.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    errors.init_app(app)
    security.init_app(app)

    app.register_blueprint(health.bp)
    app.register_blueprint(accounts_bp)
    app.register_blueprint(auth_bp)
    # Los módulos de negocio (wallet, transfers, movements) se registran aquí a medida
    # que se implementan sus historias, con prefijo /api/v1.
    return app
