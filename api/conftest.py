"""Fixtures base compartidas por `app/**/tests` y `tests/` (ver testing.md).

Un conftest.py en la raíz de `api/` es necesario para que las fixtures de integración
(MySQL real) sean visibles tanto desde `tests/` como desde `app/modules/*/tests/`.
"""

from __future__ import annotations

import os
from collections.abc import Generator, Iterator

import pytest
from flask import Flask
from flask.testing import FlaskClient
from flask_migrate import upgrade
from sqlalchemy.orm import Session as SqlAlchemySession
from testcontainers.mysql import MySqlContainer

from app import create_app
from app.extensions import db
from app.modules.accounts.models import User
from app.modules.auth.models import Session
from app.modules.wallet.models import Wallet

os.environ.setdefault("SECRET_KEY", "clave-de-pruebas-no-secreta")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")


@pytest.fixture
def app() -> Iterator[Flask]:
    application = create_app("testing")
    with application.app_context():
        yield application


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()


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
            upgrade(directory=os.path.join(os.path.dirname(__file__), "migrations"))
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

    Las pruebas deben capturar en una variable local los atributos de un objeto
    recién creado (p. ej. `phone = user.phone`) ANTES de llamar a `commit()`: después
    del commit los objetos quedan expirados y leerlos dispara una recarga que abre una
    transacción nueva, que choca con el `with db.session.begin():` de la propia
    petición HTTP simulada (la app de pruebas reutiliza el mismo contexto de
    aplicación, a diferencia de producción).
    """
    yield db.session

    db.session.rollback()
    db.session.query(Session).delete()
    db.session.query(Wallet).delete()
    db.session.query(User).delete()
    db.session.commit()
