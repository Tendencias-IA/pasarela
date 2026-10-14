# Quickstart: validar Iniciar sesión (HU-02)

## Prerrequisitos

```bash
cd api
cp .env.example .env   # primera vez
docker compose up -d mysql
flask db upgrade
```

## Sembrar un usuario de prueba

No existe aún un endpoint de registro (HU-01); se crea directamente con la factory de
pruebas o con una consola Python:

```bash
cd api
python - <<'PY'
from app import create_app
from app.extensions import db
from app.modules.accounts.models import User
from app.common.passwords import hash_password

app = create_app("development")
with app.app_context():
    db.session.add(User(phone="3009876543", password_hash=hash_password("Clave1234")))
    db.session.commit()
PY
```

## Validar el camino exitoso (US1)

```bash
curl -i -c cookies.txt -X POST http://127.0.0.1:5000/api/v1/auth/login \
  -H "Content-Type: application/json" -H "X-Requested-With: fetch" \
  -d '{"phone": "3009876543", "password": "Clave1234"}'
# Esperado: 200, Set-Cookie con la sesión, cuerpo {"user_id": <id>}
```

## Validar credenciales inválidas sin filtrar cuál falló (US2)

```bash
curl -i -X POST http://127.0.0.1:5000/api/v1/auth/login \
  -H "Content-Type: application/json" -H "X-Requested-With: fetch" \
  -d '{"phone": "3000000000", "password": "cualquiera"}'
# Esperado: 401, code "invalid_credentials"

curl -i -X POST http://127.0.0.1:5000/api/v1/auth/login \
  -H "Content-Type: application/json" -H "X-Requested-With: fetch" \
  -d '{"phone": "3009876543", "password": "incorrecta"}'
# Esperado: 401, mismo code "invalid_credentials" y mismo mensaje que el caso anterior
```

## Validar la puerta de acceso (US3)

Sin cookie de sesión, cualquier ruta protegida con `@login_required` responde `401`. Se
puede comprobar contra la ruta de pruebas de integración (`auth/tests/integration/
test_routes.py`), que registra una ruta privada mínima solo para esta verificación,
hasta que exista una función privada real (`GET /wallet`, HU-05).

```bash
curl -i -b cookies.txt -X POST http://127.0.0.1:5000/api/v1/auth/logout \
  -H "X-Requested-With: fetch"
# Esperado: 204

curl -i -b cookies.txt -X POST http://127.0.0.1:5000/api/v1/auth/logout \
  -H "X-Requested-With: fetch"
# Esperado ahora: 401 (la sesión ya fue revocada)
```

## Pruebas automáticas

```bash
cd api && pytest app/modules/accounts app/modules/auth tests/contract/test_auth_contract.py
```

Referencias: contrato en [contracts/auth.openapi.yaml](./contracts/auth.openapi.yaml),
modelo de datos en [data-model.md](./data-model.md).
