"""Fixtures base compartidas por `app/**/tests` y `tests/` (ver testing.md).

Un conftest.py en la raíz de `api/` es necesario para que las fixtures de integración
(MySQL real) sean visibles tanto desde `tests/` como desde `app/modules/*/tests/`.

Dos formas de MySQL real:
- `integration_app`/`integration_client`/`db_session`: contenedor efímero por sesión
  (testcontainers), sin configuración previa.
- marker `mysql` + `db_tables` + `logged_in_client`: usa `DATABASE_URL` si apunta a MySQL
  (el servicio de CI o `docker compose up -d mysql` en local); si no, se omiten.
"""

from __future__ import annotations

import os
from collections.abc import Generator, Iterator

import pytest
from flask import Flask, g
from flask.testing import FlaskClient
from flask_migrate import upgrade
from sqlalchemy.orm import Session as SqlAlchemySession
from testcontainers.mysql import MySqlContainer

from app import create_app
from app.extensions import db
from app.modules.accounts.models import User
from app.modules.auth.models import Session
from app.modules.wallet.models import Wallet
from tests.factories import SeededUser, make_user

os.environ.setdefault("SECRET_KEY", "clave-de-pruebas-no-secreta")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

USES_MYSQL = os.environ["DATABASE_URL"].startswith("mysql")
MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "migrations")


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "mysql: requiere DATABASE_URL apuntando a MySQL (mysql+pymysql://...)"
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if USES_MYSQL:
        return
    skip = pytest.mark.skip(reason="DATABASE_URL no apunta a MySQL; ver quickstart.md")
    for item in items:
        if "mysql" in item.keywords:
            item.add_marker(skip)


@pytest.fixture
def app() -> Iterator[Flask]:
    application = create_app("testing")
    with application.app_context():
        yield application
        db.session.remove()


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()


@pytest.fixture
def logged_in_client(app: Flask) -> FlaskClient:
    """Simula la capa de sesión: fija g.user_id = 1 en cada petición (sin cookie ni BD)."""

    @app.before_request
    def fake_session() -> None:
        g.user_id = 1

    return app.test_client()


# --- MySQL por DATABASE_URL (marker `mysql`) -------------------------------------------


@pytest.fixture(scope="session")
def migrated_database() -> Iterator[None]:
    """Aplica las migraciones Alembic una vez por sesión cuando hay MySQL (nunca create_all)."""
    if not USES_MYSQL:
        yield
        return
    application = create_app("testing")
    with application.app_context():
        upgrade(directory=MIGRATIONS_DIR)
    yield


def _truncate_all() -> None:
    from sqlalchemy import text

    db.session.remove()  # libera bloqueos pendientes antes de truncar
    with db.engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        for table in ("idempotency_keys", "transactions", "wallets", "sessions", "users"):
            conn.execute(text(f"TRUNCATE TABLE {table}"))  # noqa: S608 (nombres fijos)
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))


@pytest.fixture
def db_tables(app: Flask, migrated_database: None) -> Iterator[None]:
    """Tablas limpias para pruebas con MySQL, antes y después de cada test."""
    if USES_MYSQL:
        _truncate_all()
    yield
    if USES_MYSQL:
        _truncate_all()


@pytest.fixture
def seeded_users(db_tables: None) -> list[SeededUser]:
    """Dos usuarios persistidos (ids 1 y 2 tras el TRUNCATE) para las pruebas con MySQL."""
    users = [make_user(password="Clave1234"), make_user(password="Clave1234")]
    for seeded in users:
        db.session.add(seeded.user)
    db.session.commit()
    ids = [u.user.id for u in users]
    db.session.expire_all()
    assert ids == [1, 2], ids  # noqa: S101 (invariante de las fixtures)
    return users


# --- MySQL efímero por testcontainers ---------------------------------------------------


@pytest.fixture(scope="session")
def mysql_database_url() -> Generator[str, None, None]:
    """MySQL real en contenedor para pruebas de integración (testing.md: nunca create_all())."""
    with MySqlContainer("mysql:8.0") as mysql:
        url = (
            mysql.get_connection_url()
            .replace("mysql+mysqldb://", "mysql+pymysql://")
            .replace("mysql://", "mysql+pymysql://")
        )
        os.environ["DATABASE_URL"] = url
        application = create_app("testing")
        with application.app_context():
            upgrade(directory=MIGRATIONS_DIR)
        yield url


@pytest.fixture
def integration_app(mysql_database_url: str) -> Iterator[Flask]:
    os.environ["DATABASE_URL"] = mysql_database_url
    application = create_app("testing")
    with application.app_context():
        yield application


@pytest.fixture
def integration_client(integration_app: Flask) -> FlaskClient:
    return integration_app.test_client()


@pytest.fixture
def db_session(integration_app: Flask) -> Generator[SqlAlchemySession, None, None]:
    """Sesión de BD contra el MySQL de pruebas; limpia sus propias filas al terminar.

    Capturar en variables locales los atributos de un objeto recién creado antes de
    `commit()`: después del commit los objetos quedan expirados.
    """
    yield db.session

    db.session.rollback()
    db.session.query(Session).delete()
    db.session.query(Wallet).delete()
    db.session.query(User).delete()
    db.session.commit()
