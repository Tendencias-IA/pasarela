"""Resumen público de usuarios por id para otros módulos (HU-09 CA-3)."""

from __future__ import annotations

import pytest
from flask import Flask

from app.modules.accounts import service
from tests.factories import SeededUser

pytestmark = pytest.mark.mysql


def test_get_users_by_ids_returns_summaries_for_existing_ids(
    app: Flask, seeded_users: list[SeededUser]
) -> None:
    """HU-09 CA-3: el módulo movements resuelve la contraparte vía accounts_service."""
    result = service.get_users_by_ids([1, 2, 99])

    assert set(result) == {1, 2}
    assert result[1] == service.UserSummary(id=1, phone=seeded_users[0].phone, full_name=None)
    assert result[2].phone == seeded_users[1].phone


def test_get_users_by_ids_with_no_ids_returns_empty_dict(
    app: Flask, seeded_users: list[SeededUser]
) -> None:
    assert service.get_users_by_ids([]) == {}
