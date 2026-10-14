"""SQLAlchemy operations for wallets only."""

from decimal import Decimal
from typing import Protocol

from app.modules.wallet.models import Wallet


class SessionLike(Protocol):
    def add(self, instance: object) -> None: ...

    def flush(self) -> None: ...


def create_for_user(user_id: int, session: SessionLike) -> Wallet:
    wallet = Wallet(user_id=user_id, balance=Decimal("0.00"))
    session.add(wallet)
    session.flush()
    return wallet
