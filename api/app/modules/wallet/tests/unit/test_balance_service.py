"""Consulta de saldo con repositorio falso (HU-05). Sin base de datos."""

from __future__ import annotations

import logging
from decimal import Decimal

import pytest
from flask import Flask

from app.modules.wallet import service
from app.modules.wallet.service import WalletNotFoundError
from app.modules.wallet.tests.unit.fakes import FakeWalletRepository


def test_get_balance_returns_the_exact_persisted_decimal(app: Flask) -> None:
    """HU-05 CA-1, CA-2; RNF-04.3: no calcula ni redondea el saldo."""
    repo = FakeWalletRepository({1: Decimal("123456.70")})

    balance = service.get_balance(1, repo=repo)

    assert balance == Decimal("123456.70")
    assert isinstance(balance, Decimal)


def test_get_balance_is_a_pure_read_without_locks_or_writes(app: Flask) -> None:
    """FR-008, RNF-04: la consulta no bloquea la billetera ni registra movimientos."""
    repo = FakeWalletRepository({1: Decimal("5000.00")})

    service.get_balance(1, repo=repo)

    assert repo.locked == []
    assert repo.transactions == []
    assert repo.keys == []


def test_get_balance_returns_only_the_requested_users_wallet(app: Flask) -> None:
    """HU-05 CA-1, CA-4: con varias billeteras devuelve la del usuario indicado."""
    repo = FakeWalletRepository({1: Decimal("10.00"), 2: Decimal("999999.99")})

    assert service.get_balance(1, repo=repo) == Decimal("10.00")
    assert service.get_balance(2, repo=repo) == Decimal("999999.99")


def test_get_balance_without_wallet_raises_not_found_and_logs_warning(
    app: Flask, caplog: pytest.LogCaptureFixture
) -> None:
    """HU-05 CA-5, FR-005: saldo no disponible, error técnico registrado, nada creado."""
    repo = FakeWalletRepository({2: Decimal("0.00")})

    with (
        caplog.at_level(logging.WARNING, logger="app.wallet"),
        pytest.raises(WalletNotFoundError) as excinfo,
    ):
        service.get_balance(1, repo=repo)

    assert excinfo.value.code == "wallet_not_found"
    assert excinfo.value.status == 404
    assert list(repo.wallets) == [2]  # no se crea la billetera a escondidas
    missing = [r for r in caplog.records if r.getMessage() == "wallet.missing"]
    assert len(missing) == 1
    assert missing[0].levelno == logging.WARNING
    assert getattr(missing[0], "user_id", None) == 1
