"""MySQL transaction and uniqueness tests for HU-01."""

from concurrent.futures import ThreadPoolExecutor

from flask import Flask
from sqlalchemy import func, select
from werkzeug.test import TestResponse

from app.extensions import db
from app.modules.accounts.models import User
from app.modules.wallet.models import Wallet


def _post(app: Flask, _: str) -> TestResponse:
    with app.test_client() as client:
        return client.post(
            "/api/v1/accounts",
            json={
                "full_name": "Persona Prueba",
                "phone": "3000099999",
                "national_id": "CONCURRENT1",
                "email": "concurrent@example.test",
                "password": "clave123",
            },
            headers={"X-Requested-With": "fetch"},
        )


def test_login_user_without_hu01_profile_survives_extended_schema(integration_app: Flask) -> None:
    """The HU-02 base user remains valid after the HU-01 migration."""
    with integration_app.app_context(), db.session.begin():
        user = User(
            phone="3000077777",
            password_hash="$argon2id$login-fixture",  # noqa: S106 - encoded test fixture
        )
        db.session.add(user)
        db.session.flush()

        assert user.full_name is None
        assert user.national_id is None
        assert user.email is None


def test_concurrent_duplicate_creates_one_account_and_wallet(integration_app: Flask) -> None:
    """HU-01 CA-1, CA-2, CA-4; SC-003."""
    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(lambda suffix: _post(integration_app, suffix), ("a", "b")))
    assert sorted(response.status_code for response in responses) == [201, 409]
    with integration_app.app_context():
        assert (
            db.session.scalar(
                select(func.count())
                .select_from(User)
                .where(User.email == "concurrent@example.test")
            )
            == 1
        )
        user_id = db.session.scalar(select(User.id).where(User.email == "concurrent@example.test"))
        assert (
            db.session.scalar(
                select(func.count()).select_from(Wallet).where(Wallet.user_id == user_id)
            )
            == 1
        )
