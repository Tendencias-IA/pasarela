"""MySQL wallet invariants for HU-01."""

from decimal import Decimal

import pytest
from flask import Flask
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.modules.accounts.models import User
from app.modules.wallet.models import Wallet


def test_wallet_is_one_to_one_decimal_and_nonnegative(integration_app: Flask) -> None:
    """HU-01 CA-2."""
    with integration_app.app_context():
        with db.session.begin():
            user = User(
                full_name="Persona Billetera",
                phone="3000088888",
                national_id="WALLET001",
                email="wallet@example.test",
                password_hash="$argon2id$fake",  # noqa: S106 - hash ficticio, no contraseña
            )
            db.session.add(user)
            db.session.flush()
            wallet = Wallet(user_id=user.id, balance=Decimal("0.00"))
            db.session.add(wallet)
            assert wallet.balance == Decimal("0.00")
        with pytest.raises(IntegrityError), db.session.begin():
            db.session.add(Wallet(user_id=user.id, balance=Decimal("0.00")))
        db.session.rollback()
