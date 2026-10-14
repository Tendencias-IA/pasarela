"""Flujo completo del historial por HTTP contra MySQL (HU-09)."""

from __future__ import annotations

import re
from typing import Any

import pytest
from flask.testing import FlaskClient

from app.modules.wallet import service as wallet_service
from tests.factories import SeededUser

URL = "/api/v1/movements"
pytestmark = pytest.mark.mysql


def _recharge(client: FlaskClient, amount: str, key_suffix: str) -> Any:
    return client.post(
        "/api/v1/wallet/recharges",
        json={"amount": amount},
        headers={
            "X-Requested-With": "fetch",
            "Idempotency-Key": f"00000000-0000-4000-8000-0000000000{key_suffix}",
        },
    )


def test_history_lists_recharges_newest_first(
    logged_in_client: FlaskClient, seeded_users: list[SeededUser]
) -> None:
    """HU-09 CA-1, CA-2, CA-4; SC-007."""
    wallet_service.create_wallet(1)
    assert _recharge(logged_in_client, "50000.00", "a1").status_code == 201
    assert _recharge(logged_in_client, "20000.00", "a2").status_code == 201
    assert _recharge(logged_in_client, "4999.00", "a3").status_code == 422

    response = logged_in_client.get(URL)

    assert response.status_code == 200
    body = response.get_json()
    assert body["total"] == 3 and body["page"] == 1 and body["page_size"] == 20
    newest, middle, oldest = body["items"]
    assert newest["status"] == "rechazada"
    assert newest["rejection_reason"] == "amount_out_of_range"
    assert newest["amount"] == "4999.00"
    assert middle["amount"] == "20000.00" and oldest["amount"] == "50000.00"
    assert all(item["direction"] == "recarga" for item in body["items"])
    assert all(item["counterparty"] is None for item in body["items"])
    assert all(re.fullmatch(r"\d+\.\d{2}", item["amount"]) for item in body["items"])
    assert all(item["created_at"].endswith("Z") for item in body["items"])


def test_real_login_cookie_lists_movements(
    client: FlaskClient, seeded_users: list[SeededUser]
) -> None:
    """HU-02 CA-5 + HU-09: la cookie de sesión real autoriza la consulta."""
    wallet_service.create_wallet(1)
    login = client.post(
        "/api/v1/auth/login",
        json={"phone": seeded_users[0].phone, "password": seeded_users[0].password},
        headers={"X-Requested-With": "fetch"},
    )
    assert login.status_code == 204

    response = client.get(URL)

    assert response.status_code == 200
    assert response.get_json() == {"items": [], "page": 1, "page_size": 20, "total": 0}


def test_without_session_is_rejected(client: FlaskClient, seeded_users: list[SeededUser]) -> None:
    """RNF-01.1, HU-02 CA-5."""
    response = client.get(URL)

    assert response.status_code == 401
    assert response.get_json()["code"] == "invalid_session"


def test_foreign_wallet_params_are_ignored(
    logged_in_client: FlaskClient, seeded_users: list[SeededUser]
) -> None:
    """HU-09 CA-5, RNF-01.4: la billetera sale de la sesión, nunca de la query."""
    wallet_service.create_wallet(1)
    wallet_service.create_wallet(2)
    _recharge(logged_in_client, "50000.00", "b1")

    response = logged_in_client.get(f"{URL}?user_id=2&wallet_id=2")

    assert response.status_code == 200
    assert response.get_json()["total"] == 1


@pytest.mark.parametrize("raw", ["0", "-1", "abc", "1.5"])
def test_invalid_page_is_422_on_field_page(
    logged_in_client: FlaskClient, seeded_users: list[SeededUser], raw: str
) -> None:
    """FR-009."""
    response = logged_in_client.get(f"{URL}?page={raw}")

    assert response.status_code == 422
    body = response.get_json()
    assert body["code"] == "validation"
    assert body["errors"][0]["field"] == "page"


def test_page_beyond_last_is_empty_with_real_total(
    logged_in_client: FlaskClient, seeded_users: list[SeededUser]
) -> None:
    """FR-009."""
    wallet_service.create_wallet(1)
    _recharge(logged_in_client, "50000.00", "c1")

    response = logged_in_client.get(f"{URL}?page=9")

    assert response.status_code == 200
    assert response.get_json() == {"items": [], "page": 9, "page_size": 20, "total": 1}


def _today() -> str:
    from app.common.clock import utcnow

    return utcnow().date().isoformat()


def test_type_filter_returns_only_recharges_and_empty_for_sent(
    logged_in_client: FlaskClient, seeded_users: list[SeededUser]
) -> None:
    """HU-10 CA-3, CA-7: filtrar recargas muestra filas; enviadas, vacío con filtros válidos."""
    wallet_service.create_wallet(1)
    _recharge(logged_in_client, "50000.00", "d1")
    _recharge(logged_in_client, "4999.00", "d2")

    recharges = logged_in_client.get(f"{URL}?type=recharge").get_json()
    sent = logged_in_client.get(f"{URL}?type=sent")

    assert recharges["total"] == 2
    assert all(i["direction"] == "recarga" for i in recharges["items"])
    assert sent.status_code == 200
    assert sent.get_json() == {"items": [], "page": 1, "page_size": 20, "total": 0}


def test_date_and_type_filters_combine_over_http(
    logged_in_client: FlaskClient, seeded_users: list[SeededUser]
) -> None:
    """HU-10 CA-1, CA-4: hoy + recargas devuelve la recarga; ayer, nada."""
    wallet_service.create_wallet(1)
    _recharge(logged_in_client, "50000.00", "e1")
    today = _today()

    hit = logged_in_client.get(f"{URL}?from={today}&to={today}&type=recharge").get_json()
    miss = logged_in_client.get(f"{URL}?to=2000-01-01&type=recharge").get_json()

    assert hit["total"] == 1
    assert miss["total"] == 0


def test_reversed_range_is_422_invalid_date_range(
    logged_in_client: FlaskClient, seeded_users: list[SeededUser]
) -> None:
    """HU-10 CA-2, RNF-01.4."""
    wallet_service.create_wallet(1)

    response = logged_in_client.get(f"{URL}?from=2026-12-31&to=2026-01-01")

    assert response.status_code == 422
    body = response.get_json()
    assert body["code"] == "invalid_date_range"
    assert body["detail"] == "La fecha inicial no puede ser posterior a la final."
    assert "2026" not in body["detail"]


@pytest.mark.parametrize(
    ("query", "fields"),
    [
        ("from=2026-02-31", ["from"]),
        ("to=ayer", ["to"]),
        ("type=foo", ["type"]),
        ("page=0&from=x&type=y", ["page", "from", "type"]),
    ],
)
def test_invalid_filter_values_are_422_validation(
    logged_in_client: FlaskClient, seeded_users: list[SeededUser], query: str, fields: list[str]
) -> None:
    """HU-10 CA-1, CA-3."""
    response = logged_in_client.get(f"{URL}?{query}")

    assert response.status_code == 422
    body = response.get_json()
    assert body["code"] == "validation"
    assert [e["field"] for e in body["errors"]] == fields


def test_filters_without_session_are_rejected(
    client: FlaskClient, seeded_users: list[SeededUser]
) -> None:
    """HU-10, RNF-01.1."""
    assert client.get(f"{URL}?type=recharge").status_code == 401
