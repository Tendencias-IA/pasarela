"""HU-01 HTTP registration behavior."""

from unittest.mock import patch

from app import create_app
from app.modules.accounts.schemas import RegisterAccountOut


def test_post_account_returns_201_without_session_cookie() -> None:
    """HU-01 CA-1, CA-2, CA-6."""
    app = create_app("testing")
    result = RegisterAccountOut(account_id=7, balance="0.00")
    with (
        app.test_client() as client,
        patch("app.modules.accounts.routes.register_account", return_value=result),
    ):
        response = client.post(
            "/api/v1/accounts",
            json={
                "full_name": "Lía Test",
                "phone": "3000000001",
                "national_id": "TEST001",
                "email": "lia@example.test",
                "password": "clave123",
            },
            headers={"X-Requested-With": "fetch"},
        )
    assert response.status_code == 201
    assert response.get_json() == {"account_id": 7, "wallet": {"balance": "0.00"}}
    assert "Set-Cookie" not in response.headers
