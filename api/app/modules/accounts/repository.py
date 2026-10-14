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
