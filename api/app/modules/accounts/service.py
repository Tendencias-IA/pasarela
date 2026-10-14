"""HU-01 registration orchestration."""

import logging
from dataclasses import dataclass
from typing import Literal

from sqlalchemy.exc import IntegrityError

from app.common.errors import AppError, DuplicateIdentityError
from app.common.passwords import hash_password
from app.extensions import db, transaction
from app.modules.accounts import repository
from app.modules.accounts.models import User
from app.modules.accounts.schemas import RegisterAccountIn
from app.modules.wallet import service as wallet_service

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class RegisteredAccount:
    account_id: int
    balance: str


def register_account(data: RegisterAccountIn) -> RegisteredAccount:
    password_hash = hash_password(data.password)
    try:
        with db.session.begin():
            if repository.find_duplicate(data):
                raise DuplicateIdentityError()
            user = repository.create(data, password_hash)
            wallet = wallet_service.create_wallet_for_account(user.id, db.session)
        log.info("account.registered", extra={"business_module": "accounts", "user_id": user.id})
        return RegisteredAccount(account_id=user.id, balance=f"{wallet.balance:.2f}")
    except IntegrityError as error:
        db.session.rollback()
        raise DuplicateIdentityError() from error


def get_user_by_phone(phone: str) -> User | None:
    """Stable accounts API consumed by the login module."""
    return repository.get_by_phone(phone)


class ProfileNotFoundError(AppError):
    status = 404
    code = "profile_not_found"
    title = "Perfil no encontrado"


@dataclass(frozen=True)
class AccountProfile:
    full_name: str | None
    phone: str
    national_id: str | None
    email: str | None


def _profile(user: User) -> AccountProfile:
    return AccountProfile(user.full_name, user.phone, user.national_id, user.email)


def get_profile(user_id: int) -> AccountProfile:
    user = repository.get_by_id(user_id)
    if user is None:
        raise ProfileNotFoundError()
    return _profile(user)


def update_phone(user_id: int, phone: str) -> AccountProfile:
    """HU-12 CA-2 a CA-8: conservar cuenta, saldo e historial."""
    return _update_contact(user_id, phone, "phone")


def update_email(user_id: int, email: str) -> AccountProfile:
    """HU-13 CA-2 a CA-6: conservar teléfono y datos financieros."""
    return _update_contact(user_id, email, "email")


def _update_contact(user_id: int, value: str, field: Literal["phone", "email"]) -> AccountProfile:
    try:
        with transaction():
            user = repository.get_by_id(user_id, lock=True)
            if user is None:
                raise ProfileNotFoundError()
            duplicate = (
                repository.phone_registered_elsewhere(user_id, value)
                if field == "phone"
                else repository.email_registered_elsewhere(user_id, value)
            )
            if duplicate:
                raise DuplicateIdentityError()
            if field == "phone":
                repository.update_phone(user, value)
            else:
                repository.update_email(user, value)
            result = _profile(user)
    except IntegrityError as error:
        raise DuplicateIdentityError() from error
    log.info("account.contact_updated", extra={"user_id": user_id, "field": field})
    return result
