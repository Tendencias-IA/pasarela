"""Errores de negocio y respuestas RFC 9457 (application/problem+json)."""

from __future__ import annotations

import logging
from typing import Any

from flask import Flask, Response, g, jsonify, request
from werkzeug.exceptions import HTTPException

PROBLEM_BASE = "https://pasarela.local/problems/"
log = logging.getLogger("app.errors")


class AppError(Exception):
    """Error de negocio. Subclases fijan `status`, `code` y `title`."""

    status = 400
    code = "app_error"
    title = "Error de la aplicación"

    def __init__(self, detail: str = "", errors: list[dict[str, str]] | None = None) -> None:
        super().__init__(detail or self.title)
        self.detail = detail
        self.errors = errors or []


class ValidationError(AppError):
    status = 422
    code = "validation"
    title = "Datos inválidos"


def problem(
    status: int, code: str, title: str, detail: str = "", errors: list[dict[str, str]] | None = None
) -> Response:
    body: dict[str, Any] = {
        "type": PROBLEM_BASE + code,
        "title": title,
        "status": status,
        "detail": detail,
        "instance": request.path,
        "code": code,
        "request_id": getattr(g, "request_id", None),
    }
    if errors:
        body["errors"] = errors
    response = jsonify(body)
    response.status_code = status
    response.mimetype = "application/problem+json"
    return response


def init_app(app: Flask) -> None:
    @app.errorhandler(AppError)
    def handle_app_error(exc: AppError) -> Response:
        log.info("business.rejected", extra={"code": exc.code, "status": exc.status})
        return problem(exc.status, exc.code, exc.title, exc.detail, exc.errors)

    @app.errorhandler(HTTPException)
    def handle_http_error(exc: HTTPException) -> Response:
        status = exc.code or 500
        code = (exc.name or "http_error").lower().replace(" ", "_")
        return problem(status, code, exc.name or "Error HTTP", exc.description or "")

    @app.errorhandler(Exception)
    def handle_unexpected(exc: Exception) -> Response:
        log.exception("unhandled.exception")
        return problem(500, "internal_error", "Error interno", "Ocurrió un error inesperado.")
