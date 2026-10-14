"""Titulares de billeteras para otros módulos (HU-09 CA-3)."""

from __future__ import annotations

import pytest
from flask import Flask

from app.modules.wallet import service
from tests.factories import SeededUser

pytestmark = pytest.mark.mysql


def test_get_wallet_owners_maps_wallet_to_user_phone(
    app: Flask, seeded_users: list[SeededUser]
) -> None:
    """HU-09 CA-3: movements obtiene la contraparte sin tocar wallets ni users."""
    w1 = service.create_wallet(1)
    w2 = service.create_wallet(2)

    owners = service.get_wallet_owners([w1, w2, 999])

    assert set(owners) == {w1, w2}
    assert owners[w1] == service.WalletOwner(
        wallet_id=w1, user_id=1, phone=seeded_users[0].phone, full_name=None
    )
    assert owners[w2].user_id == 2


def test_get_wallet_owners_with_no_ids_returns_empty_dict(
    app: Flask, seeded_users: list[SeededUser]
) -> None:
    assert service.get_wallet_owners([]) == {}
