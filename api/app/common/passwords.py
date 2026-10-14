"""Hash de contraseñas con Argon2id. Nunca hashlib ni texto plano (RNF-01.2)."""

from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError

_hasher = PasswordHasher()


def hash_password(raw_password: str) -> str:
    return _hasher.hash(raw_password)


def verify_password(raw_password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, raw_password)
    except VerificationError:
        return False
