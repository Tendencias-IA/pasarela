"""HU-01 registration orchestration."""

import logging
from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError

from app.common.errors import DuplicateIdentityError
from app.common.passwords import hash_password
from app.extensions import db
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
