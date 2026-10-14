"""Unitarias de auth.service con accounts y repository falsos (testing.md).

HU-02 CA-1 a CA-5 citados en cada test.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from flask import Flask

from app.modules.accounts.models import User
from app.modules.auth import service
from app.modules.auth.models import Session


def _user(password_hash: str) -> User:
    return User(id=7, phone="3009876543", password_hash=password_hash)


def test_login_valid_credentials_returns_session(app: Flask) -> None:
    """HU-02 CA-1."""
    from app.common.passwords import hash_password

    user = _user(hash_password("Clave1234"))
    created = Session(id=1, user_id=user.id, token_hash="x", expires_at=datetime.now(UTC))

    with (
        patch("app.modules.auth.service.accounts_service.get_user_by_phone", return_value=user),
        patch("app.modules.auth.service.repository.create_session", return_value=created),
    ):
        result = service.login("3009876543", "Clave1234")

    assert result.session is created
    assert isinstance(result.token, str) and len(result.token) > 20


def test_login_unknown_phone_raises_invalid_credentials(app: Flask) -> None:
    """HU-02 CA-2, CA-3."""
    with (
        patch("app.modules.auth.service.accounts_service.get_user_by_phone", return_value=None),
        pytest.raises(service.InvalidCredentialsError) as exc_info,
    ):
        service.login("3000000000", "cualquiera")

    assert exc_info.value.code == "invalid_credentials"


def test_login_wrong_password_raises_same_invalid_credentials_error(app: Flask) -> None:
    """HU-02 CA-2, CA-3."""
    from app.common.passwords import hash_password

    user = _user(hash_password("Clave1234"))

    with (
        patch("app.modules.auth.service.accounts_service.get_user_by_phone", return_value=user),
        pytest.raises(service.InvalidCredentialsError) as exc_info,
    ):
        service.login("3009876543", "incorrecta")

    assert exc_info.value.code == "invalid_credentials"


def test_login_never_raises_with_raw_password_in_message(app: Flask) -> None:
    """HU-02 CA-4, RNF-06.4."""
    secret_password = "ClaveSecreta99"

    with (
        patch("app.modules.auth.service.accounts_service.get_user_by_phone", return_value=None),
        pytest.raises(service.InvalidCredentialsError) as exc_info,
    ):
        service.login("3000000000", secret_password)

    assert secret_password not in str(exc_info.value)
    assert secret_password not in exc_info.value.detail


def test_current_session_without_token_returns_none() -> None:
    """FR-005."""
    assert service.get_current_session(None) is None


def test_current_session_with_revoked_session_returns_none(app: Flask) -> None:
    """FR-005, FR-006."""
    token = "un-token-cualquiera"
    token_hash = service._hash_token(token)
    revoked = Session(
        id=1,
        user_id=7,
        token_hash=token_hash,
        expires_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=5),
        revoked_at=datetime.now(UTC).replace(tzinfo=None),
    )

    with patch("app.modules.auth.service.repository.get_by_token_hash", return_value=revoked):
        assert service.get_current_session(token) is None


def test_current_session_with_expired_session_returns_none(app: Flask) -> None:
    """FR-005, FR-006."""
    token = "otro-token"
    token_hash = service._hash_token(token)
    expired = Session(
        id=2,
        user_id=7,
        token_hash=token_hash,
        expires_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=1),
        revoked_at=None,
    )

    with patch("app.modules.auth.service.repository.get_by_token_hash", return_value=expired):
        assert service.get_current_session(token) is None
