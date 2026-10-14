"""Crea un usuario de prueba (HU-02) con su billetera (HU-08) mientras HU-01 no existe.

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
from app.modules.wallet import service as wallet_service

PHONE = "3008013627"
PASSWORD = "MainKilljoy123456"


def main() -> None:
    app = create_app()
    with app.app_context():
        user = get_by_phone(PHONE)
        if user is None:
            user = User(phone=PHONE, password_hash=hash_password(PASSWORD))
            db.session.add(user)
            db.session.commit()
            print(f"Usuario creado: teléfono {PHONE}, contraseña {PASSWORD}")
        else:
            print(f"Ya existe un usuario con teléfono {PHONE}; no se crea de nuevo.")
        if wallet_service.get_wallet_id(user.id) is None:
            wallet_service.create_wallet(user.id)
            print("Billetera creada con saldo 0.00")
        sys.exit(0)


if __name__ == "__main__":
    main()
