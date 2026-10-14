"""Preparar contra MySQL real no emite escrituras ni bloqueos (HU-06 CA-8)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from flask import Flask
from sqlalchemy import event

from app.extensions import db
from app.modules.transfers import service
from app.modules.wallet import service as wallet_service
from tests.factories import SeededUser

pytestmark = pytest.mark.mysql


def test_preview_with_real_services_emits_only_selects(
    app: Flask, seeded_users: list[SeededUser]
) -> None:
    """HU-06 CA-8: ni INSERT, ni UPDATE, ni FOR UPDATE."""
    wallet_service.create_wallet(1)
    wallet_service.create_wallet(2)
    statements: list[str] = []

    def capture(conn: object, cursor: object, statement: str, *args: object) -> None:
        statements.append(statement.strip().upper())

    event.listen(db.engine, "before_cursor_execute", capture)
    try:
        with pytest.raises(wallet_service.InsufficientBalanceError):
            service.preview_transfer(1, seeded_users[1].phone, Decimal("1000.00"))
    finally:
        event.remove(db.engine, "before_cursor_execute", capture)

    assert statements, "debió consultar al menos el destinatario"
    assert all(s.startswith("SELECT") and "FOR UPDATE" not in s for s in statements)
