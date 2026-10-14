"""Preparar una transferencia con dobles de wallet y accounts (HU-06)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.modules.transfers import service
from app.modules.transfers.service import RecipientNotFoundError, SelfTransferError
from app.modules.transfers.tests.unit.fakes import FakeAccounts, FakeWallet
from app.modules.wallet.service import (
    AmountOutOfRangeError,
    InsufficientBalanceError,
    WalletNotFoundError,
)

SENDER, RECIPIENT = 1, 2
PHONE = "3001234567"


@pytest.fixture
def wallet() -> FakeWallet:
    return FakeWallet({SENDER: Decimal("500000.00"), RECIPIENT: Decimal("0.00")})


@pytest.fixture
def accounts() -> FakeAccounts:
    return FakeAccounts({PHONE: (RECIPIENT, None), "3000000001": (SENDER, None)})


def _preview(wallet: FakeWallet, accounts: FakeAccounts, amount: str, phone: str = PHONE):  # type: ignore[no-untyped-def]
    return service.preview_transfer(
        SENDER, phone, Decimal(amount), wallet=wallet, accounts=accounts
    )


def test_preview_valid_data_returns_masked_recipient_and_balance_after(
    wallet: FakeWallet, accounts: FakeAccounts
) -> None:
    """HU-06 CA-1, CA-7."""
    result = _preview(wallet, accounts, "150000.00")

    assert result.amount == Decimal("150000.00")
    assert result.recipient.phone_masked == "***4567"
    assert result.recipient.name_masked is None
    assert result.balance_after == Decimal("350000.00")
    assert result.to_body() == {
        "amount": "150000.00",
        "recipient": {"name_masked": None, "phone_masked": "***4567"},
        "balance_after": "350000.00",
    }


@pytest.mark.parametrize("amount", ["100.00", "3000000.00"])
def test_preview_limit_amounts_are_accepted(
    wallet: FakeWallet, accounts: FakeAccounts, amount: str
) -> None:
    """HU-06 CA-2."""
    wallet.balances[SENDER] = Decimal("3000000.00")

    assert _preview(wallet, accounts, amount).amount == Decimal(amount)


def test_preview_masks_recipient_name_to_initials(wallet: FakeWallet) -> None:
    """HU-06 CA-7, RNF-06.1."""
    accounts = FakeAccounts({PHONE: (RECIPIENT, "Maria Garcia")})

    result = _preview(wallet, accounts, "1000.00")

    assert result.recipient.name_masked == "Mar** G*****"
    assert "Garcia" not in str(result.to_body())


def test_preview_balance_equal_to_amount_leaves_zero(
    wallet: FakeWallet, accounts: FakeAccounts
) -> None:
    wallet.balances[SENDER] = Decimal("100.00")

    assert _preview(wallet, accounts, "100.00").balance_after == Decimal("0.00")


@pytest.mark.parametrize("amount", ["99.99", "3000000.01"])
def test_preview_out_of_range_is_rejected_before_any_lookup(
    wallet: FakeWallet, accounts: FakeAccounts, amount: str
) -> None:
    """HU-06 CA-2, CA-3."""
    with pytest.raises(AmountOutOfRangeError) as excinfo:
        _preview(wallet, accounts, amount)

    assert excinfo.value.errors[0]["message"] == "Debe estar entre 100.00 y 3000000.00"
    assert accounts.lookups == [] and wallet.calls == []


def test_preview_unknown_phone_is_recipient_not_found(
    wallet: FakeWallet, accounts: FakeAccounts
) -> None:
    """HU-06 CA-4."""
    with pytest.raises(RecipientNotFoundError) as excinfo:
        _preview(wallet, accounts, "1000.00", phone="3999999999")

    assert (excinfo.value.status, excinfo.value.code) == (404, "recipient_not_found")


def test_preview_recipient_without_wallet_is_recipient_not_found(accounts: FakeAccounts) -> None:
    """Research §4: no se filtra el estado parcial de otra cuenta."""
    wallet = FakeWallet({SENDER: Decimal("500000.00")})

    with pytest.raises(RecipientNotFoundError):
        _preview(wallet, accounts, "1000.00")


def test_preview_own_phone_is_self_transfer(wallet: FakeWallet, accounts: FakeAccounts) -> None:
    """HU-06 CA-5."""
    with pytest.raises(SelfTransferError) as excinfo:
        _preview(wallet, accounts, "1000.00", phone="3000000001")

    assert (excinfo.value.status, excinfo.value.code) == (422, "self_transfer")


def test_preview_insufficient_balance_is_rejected_without_leaking_numbers(
    wallet: FakeWallet, accounts: FakeAccounts
) -> None:
    """HU-06 CA-6."""
    with pytest.raises(InsufficientBalanceError) as excinfo:
        _preview(wallet, accounts, "500000.01")

    assert "500000" not in excinfo.value.detail


def test_preview_sender_without_wallet_raises_wallet_not_found(accounts: FakeAccounts) -> None:
    wallet = FakeWallet({RECIPIENT: Decimal("0.00")})

    with pytest.raises(WalletNotFoundError):
        _preview(wallet, accounts, "1000.00")
