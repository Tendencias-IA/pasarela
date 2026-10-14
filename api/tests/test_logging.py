"""request_id y log de acceso (observability.md)."""

from __future__ import annotations

from flask.testing import FlaskClient


def test_request_id_is_echoed_when_provided(client: FlaskClient) -> None:
    response = client.get("/health", headers={"X-Request-Id": "abc123"})

    assert response.headers["X-Request-Id"] == "abc123"


def test_request_id_is_generated_when_absent(client: FlaskClient) -> None:
    response = client.get("/health")

    assert len(response.headers["X-Request-Id"]) == 12


# NOTA: se retiró aquí `test_slow_request_is_logged_as_warning` por pedido explícito
# del usuario para desbloquear el push ya. Se volvió intermitente al correr junto con
# el resto de la suite: `caplog` depende de ser el único handler nuevo del logger raíz
# durante el test, y al crecer la suite con más llamadas a create_app() antes de este
# test, el orden de inicialización del logging deja de garantizarlo. El comportamiento
# en sí (request.slow en WARNING) no cambió.
