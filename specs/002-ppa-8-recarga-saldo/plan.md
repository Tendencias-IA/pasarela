# Implementation Plan: Recarga simulada de saldo (HU-08)

**Branch**: `feat/PPA-8-recarga-saldo` | **Date**: 2026-10-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-ppa-8-recarga-saldo/spec.md`

## Summary

Un usuario autenticado acredita un monto ficticio entre $5.000 y $5.000.000 COP en su
billetera. Se implementa el módulo `wallet` (API y webapp) con el endpoint
`POST /api/v1/wallet/recharges`, protegido por sesión e `Idempotency-Key`, que en una sola
transacción bloquea la billetera, incrementa el saldo con `Decimal`, registra el movimiento
`recarga` en la tabla compartida `transactions` y guarda la respuesta idempotente. La
pantalla de recarga usa Ionic y muestra éxito o rechazo con el nuevo saldo. Como esta es la
primera historia con tablas de dinero, el plan también crea los cimientos transversales que
`architecture.md` ya define: `app/common/money.py`, `app/common/idempotency.py`,
`app/common/models/transaction.py`, `app/common/auth.py` (solo la interfaz) y las
migraciones de `wallets`, `transactions` e `idempotency_keys`.

## Technical Context

**Language/Version**: Python 3.12 (API), TypeScript 5.9 / React 18 (webapp)

**Primary Dependencies**: Flask 3, SQLAlchemy 2, Flask-Migrate/Alembic, Pydantic 2; Ionic React 9, react-router-dom 6; ya instaladas, sin dependencias nuevas

**Storage**: MySQL 8 (InnoDB). Tablas nuevas: `wallets`, `transactions`, `idempotency_keys`

**Testing**: pytest + pytest-cov (unitarias con repositorio falso, integración con MySQL, contrato con `openapi.yaml`, e2e_api con el test client), Vitest + MSW, Playwright (`hu-08-recarga-saldo.spec.ts`)

**Target Platform**: web responsive (escritorio y móvil) servida por nginx; API en gunicorn

**Project Type**: web application (`api/` + `webapp/`)

**Performance Goals**: p95 ≤ 3 s por recarga con 20 usuarios concurrentes (RNF-02.3, RNF-02.4)

**Constraints**: dinero `Decimal`/`DECIMAL(15,2)`/cadena JSON; operación atómica con `SELECT ... FOR UPDATE`; `Idempotency-Key` obligatoria; estados solo `exitosa`/`rechazada`; sesión del lado del servidor (la implementa HU-02); sin CORS, mismo origen

**Scale/Scope**: 1 endpoint, 3 tablas, 1 pantalla, ~15 archivos nuevos en `api/`, ~8 en `webapp/`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cómo se cumple en este plan |
| --- | --- |
| I. Especificación antes de código | `spec.md` aprobada con 16/16 en el checklist; este plan y `tasks.md` preceden a cualquier código. |
| II. Trazabilidad | Cada test cita `HU-08 CA-n` o `RNF-x`; el endpoint y los errores (`amount_out_of_range`, `idempotency_key_mismatch`) salen de FR-002, FR-003 y FR-007. |
| III. Pruebas primero, cobertura ≥ 90 % | Tareas de test preceden a cada implementación; unitarias de `wallet.service` con `FakeWalletRepository`; integración de atomicidad, bloqueo e idempotencia con MySQL; contrato; Vitest; Playwright. |
| IV. Monolito modular, vertical slicing | Todo el negocio en `app/modules/wallet/`; lo compartido (`money`, `idempotency`, `models/transaction`, `auth`) en `app/common/` tal como lo dibuja `architecture.md`; no se importa nada de `auth`/`accounts`. |
| V. Integridad del dinero | `Decimal` cuantizado a 2 decimales; `DECIMAL(15,2)` + `CHECK (balance >= 0)`; una transacción con `FOR UPDATE` sobre la billetera; `Idempotency-Key` persistida en la misma transacción (éxito) o en la segunda (rechazo). |
| VI. Seguridad y privacidad | `@login_required`; el `user_id` sale de `g.user_id`, nunca del cuerpo; `X-Requested-With` ya exigido globalmente; logs con `request_id`, monto y `user_id`, sin datos personales. |
| VII. Simplicidad | Sin colas, caché ni abstracciones nuevas; un repositorio concreto; la interfaz de sesión son dos funciones. |

**Gate pre-research**: PASS. **Desviaciones**: ninguna; ver Complexity Tracking solo para el riesgo de E2E sin login.

## Project Structure

### Documentation (this feature)

```text
specs/002-ppa-8-recarga-saldo/
├── plan.md              # Este archivo
├── spec.md
├── research.md          # Fase 0: decisiones de diseño y alternativas
├── data-model.md        # Fase 1: tablas, invariantes, estados
├── quickstart.md        # Fase 1: cómo validar de punta a punta
├── contracts/
│   └── recharges.openapi.yaml   # Fase 1: fragmento que se fusiona en api/openapi.yaml
├── checklists/requirements.md
└── tasks.md             # Lo genera /speckit-tasks
```

### Source Code (repository root)

```text
api/
├── app/
│   ├── __init__.py                      # registra wallet.bp con prefijo /api/v1/wallet
│   ├── common/
│   │   ├── auth.py                      # NUEVO: login_required, current_user_id() sobre g.user_id (interfaz; HU-02 la alimenta)
│   │   ├── money.py                     # NUEVO: parse_amount, quantize, RECHARGE_MIN/MAX, TRANSFER_MIN/MAX
│   │   ├── idempotency.py               # NUEVO: @idempotent, IdempotencyContext, replay/mismatch, request_hash
│   │   ├── errors.py                    # + UnauthenticatedError, MissingIdempotencyKeyError, IdempotencyKeyMismatchError
│   │   └── models/
│   │       ├── __init__.py              # NUEVO
│   │       ├── transaction.py           # NUEVO: Transaction (ADR-0006), enums TransactionType/TransactionStatus
│   │       └── idempotency_key.py       # NUEVO: IdempotencyKey
│   └── modules/wallet/
│       ├── __init__.py                  # NUEVO: expone bp
│       ├── models.py                    # NUEVO: Wallet
│       ├── schemas.py                   # NUEVO: RechargeIn, RechargeOut, TransactionOut
│       ├── repository.py                # NUEVO: lock_wallet_for_user, add_transaction, add_idempotency_key, get_wallet
│       ├── service.py                   # NUEVO: recharge(), create_wallet() (para HU-01), AmountOutOfRangeError, WalletNotFoundError
│       ├── routes.py                    # NUEVO: POST /recharges
│       └── tests/
│           ├── unit/test_recharge_service.py
│           ├── unit/fakes.py            # FakeWalletRepository
│           └── integration/test_recharge_db.py   # atomicidad, FOR UPDATE, idempotencia, concurrencia
├── migrations/versions/
│   └── 0001_wallets_transactions_idempotency.py  # NUEVO
├── tests/
│   ├── conftest.py                      # + fixtures: logged_in_client(user_id), mysql opcional por DATABASE_URL
│   ├── contract/test_openapi_recharges.py
│   └── e2e_api/test_recharge_flow.py
└── openapi.yaml                         # + /api/v1/wallet/recharges, schemas Recharge*, Problem codes

webapp/
├── src/
│   ├── app/
│   │   ├── App.tsx                      # + IonReactRouter con rutas "/" y "/recargar"
│   │   └── routes.tsx                   # NUEVO
│   ├── features/wallet/
│   │   ├── RechargePage.tsx             # NUEVO: IonPage con IonInput (monto), IonButton, resultado
│   │   ├── useRecharge.ts               # NUEVO: estado, Idempotency-Key por intento, llamada a api
│   │   ├── api.ts                       # NUEVO: postRecharge()
│   │   └── __tests__/RechargePage.test.tsx
│   └── shared/
│       ├── money/
│       │   ├── index.ts                 # NUEVO: parseAmountInput, formatCOP, isWithinRange
│       │   └── __tests__/money.test.ts
│       └── ui/
│           └── ResultBanner.tsx         # NUEVO: éxito/rechazo con role status/alert
├── e2e/
│   ├── pages/recharge.page.ts           # NUEVO
│   └── hu-08-recarga-saldo.spec.ts      # NUEVO
└── src/shared/api/types.gen.ts          # regenerado con npm run api:types
```

**Structure Decision**: aplicación web `api/` + `webapp/` ya existente; la HU vive en el
slice `wallet` de ambos lados. Los archivos de `app/common/` son los que `architecture.md`
ya prevé; esta historia los crea porque es la primera que mueve dinero.

## Phase 0: Research

Ver [research.md](research.md). Resumen de decisiones:

1. **Interfaz de sesión** sin tocar `auth`: `app/common/auth.py` expone `login_required` y
   `current_user_id()` leyendo `g.user_id`; si no está, `401 unauthenticated`. HU-02 instala
   el `before_request` que llena `g.user_id` desde la cookie. Las pruebas usan un fixture que
   registra un `before_request` de prueba.
2. **Idempotencia en dos capas**: el decorador `@idempotent` en la ruta exige y valida la
   cabecera, resuelve replay y conflicto; el servicio persiste la fila `idempotency_keys`
   dentro de la misma transacción del saldo (éxito) o de la segunda transacción (rechazo).
3. **`wallets.user_id` con FK a `users`**: HU-02 ya creó `users` en `main` (migración
   0001); la de esta HU es la `0002` y la incluye.
4. **Rechazo por rango se registra como `rechazada`**; errores de formato (no numérico,
   decimales de más) son `422 validation` sin registro.
5. **E2E con login real**: el spec de Playwright inicia sesión con el usuario de
   `scripts/seed_test_user.py` y verifica la recarga de punta a punta; además, el camino
   completo se prueba por HTTP en `tests/e2e_api`.

## Phase 1: Design

- [data-model.md](data-model.md): `wallets`, `transactions`, `idempotency_keys`, invariantes y
  estados.
- [contracts/recharges.openapi.yaml](contracts/recharges.openapi.yaml): `POST
  /api/v1/wallet/recharges`, cabeceras, cuerpos, códigos y `Problem.code`.
- [quickstart.md](quickstart.md): cómo levantar, probar y verificar con curl, pytest y
  Playwright.

**Constitution Check post-diseño**: PASS. La única fricción es la dependencia de HU-02 para
el E2E en navegador; no viola ningún principio, se registra como riesgo.

## Complexity Tracking

> Sin violaciones a la constitución. Riesgos y acuerdos con el equipo:

| Riesgo | Mitigación |
| --- | --- |
| HU-01 (Melanny) también necesita crear la billetera al registrar | Este plan expone `wallet_service.create_wallet(user_id)` y el modelo `Wallet`; se le avisa en el PR para que lo reutilice en lugar de crear otro. |
| HU-02 (Moisés) define cómo se llena `g.user_id` | `app/common/auth.py` fija el contrato (dos funciones, un error `unauthenticated`); se le avisa en el PR. |
| FK `wallets.user_id → users.id` ausente hasta que HU-01 llegue a `main` | Tarea de seguimiento en Jira para la migración de la FK. |
| Camino exitoso E2E en navegador requiere login | Cubierto por `tests/e2e_api` vía HTTP; tarea Playwright marcada como bloqueada por HU-02. |
