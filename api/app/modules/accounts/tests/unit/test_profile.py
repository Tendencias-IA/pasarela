"""HU-12: formato, sesión y rechazo sin modificar la cuenta."""

from unittest.mock import Mock, patch

import pytest
from flask.testing import FlaskClient
from pydantic import ValidationError

from app.common.errors import DuplicateIdentityError
from app.modules.accounts import service
from app.modules.accounts.schemas import UpdatePhoneIn


@pytest.mark.parametrize("phone", ["", "123", "2001234567", 3001234567])
def test_invalid_phone_is_rejected(phone: object) -> None:
    """HU-12 CA-1."""
    with pytest.raises(ValidationError):
        UpdatePhoneIn.model_validate({"phone": phone})


def test_extra_fields_are_rejected() -> None:
    """HU-12 CA-6; RNF-01.4."""
    with pytest.raises(ValidationError):
        UpdatePhoneIn.model_validate({"phone": "3001234567", "user_id": 2})


def test_profile_requires_session(client: FlaskClient) -> None:
    """HU-12: únicamente el titular autenticado."""
    assert client.get("/api/v1/profile").status_code == 401
    assert (
        client.patch(
            "/api/v1/profile",
            json={"phone": "3001234567"},
            headers={"X-Requested-With": "fetch"},
        ).status_code
        == 401
    )


def test_duplicate_keeps_old_phone() -> None:
    """HU-12 CA-2, CA-8."""
    user = Mock(phone="3001234567")
    with patch.object(service, "repository") as repo, patch.object(service, "transaction"):
        repo.get_by_id.return_value = user
        repo.phone_registered_elsewhere.return_value = True
        with pytest.raises(DuplicateIdentityError):
            service.update_phone(1, "3007654321")
        repo.update_phone.assert_not_called()
    assert user.phone == "3001234567"


def test_profile_patch_rejects_invalid_input(logged_in_client: FlaskClient) -> None:
    """HU-12 CA-1, CA-6."""
    response = logged_in_client.patch(
        "/api/v1/profile",
        json={"phone": "abc"},
        headers={"X-Requested-With": "fetch"},
    )
    assert response.status_code == 422
    assert response.get_json()["errors"][0]["field"] == "phone"
