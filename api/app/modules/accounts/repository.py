"""SQLAlchemy operations for the accounts module only."""

from sqlalchemy import or_, select

from app.extensions import db
from app.modules.accounts.models import User
from app.modules.accounts.schemas import RegisterAccountIn


def find_duplicate(data: RegisterAccountIn) -> bool:
    statement = (
        select(User.id)
        .where(
            or_(
                User.phone == data.phone,
                User.email == data.email,
                User.national_id == data.national_id,
            )
        )
        .limit(1)
    )
    return db.session.execute(statement).scalar_one_or_none() is not None


def get_by_phone(phone: str) -> User | None:
    """Public accounts lookup used by authentication without crossing module layers."""
    return db.session.execute(select(User).where(User.phone == phone)).scalar_one_or_none()


def create(data: RegisterAccountIn, password_hash: str) -> User:
    user = User(
        full_name=data.full_name,
        phone=data.phone,
        national_id=data.national_id,
        email=data.email,
        password_hash=password_hash,
    )
    db.session.add(user)
    db.session.flush()
    return user


def get_by_id(user_id: int, *, lock: bool = False) -> User | None:
    statement = select(User).where(User.id == user_id)
    if lock:
        statement = statement.with_for_update()
    return db.session.execute(statement).scalar_one_or_none()


def phone_registered_elsewhere(user_id: int, phone: str) -> bool:
    statement = select(User.id).where(User.phone == phone, User.id != user_id).limit(1)
    return db.session.execute(statement).scalar_one_or_none() is not None


def update_phone(user: User, phone: str) -> None:
    """HU-12 CA-6: modificar solo el teléfono y su timestamp automático."""
    user.phone = phone
    db.session.flush()


def email_registered_elsewhere(user_id: int, email: str) -> bool:
    statement = select(User.id).where(User.email == email, User.id != user_id).limit(1)
    return db.session.execute(statement).scalar_one_or_none() is not None


def update_email(user: User, email: str) -> None:
    """HU-13 CA-4: modificar exclusivamente correo y timestamp."""
    user.email = email
    db.session.flush()
