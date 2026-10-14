"""Password helpers shared by registration and login."""

from app.common.passwords import hash_password, verify_password


def test_hash_can_be_verified_without_containing_the_password() -> None:
    raw_password = "clave123"  # noqa: S105 - isolated test fixture
    password_hash = hash_password(raw_password)

    assert password_hash.startswith("$argon2id$")
    assert raw_password not in password_hash
    assert verify_password(raw_password, password_hash)


def test_wrong_password_is_rejected() -> None:
    assert not verify_password("incorrecta9", hash_password("correcta8"))
