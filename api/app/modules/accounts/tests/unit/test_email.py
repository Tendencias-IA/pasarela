"""HU-13: validación y rechazo seguro del correo."""

from unittest.mock import Mock, patch

import pytest
from pydantic import ValidationError

from app.common.errors import DuplicateIdentityError
from app.modules.accounts import service
from app.modules.accounts.schemas import UpdateEmailIn


@pytest.mark.parametrize("email", ["", "abc", "a@b", 123, None])
def test_invalid_email_is_rejected(email: object) -> None:
    """HU-13 CA-1."""
    with pytest.raises(ValidationError):
        UpdateEmailIn.model_validate({"email": email})


def test_email_is_normalized_and_extra_fields_rejected() -> None:
    """HU-13 CA-1, CA-4."""
    assert (
        UpdateEmailIn.model_validate({"email": " Nuevo@Example.test "}).email
        == "nuevo@example.test"
    )
    with pytest.raises(ValidationError):
        UpdateEmailIn.model_validate({"email": "nuevo@example.test", "phone": "3001110001"})


def test_duplicate_email_keeps_previous_value() -> None:
    """HU-13 CA-2, CA-6."""
    user = Mock(email="anterior@example.test")
    with patch.object(service, "repository") as repo, patch.object(service, "transaction"):
        repo.get_by_id.return_value = user
        repo.email_registered_elsewhere.return_value = True
        with pytest.raises(DuplicateIdentityError):
            service.update_email(1, "otra@example.test")
        repo.update_email.assert_not_called()
    assert user.email == "anterior@example.test"
