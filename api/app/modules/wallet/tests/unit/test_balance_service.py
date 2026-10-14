"""Consulta de saldo con repositorio falso (HU-05)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from flask import Flask

from app.modules.wallet import service
from app.modules.wallet.service import WalletNotFoundError
from app.modules.wallet.tests.unit.fakes import FakeWalletRepository


def test_get_balance_returns_the_exact_persisted_decimal(
    app: Flask,
) -> None:
    """HU-05 CA-1 y CA-2: no calcula ni redondea el saldo."""
    repo = FakeWalletRepository({1: Decimal("123456.70")})

    result = service.get_balance(1, repo=repo)

    assert result.balance == Decimal("123456.70")


def test_get_balance_without_wallet_raises_not_found(app: Flask) -> None:
    """HU-05 CA-5."""
    repo = FakeWalletRepository()

    with pytest.raises(WalletNotFoundError) as excinfo:
        service.get_balance(1, repo=repo)

    assert excinfo.value.code == "wallet_not_found"
