"""Crea un usuario de prueba para HU-02 mientras HU-01 (registro) no existe.

Uso: flask shell-less, se ejecuta directo con python dentro del contenedor/entorno de
la API: `python scripts/seed_test_user.py`.
"""

from __future__ import annotations

import sys

from app import create_app
from app.common.passwords import hash_password
from app.extensions import db
from app.modules.accounts.models import User
from app.modules.accounts.repository import get_by_phone

PHONE = "3009876543"
PASSWORD = "Clave1234"


def main() -> None:
    app = create_app()
    with app.app_context():
        if get_by_phone(PHONE) is not None:
            print(f"Ya existe un usuario con teléfono {PHONE}; no se crea de nuevo.")
            sys.exit(0)
        db.session.add(User(phone=PHONE, password_hash=hash_password(PASSWORD)))
        db.session.commit()
        print(f"Usuario creado: teléfono {PHONE}, contraseña {PASSWORD}")


if __name__ == "__main__":
    main()
