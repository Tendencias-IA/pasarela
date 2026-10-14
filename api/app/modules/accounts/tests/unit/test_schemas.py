"""HU-01 input validation tests."""

import pytest
from pydantic import ValidationError

from app.modules.accounts.schemas import RegisterAccountIn

VALID = {
    "full_name": "Lía Test",
    "phone": "3000000001",
    "national_id": "TEST001",
    "email": "lia@example.test",
    "password": "clave123",
}


def test_register_schema_accepts_and_canonicalizes_valid_data() -> None:
    """HU-01 CA-1, CA-3, CA-5."""
    value = RegisterAccountIn.model_validate(
        {**VALID, "email": " LIA@EXAMPLE.TEST ", "national_id": " test001 "}
    )
    assert value.email == "lia@example.test"
    assert value.national_id == "TEST001"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("full_name", "1"),
        ("phone", "2000000000"),
        ("national_id", "A-1"),
        ("email", "bad"),
        ("password", "abcdefgh"),
    ],
)
def test_register_schema_rejects_each_invalid_field(field: str, value: str) -> None:
    """HU-01 CA-3, CA-5."""
    with pytest.raises(ValidationError):
        RegisterAccountIn.model_validate({**VALID, field: value})


def test_register_schema_reports_all_invalid_fields() -> None:
    """HU-01 CA-3 aggregates corrections."""
    with pytest.raises(ValidationError) as caught:
        RegisterAccountIn.model_validate(
            {"full_name": "", "phone": "", "national_id": "", "email": "", "password": ""}
        )
    assert {str(error["loc"][0]) for error in caught.value.errors()} == set(VALID)
