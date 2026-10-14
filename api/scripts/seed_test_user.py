"""Crea los usuarios de prueba de E2E con su billetera mientras HU-01 no existe.

- 3009876543: acumula recargas entre corridas (HU-08, HU-09 con historial).
- 3009876544: nunca opera; sirve para el estado vacío del historial (HU-09 CA-7) y para
  probar saldo insuficiente al preparar una transferencia (HU-06 CA-6).
- 3009876545: recibe las transferencias reales de los specs de HU-07.

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

PASSWORD = "Clave1234"
PHONES = ("3009876543", "3009876544", "3009876545")


def seed(phone: str) -> None:
    user = get_by_phone(phone)
    if user is None:
        user = User(phone=phone, password_hash=hash_password(PASSWORD))
        db.session.add(user)
        db.session.commit()
        print(f"Usuario creado: teléfono {phone}, contraseña {PASSWORD}")
    else:
        print(f"Ya existe un usuario con teléfono {phone}; no se crea de nuevo.")
    if wallet_service.get_wallet_id(user.id) is None:
        wallet_service.create_wallet(user.id)
        print("Billetera creada con saldo 0.00")


def main() -> None:
    app = create_app()
    with app.app_context():
        for phone in PHONES:
            seed(phone)
        sys.exit(0)


if __name__ == "__main__":
    main()
