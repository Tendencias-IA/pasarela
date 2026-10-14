"""Unitarias de la expiración deslizante (HU-04) con el reloj parcheado (testing.md).

`app.modules.auth.service.utcnow` y `app.modules.auth.repository.utcnow` son el único
reloj; los objetos `Session` son transitorios (no se añaden a `db.session`), así que
`transaction()` no escribe nada y las reglas se prueban sin base de datos.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from flask import Flask

from app.common import auth as common_auth
from app.modules.auth import repository, service
from app.modules.auth.models import Session

NOW = datetime(2026, 10, 14, 21, 40, 0)
IDLE = timedelta(minutes=5)
TOKEN = "token-de-prueba-no-secreto"


def _session(
    *, last_activity_at: datetime, expires_at: datetime, revoked_at: datetime | None = None
) -> Session:
    return Session(
        id=1,
        user_id=7,
        token_hash=service._hash_token(TOKEN),
        last_activity_at=last_activity_at,
        expires_at=expires_at,
        revoked_at=revoked_at,
    )


# --- Phase 2: base del umbral ----------------------------------------------------------


def test_create_session_sets_last_activity_with_python_clock(app: Flask) -> None:
    """HU-04 CA-4 (data-model.md: hora UTC de Python, nunca now() de MySQL)."""
    with patch("app.modules.auth.repository.utcnow", return_value=NOW):
        session = repository.create_session(7, "hash", NOW + IDLE)

    assert session.last_activity_at == NOW
    assert session.expires_at == NOW + IDLE


# --- US1: la sesión caduca --------------------------------------------------------------


def test_get_current_session_expired_marks_revoked_and_logs(
    app: Flask, caplog: pytest.LogCaptureFixture
) -> None:
    """HU-04 CA-1, RNF-06.2."""
    expired = _session(
        last_activity_at=NOW - IDLE - timedelta(seconds=1), expires_at=NOW - timedelta(seconds=1)
    )
    caplog.set_level(logging.INFO, logger="app.auth")

    with (
        patch("app.modules.auth.service.utcnow", return_value=NOW),
        patch("app.modules.auth.service.repository.get_by_token_hash", return_value=expired),
    ):
        result = service.get_current_session(TOKEN)

    assert result is None
    assert expired.revoked_at == NOW
    records = [r for r in caplog.records if r.getMessage() == "auth.session_expired"]
    assert len(records) == 1
    assert records[0].user_id == 7  # type: ignore[attr-defined]
    assert TOKEN not in caplog.text


def test_get_current_session_expired_exactly_at_boundary_is_rejected(app: Flask) -> None:
    """HU-04 CA-1: vencimiento inclusivo."""
    boundary = _session(last_activity_at=NOW - IDLE, expires_at=NOW)

    with (
        patch("app.modules.auth.service.utcnow", return_value=NOW),
        patch("app.modules.auth.service.repository.get_by_token_hash", return_value=boundary),
    ):
        assert service.get_current_session(TOKEN) is None

    assert boundary.revoked_at == NOW


def test_get_current_session_already_revoked_does_not_log_expiry(
    app: Flask, caplog: pytest.LogCaptureFixture
) -> None:
    """HU-04 CA-1: una sesión ya revocada no se revoca ni se loguea dos veces."""
    revoked_at = NOW - timedelta(minutes=1)
    revoked = _session(
        last_activity_at=NOW - IDLE, expires_at=NOW - timedelta(minutes=2), revoked_at=revoked_at
    )
    caplog.set_level(logging.INFO, logger="app.auth")

    with (
        patch("app.modules.auth.service.utcnow", return_value=NOW),
        patch("app.modules.auth.service.repository.get_by_token_hash", return_value=revoked),
    ):
        assert service.get_current_session(TOKEN) is None

    assert revoked.revoked_at == revoked_at
    assert "auth.session_expired" not in caplog.text


def test_get_current_session_active_returns_session_untouched(app: Flask) -> None:
    """HU-04 CA-4: validar no escribe; el toque es responsabilidad de touch_session."""
    active = _session(
        last_activity_at=NOW - timedelta(minutes=1), expires_at=NOW + timedelta(minutes=4)
    )

    with (
        patch("app.modules.auth.service.utcnow", return_value=NOW),
        patch("app.modules.auth.service.repository.get_by_token_hash", return_value=active),
    ):
        assert service.get_current_session(TOKEN) is active

    assert active.expires_at == NOW + timedelta(minutes=4)
    assert active.revoked_at is None


# --- US2: la actividad válida reinicia el periodo ---------------------------------------


def test_touch_session_extends_expiry_from_now(app: Flask) -> None:
    """HU-04 CA-4, RNF-01.3."""
    session = _session(
        last_activity_at=NOW - timedelta(seconds=60), expires_at=NOW + timedelta(minutes=4)
    )

    with patch("app.modules.auth.service.utcnow", return_value=NOW):
        expires_at = service.touch_session(session)

    assert expires_at == NOW + IDLE
    assert session.expires_at == NOW + IDLE
    assert session.last_activity_at == NOW


def test_touch_session_within_threshold_does_not_write(app: Flask) -> None:
    """HU-04 CA-4 (research.md: umbral de 10 s)."""
    previous_expiry = NOW + timedelta(minutes=4, seconds=57)
    session = _session(last_activity_at=NOW - timedelta(seconds=3), expires_at=previous_expiry)

    with patch("app.modules.auth.service.utcnow", return_value=NOW):
        expires_at = service.touch_session(session)

    assert expires_at == previous_expiry
    assert session.expires_at == previous_expiry
    assert session.last_activity_at == NOW - timedelta(seconds=3)


def test_touch_session_with_future_last_activity_still_writes(app: Flask) -> None:
    """HU-04 CA-4 (research.md: reloj de BD adelantado no bloquea la extensión)."""
    session = _session(
        last_activity_at=NOW + timedelta(seconds=30), expires_at=NOW + timedelta(minutes=4)
    )

    with patch("app.modules.auth.service.utcnow", return_value=NOW):
        expires_at = service.touch_session(session)

    assert expires_at == NOW + IDLE
    assert session.last_activity_at == NOW


def test_current_session_expires_at_without_session_raises(app: Flask) -> None:
    """HU-04 FR-005: sin sesión tocada en la petición no hay vencimiento que informar."""
    with app.test_request_context(), pytest.raises(service.InvalidSessionError):
        common_auth.current_session_expires_at()


def test_current_user_id_touches_session_and_exposes_expiry(app: Flask) -> None:
    """HU-04 CA-4: cada petición privada válida reinicia el periodo."""
    active = _session(
        last_activity_at=NOW - timedelta(minutes=1), expires_at=NOW + timedelta(minutes=4)
    )

    with (
        app.test_request_context(headers={"Cookie": f"session={TOKEN}"}),
        patch("app.modules.auth.service.utcnow", return_value=NOW),
        patch("app.modules.auth.service.repository.get_by_token_hash", return_value=active),
    ):
        user_id = common_auth.current_user_id()
        expires_at = common_auth.current_session_expires_at()

    assert user_id == 7
    assert expires_at == NOW + IDLE
    assert active.expires_at == NOW + IDLE
