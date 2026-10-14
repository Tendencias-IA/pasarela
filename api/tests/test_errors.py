"""Formato de error RFC 9457 (api-design.md)."""

from __future__ import annotations

from flask import Flask
from flask.testing import FlaskClient

from app.common.errors import AppError, ValidationError


class InsufficientBalanceError(AppError):
    status = 422
    code = "insufficient_balance"
    title = "Saldo insuficiente"


def test_unknown_route_returns_problem_json(client: FlaskClient) -> None:
    response = client.get("/no-existe")

    assert response.status_code == 404
    assert response.mimetype == "application/problem+json"
    body = response.get_json()
    assert body["code"] == "not_found"
    assert body["instance"] == "/no-existe"
    assert body["request_id"]


def test_app_error_maps_status_code_and_detail(app: Flask, client: FlaskClient) -> None:
    @app.get("/_rechazo")
    def rechazo() -> str:
        raise InsufficientBalanceError("El saldo disponible es menor que el monto solicitado.")

    response = client.get("/_rechazo")

    assert response.status_code == 422
    body = response.get_json()
    assert body["type"].endswith("/insufficient_balance")
    assert body["title"] == "Saldo insuficiente"
    assert body["detail"] == "El saldo disponible es menor que el monto solicitado."
    assert "errors" not in body


def test_validation_error_lists_every_field(app: Flask, client: FlaskClient) -> None:
    @app.get("/_validacion")
    def validacion() -> str:
        raise ValidationError(errors=[{"field": "phone", "message": "Debe tener 10 dígitos"}])

    body = client.get("/_validacion").get_json()

    assert body["status"] == 422
    assert body["errors"] == [{"field": "phone", "message": "Debe tener 10 dígitos"}]


def test_unexpected_exception_returns_generic_500(app: Flask, client: FlaskClient) -> None:
    @app.get("/_explota")
    def explota() -> str:
        raise RuntimeError("detalle interno que no debe filtrarse")

    response = client.get("/_explota")

    assert response.status_code == 500
    body = response.get_json()
    assert body["code"] == "internal_error"
    assert "interno que no debe" not in body["detail"]
