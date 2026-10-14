# Quickstart: validar HU-09 de punta a punta

## Prerrequisitos

- Los de HU-08 (`specs/002-ppa-8-recarga-saldo/quickstart.md`): Docker, `.env`, Node 22,
  Python 3.12 con `.venv`, dependencias instaladas. Tras esta HU, `cd webapp && npm ci`
  instala además `@tanstack/react-query`.

## 1. Pruebas de la API (unitarias, contrato, e2e por HTTP)

```bash
cd api && .venv/bin/ruff format . && .venv/bin/ruff check . && .venv/bin/mypy app && .venv/bin/pytest
```

Esperado: cobertura ≥ 90 % y en la salida los tests que citan `HU-09 CA-1..CA-7`. Las
unitarias de `movements.service` corren sin base de datos (`FakeMovementsRepository`);
`app/common/masking.py` al 100 %.

## 2. Integración con MySQL (titularidad, orden estable, paginación)

```bash
docker compose up -d mysql
cd api && DATABASE_URL="mysql+pymysql://root:$MYSQL_ROOT_PASSWORD@127.0.0.1:${MYSQL_PORT:-3306}/pasarela_test" \
  .venv/bin/pytest app/modules/movements/tests/integration tests/e2e_api -q -k movements
```

Esperado: con 45 movimientos sembrados para el usuario 1 (recargas y transferencias con el
usuario 2), las páginas 1, 2 y 3 suman 45 ids distintos en orden descendente; el usuario 2
solo ve las transferencias en las que participa; la página 9 responde `items: []` y
`total: 45`; `page=0` y `page=abc` responden `422 validation`; sin sesión `401`.

## 3. Verificación manual con curl (API en Docker)

```bash
docker compose --profile app up --build -d
docker compose exec api python scripts/seed_test_user.py
# Login real (cookie en jar), una recarga y el historial
curl -s -c /tmp/jar -X POST http://127.0.0.1:${API_PORT:-5000}/api/v1/auth/login \
  -H 'Content-Type: application/json' -H 'X-Requested-With: fetch' \
  -d '{"phone":"3009876543","password":"Clave1234"}' -o /dev/null -w "%{http_code}\n"
curl -s -b /tmp/jar -X POST http://127.0.0.1:${API_PORT:-5000}/api/v1/wallet/recharges \
  -H 'Content-Type: application/json' -H 'X-Requested-With: fetch' -H "Idempotency-Key: $(uuidgen | tr A-Z a-z)" \
  -d '{"amount":"50000.00"}' -o /dev/null -w "%{http_code}\n"
curl -s -b /tmp/jar "http://127.0.0.1:${API_PORT:-5000}/api/v1/movements?page=1" | jq .
```

Esperado: `204`, `201` y un `200` cuyo primer `item` es la recarga recién hecha
(`direction: recarga`, `status: exitosa`, `amount: "50000.00"`, `counterparty: null`),
`page_size: 20` y `total` igual al número de recargas hechas hasta ahora.

## 4. Webapp

```bash
cd webapp && npm run lint && npm run typecheck && npm run test -- --coverage && npm run build
```

Esperado: `useMovements` probado con MSW (página con datos, vacío, cambio de página con
datos previos visibles, 401 → manejador de sesión); `MovementsPage` muestra fecha, monto,
tipo, estado y contraparte enmascarada, estado vacío con enlace a recargar, controles
anterior/siguiente deshabilitados en los extremos.

Con la API arriba (paso 3):

```bash
cd webapp && npm run e2e
```

Esperado: `hu-09-historial-movimientos.spec.ts` verde en `desktop-chromium` y
`mobile-chromium`: desde el panel se llega a "Movimientos" en un clic; con el usuario
sembrado, una recarga hecha en `/recargar` aparece de primera en `/movimientos`; con el
segundo usuario sembrado (sin movimientos) se ve el estado vacío; axe sin violaciones
serias; la paginación se verifica por unidad e integración (sembrar 45 movimientos en E2E
exige la API de HU-07 o datos directos, fuera del alcance del navegador).

## 5. Contrato

`api/openapi.yaml` debe contener el fragmento de `contracts/movements.openapi.yaml`;
`pytest tests/contract` valida la respuesta real contra `MovementsPageOut`, y
`npm run api:types` regenera `types.gen.ts` (debe incluir `MovementOut` y
`MovementsPageOut`).
