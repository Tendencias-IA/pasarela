"""Integración de /api/v1/auth/login contra MySQL real (testing.md).

HU-02: ver specs/001-ppa-2-iniciar-sesion/spec.md para los criterios de aceptación citados.
"""

from __future__ import annotations

from datetime import UTC, datetime

from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session as SqlAlchemySession

from app.common.auth import login_required
from app.modules.auth.models import Session
from tests.factories import make_phone, make_user

_HEADERS = {"X-Requested-With": "fetch"}


def test_post_login_valid_credentials_sets_session_cookie(
    integration_app: Flask, integration_client: FlaskClient, db_session: SqlAlchemySession
) -> None:
    """HU-02 CA-1; éxito es 204 sin cuerpo (.claude/rules/api-design.md)."""
    seeded = make_user(password="Clave1234")
    db_session.add(seeded.user)
    db_session.commit()

    response = integration_client.post(
        "/api/v1/auth/login",
        json={"phone": seeded.phone, "password": seeded.password},
        headers=_HEADERS,
    )

    assert response.status_code == 204
    assert response.data == b""
    assert "session=" in response.headers.get("Set-Cookie", "")


def test_post_login_unknown_phone_and_wrong_password_return_identical_body(
    integration_app: Flask, integration_client: FlaskClient, db_session: SqlAlchemySession
) -> None:
    """HU-02 CA-2, CA-3: mismo cuerpo para teléfono inexistente y contraseña incorrecta."""
    seeded = make_user(password="Clave1234")
    db_session.add(seeded.user)
    db_session.commit()

    unknown_response = integration_client.post(
        "/api/v1/auth/login",
        json={"phone": make_phone(), "password": "cualquiera123"},
        headers=_HEADERS,
    )
    wrong_password_response = integration_client.post(
        "/api/v1/auth/login",
        json={"phone": seeded.phone, "password": "incorrecta123"},
        headers=_HEADERS,
    )

    unknown_body = unknown_response.get_json()
    wrong_password_body = wrong_password_response.get_json()

    assert unknown_response.status_code == 401
    assert wrong_password_response.status_code == 401
    assert unknown_body["code"] == wrong_password_body["code"] == "invalid_credentials"
    assert unknown_body["title"] == wrong_password_body["title"]
    assert unknown_body["detail"] == wrong_password_body["detail"]
    assert db_session.query(Session).count() == 0


def test_private_probe_requires_valid_session(
    integration_app: Flask, integration_client: FlaskClient, db_session: SqlAlchemySession
) -> None:
    """FR-005: sin sesión no se puede acceder a una función privada."""

    @integration_app.get("/api/v1/_private_probe")
    @login_required
    def private_probe() -> dict[str, bool]:
        return {"ok": True}

    without_cookie = integration_client.get("/api/v1/_private_probe")
    assert without_cookie.status_code == 401
    assert without_cookie.get_json()["code"] == "unauthenticated"

    seeded = make_user(password="Clave1234")
    db_session.add(seeded.user)
    db_session.commit()
    integration_client.post(
        "/api/v1/auth/login",
        json={"phone": seeded.phone, "password": seeded.password},
        headers=_HEADERS,
    )

    with_cookie = integration_client.get("/api/v1/_private_probe")
    assert with_cookie.status_code == 200


def test_revoked_session_blocks_further_access_like_no_session(
    integration_app: Flask, integration_client: FlaskClient, db_session: SqlAlchemySession
) -> None:
    """FR-005, FR-006: revocada o ausente, misma respuesta."""

    @integration_app.get("/api/v1/_private_probe_2")
    @login_required
    def private_probe_2() -> dict[str, bool]:
        return {"ok": True}

    seeded = make_user(password="Clave1234")
    db_session.add(seeded.user)
    db_session.commit()
    integration_client.post(
        "/api/v1/auth/login",
        json={"phone": seeded.phone, "password": seeded.password},
        headers=_HEADERS,
    )

    # db_session parte limpia en cada prueba (ver conftest.py#db_session), así que la
    # única sesión existente en este punto es la que el login anterior acaba de crear.
    db_session.query(Session).update({"revoked_at": datetime.now(UTC).replace(tzinfo=None)})
    db_session.commit()

    response = integration_client.get("/api/v1/_private_probe_2")

    assert response.status_code == 401
    assert response.get_json()["code"] == "unauthenticated"


# NOTA: se retiró aquí una prueba de rate limit (5 intentos/15 min, security.md) por
# pedido explícito del usuario para desbloquear el push ya: `limiter` es un singleton
# que fija `enabled` una sola vez dentro de `limiter.init_app(app)` (en create_app),
# así que ni `integration_app.config["RATELIMIT_ENABLED"]` ni forzar el atributo en el
# test lograban un resultado estable entre ejecuciones. El rate limit en sí sigue
# activo en producción (BaseConfig.RATELIMIT_ENABLED = True); falta solo su prueba.
