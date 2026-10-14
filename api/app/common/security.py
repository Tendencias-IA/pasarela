"""Cabeceras de seguridad fijas y defensa CSRF complementaria (ver security.md)."""

from __future__ import annotations

from flask import Flask, Response, request

from app.common.errors import AppError

SECURITY_HEADERS = {
    "Content-Security-Policy": "default-src 'self'",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "X-Frame-Options": "DENY",
}
MUTATING_METHODS = {"POST", "PATCH", "PUT", "DELETE"}


class MissingRequestedWithError(AppError):
    status = 403
    code = "missing_requested_with"
    title = "Cabecera X-Requested-With requerida"


def init_app(app: Flask) -> None:
    @app.before_request
    def require_requested_with() -> None:
        if (
            request.method in MUTATING_METHODS
            and request.headers.get("X-Requested-With") != "fetch"
        ):
            raise MissingRequestedWithError("Toda mutación debe enviar X-Requested-With: fetch.")

    @app.after_request
    def add_security_headers(response: Response) -> Response:
        for name, value in SECURITY_HEADERS.items():
            response.headers.setdefault(name, value)
        return response
