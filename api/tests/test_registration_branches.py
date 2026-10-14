"""Branch coverage for safe account registration failures."""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError

from app import create_app
from app.common.errors import AppError
from app.modules.accounts.schemas import RegisterAccountIn
from app.modules.accounts.service import register_account
from app.modules.wallet import repository as wallet_repository
from app.modules.wallet import service as wallet_service

VALID = {
    "full_name": "Persona Prueba",
    "phone": "3000000001",
    "national_id": "TEST001",
    "email": "person@example.test",
    "password": "clave123",
}


def test_route_rejects_missing_header_and_invalid_json() -> None:
    """HU-01 CA-3."""
    app = create_app("testing")
    with app.test_client() as client:
        missing = client.post("/api/v1/accounts", json=VALID)
        invalid = client.post(
            "/api/v1/accounts",
            data="{",
            content_type="application/json",
            headers={"X-Requested-With": "fetch"},
        )
    assert missing.status_code == 403
    assert invalid.status_code == 400


def test_route_returns_all_validation_errors() -> None:
    """HU-01 CA-3, CA-5."""
    app = create_app("testing")
    with app.test_client() as client:
        response = client.post(
            "/api/v1/accounts",
            json={key: "" for key in VALID},
            headers={"X-Requested-With": "fetch"},
        )
    assert response.status_code == 422
    assert {error["field"] for error in response.get_json()["errors"]} == set(VALID)


def test_service_rejects_preexisting_or_concurrent_duplicate() -> None:
    """HU-01 CA-4."""
    data = RegisterAccountIn.model_validate(VALID)
    with (
        patch("app.modules.accounts.service.repository") as repository,
        patch("app.modules.accounts.service.db") as db,
    ):
        repository.find_duplicate.return_value = True
        with pytest.raises(AppError) as duplicate:
            register_account(data)
        assert duplicate.value.code == "duplicate_identity"

        repository.find_duplicate.return_value = False
        repository.create.side_effect = IntegrityError("insert", {}, Exception())
        with pytest.raises(AppError) as concurrent:
            register_account(data)
        assert concurrent.value.code == "duplicate_identity"
        db.session.rollback.assert_called()


def test_wallet_service_delegates_exact_decimal_balance() -> None:
    """HU-01 CA-2."""
    session = MagicMock()
    with patch.object(wallet_repository, "create_for_user") as create:
        create.return_value.balance = Decimal("0.00")
        result = wallet_service.create_wallet_for_account(2, session)
    create.assert_called_once_with(2, session)
    assert result.balance == Decimal("0.00")
