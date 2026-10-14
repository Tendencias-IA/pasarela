"""Unitarias de accounts.service con repositorio falso (testing.md)."""

from __future__ import annotations

from unittest.mock import patch

from app.modules.accounts import service
from app.modules.accounts.models import User


def test_get_user_by_phone_returns_user_when_repository_finds_it() -> None:
    user = User(id=1, phone="3009876543", password_hash="hash")

    with patch("app.modules.accounts.service.repository.get_by_phone", return_value=user):
        result = service.get_user_by_phone("3009876543")

    assert result is user


def test_get_user_by_phone_returns_none_when_repository_finds_nothing() -> None:
    with patch("app.modules.accounts.service.repository.get_by_phone", return_value=None):
        result = service.get_user_by_phone("3000000000")

    assert result is None
