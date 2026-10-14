"""Extensiones compartidas; se inicializan en create_app."""

from collections.abc import Iterator
from contextlib import contextmanager

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base declarativa tipada; los modelos pueden heredar de aquí o de `db.Model`."""


db = SQLAlchemy(model_class=Base)
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address)


@contextmanager
def transaction() -> Iterator[None]:
    """Delimita la unidad de trabajo de un servicio: commit al salir, rollback si falla.

    Flask-SQLAlchemy abre la transacción en la primera consulta (autobegin), así que
    `db.session.begin()` fallaría si una lectura previa en la misma petición ya la abrió;
    este helper funciona en ambos casos. Solo los servicios lo usan.
    """
    try:
        yield
        db.session.commit()
    except BaseException:
        db.session.rollback()
        raise
