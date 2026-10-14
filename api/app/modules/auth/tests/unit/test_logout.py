"""HU-03 CA-1/CA-2: invalidación ausente o concurrente no concede acceso."""

from types import SimpleNamespace

import pytest
from pytest_mock import MockerFixture

from app.modules.auth import repository, service


@pytest.mark.parametrize("session", [None, SimpleNamespace(id=1, user_id=2)])
def test_logout_invalid_or_already_revoked_rejects(
    mocker: MockerFixture, session: SimpleNamespace | None
) -> None:
    mocker.patch.object(service, "transaction")
    mocker.patch.object(service, "get_current_session", return_value=session)
    mocker.patch.object(repository, "revoke_session", return_value=False)

    with pytest.raises(service.InvalidSessionError):
        service.logout("token-ficticio")
