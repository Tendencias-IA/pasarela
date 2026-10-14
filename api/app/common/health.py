"""GET /health: público, sin sesión, verifica la base de datos (ver observability.md)."""

from __future__ import annotations

import logging

from flask import Blueprint, Response, jsonify
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db

bp = Blueprint("health", __name__)
log = logging.getLogger("app.health")


@bp.get("/health")
def health() -> tuple[Response, int]:
    try:
        db.session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        log.exception("health.db_error")
        return jsonify({"status": "degraded", "db": "error"}), 503
    return jsonify({"status": "ok", "db": "ok"}), 200
