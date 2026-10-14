"""Errores de negocio y respuestas RFC 9457 (application/problem+json)."""

from __future__ import annotations

import logging
from typing import Any

from flask import Flask, Response, g, jsonify, request
from flask_limiter.errors import RateLimitExceeded
from pydantic import ValidationError as PydanticValidationError
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


class DuplicateIdentityError(AppError):
    status = 409
    code = "duplicate_identity"
    title = "Cuenta ya registrada"

    def __init__(self) -> None:
        super().__init__("Ya existe una cuenta con alguno de esos datos.")


class InvalidJsonError(AppError):
    status = 400
    code = "invalid_json"
    title = "JSON inválido"

    def __init__(self) -> None:
        super().__init__("Envía un cuerpo JSON válido.")


class ValidationError(AppError):
    status = 422
    code = "validation"
    title = "Datos inválidos"


class MissingIdempotencyKeyError(AppError):
    status = 400
    code = "missing_idempotency_key"
    title = "Cabecera Idempotency-Key requerida"


class IdempotencyKeyMismatchError(AppError):
    status = 422
    code = "idempotency_key_mismatch"
    title = "Idempotency-Key reutilizada con otra solicitud"


def problem_body(exc: AppError, instance: str, request_id: str | None) -> dict[str, Any]:
    """Cuerpo RFC 9457 de un error de negocio; lo usan el handler y la persistencia idempotente."""
    body: dict[str, Any] = {
        "type": PROBLEM_BASE + exc.code,
        "title": exc.title,
        "status": exc.status,
        "detail": exc.detail,
        "instance": instance,
        "code": exc.code,
        "request_id": request_id,
    }
    if exc.errors:
        body["errors"] = exc.errors
    return body


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
        response = jsonify(problem_body(exc, request.path, getattr(g, "request_id", None)))
        response.status_code = exc.status
        response.mimetype = "application/problem+json"
        return response

    @app.errorhandler(PydanticValidationError)
    def handle_pydantic_error(exc: PydanticValidationError) -> Response:
        errors = [
            {"field": ".".join(str(part) for part in error["loc"]), "message": error["msg"]}
            for error in exc.errors()
        ]
        return problem(422, "validation", "Datos inválidos", errors=errors)

    @app.errorhandler(RateLimitExceeded)
    def handle_rate_limit(exc: RateLimitExceeded) -> Response:
        log.info("rate_limit.exceeded", extra={"path": request.path})
        return problem(
            429, "too_many_attempts", "Demasiados intentos", "Intenta de nuevo más tarde."
        )

    @app.errorhandler(HTTPException)
    def handle_http_error(exc: HTTPException) -> Response:
        status = exc.code or 500
        code = (exc.name or "http_error").lower().replace(" ", "_")
        return problem(status, code, exc.name or "Error HTTP", exc.description or "")

    @app.errorhandler(Exception)
    def handle_unexpected(exc: Exception) -> Response:
        log.exception("unhandled.exception")
        return problem(500, "internal_error", "Error interno", "Ocurrió un error inesperado.")
