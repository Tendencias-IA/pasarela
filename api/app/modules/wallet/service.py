"""Public wallet service API."""

from app.modules.wallet import repository
from app.modules.wallet.models import Wallet


def create_wallet_for_account(user_id: int, session: repository.SessionLike) -> Wallet:
    return repository.create_for_user(user_id, session)
