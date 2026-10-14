"""HU-03 CA-1..4: revocación real en MySQL y reutilización del token."""

from decimal import Decimal

from flask import g
from flask.testing import FlaskClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session as SqlAlchemySession

from app.common.models.transaction import Transaction
from app.extensions import db
from app.modules.accounts import service as accounts_service
from app.modules.accounts.models import User
from app.modules.accounts.schemas import RegisterAccountIn
from app.modules.auth.models import Session
from app.modules.wallet.models import Wallet

HEADERS = {"X-Requested-With": "fetch"}


def test_logout_revokes_only_current_session_and_preserves_account(
    integration_client: FlaskClient, db_session: SqlAlchemySession
) -> None:
    """HU-03 CA-1/CA-2/CA-3/CA-4."""
    account = accounts_service.register_account(
        RegisterAccountIn(
            full_name="Persona Logout",
            phone="3007770001",
            national_id="LOGOUT001",
            email="logout@example.test",
            password="Clave1234",
        )
    )
    wallet = db_session.execute(
        select(Wallet).where(Wallet.user_id == account.account_id)
    ).scalar_one()
    wallet.balance = Decimal("12345.00")
    db_session.commit()
    before = db_session.get(User, account.account_id)
    assert before is not None
    snapshot = (
        before.full_name,
        before.phone,
        before.national_id,
        before.email,
        before.password_hash,
    )
    db.session.remove()
    for _ in range(2):
        response = integration_client.post(
            "/api/v1/auth/login",
            json={"phone": "3007770001", "password": "Clave1234"},
            headers=HEADERS,
        )
        assert response.status_code == 204
        db.session.remove()
    cookie = integration_client.get_cookie("session")
    assert cookie is not None
    token = cookie.value
    status = integration_client.get("/api/v1/auth/session")
    assert status.status_code == 200
    assert "expires_at" in status.get_json()
    db.session.remove()

    response = integration_client.post("/api/v1/auth/logout", headers=HEADERS)

    assert response.status_code == 204
    assert response.data == b""
    assert "Max-Age=0" in response.headers["Set-Cookie"]
    assert response.headers["Cache-Control"] == "no-store"
    assert integration_client.get_cookie("session") is None
    db.session.remove()
    # La fixture conserva app_context entre peticiones; en HTTP real g se recrea.
    g.pop("user_id", None)
    integration_client.set_cookie("session", token)
    for path in ("/api/v1/auth/session", "/api/v1/wallet/recharges"):
        response = (
            integration_client.get(path)
            if path.endswith("session")
            else integration_client.post(
                path,
                json={"amount": "5000.00"},
                headers={
                    **HEADERS,
                    "Idempotency-Key": "00000000-0000-4000-8000-000000000003",
                },
            )
        )
        assert response.status_code == 401
        assert response.get_json()["code"] == "invalid_session"
        db.session.remove()
    sessions = (
        db_session.execute(select(Session).where(Session.user_id == account.account_id))
        .scalars()
        .all()
    )
    assert sum(s.revoked_at is not None for s in sessions) == 1
    after = db_session.get(User, account.account_id)
    assert after is not None
    assert (
        after.full_name,
        after.phone,
        after.national_id,
        after.email,
        after.password_hash,
    ) == snapshot
    wallet = db_session.execute(
        select(Wallet).where(Wallet.user_id == account.account_id)
    ).scalar_one()
    assert wallet.balance == Decimal("12345.00")
    assert (
        db_session.execute(
            select(func.count())
            .select_from(Transaction)
            .where(Transaction.receiver_wallet_id == wallet.id)
        ).scalar_one()
        == 0
    )


def test_logout_without_session_rejects_and_requires_csrf(integration_client: FlaskClient) -> None:
    """HU-03 CA-2; RNF-01: sin sesión no hay cierre válido ni acceso."""
    response = integration_client.post("/api/v1/auth/logout", headers=HEADERS)
    assert response.status_code == 401
    assert response.get_json()["code"] == "invalid_session"
    assert integration_client.post("/api/v1/auth/logout").status_code == 403
