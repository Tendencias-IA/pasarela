"""HU-01 account service tests."""

from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from app.common.errors import AppError
from app.modules.accounts.models import User
from app.modules.accounts.schemas import RegisterAccountIn
from app.modules.accounts.service import get_user_by_phone, register_account

VALID = {
    "full_name": "Lía Test",
    "phone": "3000000001",
    "national_id": "TEST001",
    "email": "lia@example.test",
    "password": "clave123",
}


def test_register_account_hashes_password_and_creates_one_wallet() -> None:
    """HU-01 CA-1, CA-2, CA-6."""
    data = RegisterAccountIn.model_validate(VALID)
    user = Mock(id=12)
    wallet = Mock(balance=Decimal("0.00"))
    with (
        patch("app.modules.accounts.service.repository") as repository,
        patch("app.modules.accounts.service.wallet_service") as wallets,
        patch("app.modules.accounts.service.db") as db,
    ):
        repository.find_duplicate.return_value = False
        repository.create.return_value = user
        wallets.create_wallet_for_account.return_value = wallet
        result = register_account(data)
    saved_hash = repository.create.call_args.args[1]
    assert saved_hash.startswith("$argon2id$")
    assert VALID["password"] not in saved_hash
    wallets.create_wallet_for_account.assert_called_once_with(user.id, db.session)
    assert result.account_id == 12


def test_register_account_rejects_duplicate_without_creating_wallet() -> None:
    """HU-01 CA-4."""
    data = RegisterAccountIn.model_validate(VALID)
    with (
        patch("app.modules.accounts.service.repository") as repository,
        patch("app.modules.accounts.service.wallet_service") as wallets,
        patch("app.modules.accounts.service.db"),
    ):
        repository.find_duplicate.return_value = True
        with pytest.raises(AppError) as caught:
            register_account(data)
    assert caught.value.code == "duplicate_identity"
    wallets.create_wallet_for_account.assert_not_called()


def test_register_account_does_not_log_personal_or_secret_values(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """HU-01 CA-6, RNF-06."""
    data = RegisterAccountIn.model_validate(VALID)
    user = Mock(id=13)
    wallet = Mock(balance=Decimal("0.00"))
    with (
        patch("app.modules.accounts.service.repository") as repository,
        patch("app.modules.accounts.service.wallet_service") as wallets,
        patch("app.modules.accounts.service.db"),
    ):
        repository.find_duplicate.return_value = False
        repository.create.return_value = user
        wallets.create_wallet_for_account.return_value = wallet
        register_account(data)
    output = caplog.text
    assert VALID["password"] not in output
    assert VALID["national_id"] not in output
    assert VALID["phone"] not in output


def test_get_user_by_phone_exposes_the_lookup_needed_by_login() -> None:
    user = User(
        id=7,
        phone=VALID["phone"],
        password_hash="hash",  # noqa: S106 - isolated model fixture
    )
    with patch("app.modules.accounts.service.repository.get_by_phone", return_value=user):
        result = get_user_by_phone(VALID["phone"])
    assert result is user
