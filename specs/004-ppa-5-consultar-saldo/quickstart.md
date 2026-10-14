# Quickstart: validar HU-05 de punta a punta

## Prerrequisitos

Los de HU-09 (`specs/003-ppa-9-historial-movimientos/quickstart.md`): Docker, `.env`,
Node 22, Python 3.12 con `.venv` y dependencias instaladas. No hay dependencias nuevas.

## 1. Pruebas de la API

```bash
cd api && .venv/bin/ruff format . && .venv/bin/ruff check . && .venv/bin/mypy app && .venv/bin/pytest
```

Esperado: cobertura ≥ 90 % y, en la salida, los tests que citan `HU-05 CA-1..CA-5`. Las
unitarias de `wallet.service.get_balance` corren sin base de datos
(`FakeWalletRepository`) y verifican el `WARNING wallet.missing` con `caplog`.

## 2. Flujo por HTTP contra MySQL (titularidad, 401, 404, contrato)

```bash
docker compose up -d mysql
cd api && DATABASE_URL="mysql+pymysql://root:$MYSQL_ROOT_PASSWORD@127.0.0.1:${MYSQL_PORT:-3306}/pasarela_test" \
  .venv/bin/pytest tests/e2e_api/test_balance_flow.py tests/contract/test_openapi_wallet.py -q
```

Esperado: saldo `0.00` con login real, `5000.00` tras una recarga, `?user_id=2` ignorado,
`401 invalid_session` sin cookie, `404 wallet_not_found` sin billetera y la respuesta
`200` válida contra `WalletOut` de `api/openapi.yaml`.

## 3. Verificación manual con curl

```bash
docker compose --profile app up --build -d
docker compose exec api python scripts/seed_test_user.py
curl -s -c /tmp/jar -X POST http://127.0.0.1:${API_PORT:-5000}/api/v1/auth/login \
  -H 'Content-Type: application/json' -H 'X-Requested-With: fetch' \
  -d '{"phone":"3009876543","password":"Clave1234"}' -o /dev/null -w "%{http_code}\n"
curl -s -b /tmp/jar "http://127.0.0.1:${API_PORT:-5000}/api/v1/wallet?user_id=2" | jq .
curl -s -o /dev/null -w "%{http_code}\n" "http://127.0.0.1:${API_PORT:-5000}/api/v1/wallet"
```

Esperado: `204`, `{"balance": "<saldo acumulado del usuario sembrado>"}` (el parámetro
`user_id` se ignora) y `401` sin cookie.

## 4. Webapp

```bash
cd webapp && npm run lint && npm run typecheck && npm run test -- --coverage && npm run build
```

Esperado: `useWallet` probado con MSW (saldo, 404, 401 → manejador de sesión, error de
red + `refetch`); `HomePage` muestra "Saldo disponible" con `$ 150.000,00`, el estado de
carga y "Saldo no disponible"; `useRecharge` invalida `["wallet"]` tras un `201`.

## 5. Navegador (Playwright, escritorio y móvil)

```bash
# API en 5000 con APP_CONFIG=e2e y usuarios sembrados; la webapp la levanta Playwright.
cd webapp && npx playwright test e2e/hu-05-consultar-saldo.spec.ts e2e/smoke.spec.ts
```

Esperado: tras iniciar sesión, el panel muestra la tarjeta de saldo; tras recargar
`20.000` en `/recargar` y volver al panel, el saldo subió exactamente `$ 20.000,00`; sin
sesión, `/` redirige a `/login`; axe sin violaciones `serious`/`critical`.

## 6. Carga (job nocturno)

```bash
cd api && .venv/bin/locust -f tests/load/locustfile.py --headless -u 20 -r 5 --run-time 3m --host http://127.0.0.1:5000
```

Esperado: p95 de `GET /api/v1/wallet` ≤ 2000 ms (HU-05 CA-6, RNF-02.1).
