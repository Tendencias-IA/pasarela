# Quickstart: validar HU-08 de punta a punta

## Prerrequisitos

- Docker en marcha y `.env` creado desde `.env.example`.
- Node 22 (`nvm use` en `webapp/`), Python 3.12 (`uv venv --python 3.12 .venv` en `api/`).
- Dependencias: `cd api && uv pip install --python .venv/bin/python -e ".[dev]"`;
  `cd webapp && npm ci`.

## 1. Pruebas de la API (unitarias, contrato, e2e por HTTP)

```bash
cd api && .venv/bin/ruff check . && .venv/bin/mypy app && .venv/bin/pytest
```

Esperado: cobertura ≥ 90 %, y en la salida los tests que citan `HU-08 CA-1..CA-9`.
Las unitarias de `wallet.service` corren sin base de datos (repositorio falso).

## 2. Pruebas de integración con MySQL (atomicidad, bloqueo, idempotencia, concurrencia)

```bash
docker compose up -d mysql
cd api && DATABASE_URL="mysql+pymysql://root:$MYSQL_ROOT_PASSWORD@127.0.0.1:${MYSQL_PORT:-3306}/pasarela_test" \
  FLASK_APP=app APP_CONFIG=testing .venv/bin/flask db upgrade && .venv/bin/pytest app/modules/wallet/tests/integration -q
```

Esperado: dos hilos con la misma `Idempotency-Key` producen un solo movimiento; dos con
claves distintas producen dos; un fallo inyectado tras el `UPDATE` deja el saldo sin
cambios y sin movimiento.

## 3. Verificación manual con curl (API en Docker)

```bash
docker compose --profile app up --build -d
KEY=$(uuidgen | tr 'A-Z' 'a-z')
# Sin sesión: 401 unauthenticated
curl -s -i -X POST http://127.0.0.1:${API_PORT:-5000}/api/v1/wallet/recharges \
  -H 'Content-Type: application/json' -H 'X-Requested-With: fetch' -H "Idempotency-Key: $KEY" \
  -d '{"amount":"50000.00"}' | head -1
```

Hasta que HU-02 esté en `main` no hay cookie de sesión real; el camino exitoso se verifica
con `tests/e2e_api/test_recharge_flow.py`, que usa el fixture `logged_in_client`:

```bash
cd api && .venv/bin/pytest tests/e2e_api -q -k recharge
```

Esperado en ese test: `201` con `balance_after` = saldo previo + monto; repetir con la misma
clave → `201` + `Idempotent-Replayed: true` y saldo sin cambio; misma clave con otro
monto → `422 idempotency_key_mismatch`; `"4999.00"` → `422 amount_out_of_range` y un
movimiento `rechazada`; `"abc"` → `422 validation` sin movimiento.

## 4. Webapp

```bash
cd webapp && npm run lint && npm run typecheck && npm run test -- --coverage && npm run build
```

Esperado: `shared/money` al 100 %; `RechargePage` probada con MSW para éxito, rechazo por
rango, error de formato y 401.

Con la API arriba (paso 3):

```bash
cd webapp && npm run e2e
```

Esperado: `hu-08-recarga-saldo.spec.ts` verde en `desktop-chromium` y `mobile-chromium`:
el formulario rechaza `4999` y `abc` sin llamar a la API, el botón se deshabilita durante el
envío, axe sin violaciones serias, y ante `401` se redirige a `/login`. El escenario de éxito
en navegador queda pendiente de HU-02.

## 5. Contrato

`api/openapi.yaml` debe contener el fragmento de `contracts/recharges.openapi.yaml`;
`pytest tests/contract` valida las respuestas reales contra él, y `npm run api:types`
regenera `src/shared/api/types.gen.ts` (debe incluir `RechargeIn` y `RechargeOut`).
