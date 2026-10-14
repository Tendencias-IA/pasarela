---

description: "Tareas de implementación de HU-08 Recarga simulada de saldo (PPA-8)"
---

# Tasks: Recarga simulada de saldo (HU-08)

**Input**: Design documents from `specs/002-ppa-8-recarga-saldo/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/recharges.openapi.yaml, quickstart.md

**Tests**: OBLIGATORIAS (constitución, principio III). Cada test se escribe antes de la
implementación que cubre, falla primero, y cita en su nombre o docstring el criterio
(`HU-08 CA-n`, `RNF-x`, `FR-nnn`).

**Organization**: por historia de usuario de `spec.md` (US1 recarga válida, US2 rechazo de
montos inválidos, US3 idempotencia, US4 autenticación y titularidad). Las fases 1 y 2
crean los cimientos compartidos que `architecture.md` prevé y aún no existen.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede ejecutarse en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: historia a la que pertenece (US1, US2, US3, US4)
- Rutas exactas en cada tarea; todas relativas a la raíz del repo

## Path Conventions

- API: `api/app/...`, pruebas en `api/app/modules/wallet/tests/` y `api/tests/`
- Webapp: `webapp/src/...`, E2E en `webapp/e2e/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: dinero, errores y sesión como utilidades transversales, sin negocio.

- [x] T001 [P] Test unitario de `parse_amount`/`quantize` en `api/app/common/tests/test_money.py`: acepta `"50000"`, `"50000.5"`, `"50000.50"`; rechaza `""`, `"abc"`, `"-1"`, `"1.234"`, `"NaN"`, `"1e3"`; cuantiza a 2 decimales con `ROUND_HALF_UP`; expone `RECHARGE_MIN = Decimal("5000.00")`, `RECHARGE_MAX = Decimal("5000000.00")`, `TRANSFER_MIN`, `TRANSFER_MAX` (RNF-04.3, FR-013)
- [x] T002 [P] Implementar `api/app/common/money.py`: constantes de límites, `parse_amount(value: str) -> Decimal` (lanza `ValueError` con mensaje en español), `quantize(amount) -> Decimal`, `to_json(amount) -> str` con dos decimales
- [x] T003 [P] Test de `app/common/auth.py` en `api/app/common/tests/test_auth.py`: ruta decorada con `@login_required` responde `401` problem `unauthenticated` sin `g.user_id`, y pasa con `g.user_id` fijado por un `before_request` de prueba; `current_user_id()` devuelve el entero (RNF-01.1, FR-012)
- [x] T004 [P] Implementar `api/app/common/auth.py`: `UnauthenticatedError(AppError)` con `status=401, code="unauthenticated", title="Sesión requerida"`, `current_user_id() -> int` que lee `g.user_id`, decorador `login_required` (usa `functools.wraps`, tipado con `ParamSpec`). Solo la interfaz: HU-02 llenará `g.user_id`
- [x] T005 Añadir a `api/tests/conftest.py` los fixtures `logged_in_client(app, user_id=1)` (registra `before_request` que asigna `g.user_id`) y `mysql_url` (lee `DATABASE_URL`; si apunta a sqlite, `pytest.skip` en las pruebas marcadas `@pytest.mark.mysql`); registrar el marker `mysql` en `api/pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: modelos compartidos, migración e idempotencia; sin esto ninguna historia puede escribir dinero.

**⚠️ CRITICAL**: ninguna tarea de US1 a US4 empieza hasta cerrar esta fase.

- [x] T006 [P] Crear `api/app/common/models/__init__.py` y `api/app/common/models/transaction.py`: modelo `Transaction` (tabla `transactions`) con `id BIGINT PK`, `type` Enum `TransactionType {transferencia, recarga}`, `status` Enum `TransactionStatus {exitosa, rechazada}`, `amount Numeric(15,2, asdecimal=True) NOT NULL CHECK amount > 0`, `sender_wallet_id BIGINT NULL FK wallets.id`, `receiver_wallet_id BIGINT NOT NULL FK wallets.id`, `rejection_reason VARCHAR(64) NULL`, `created_at DATETIME(6) server_default now`; índices `(receiver_wallet_id, created_at)` y `(sender_wallet_id, created_at)` (ADR-0006, data-model.md)
- [x] T007 [P] Crear `api/app/common/models/idempotency_key.py`: modelo `IdempotencyKey` (tabla `idempotency_keys`) con PK compuesta `(user_id BIGINT, key CHAR(36))`, `request_hash CHAR(64) NOT NULL`, `status_code SMALLINT NOT NULL`, `response_body JSON NOT NULL`, `created_at DATETIME(6)` (ADR-0005)
- [x] T008 [P] Crear `api/app/modules/wallet/__init__.py` y `api/app/modules/wallet/models.py`: modelo `Wallet` (tabla `wallets`) con `id BIGINT PK`, `user_id BIGINT NOT NULL UNIQUE` (sin FK a `users`, research §3), `balance Numeric(15,2) NOT NULL default 0 CHECK balance >= 0`, `created_at`, `updated_at` con `onupdate`
- [x] T009 Importar los tres modelos en `api/app/__init__.py` (para que Alembic los vea) y generar la migración `api/migrations/versions/0001_wallets_transactions_idempotency.py` con `flask db migrate -m "ppa-8 wallets transactions idempotency"`; revisar a mano que incluya los `CHECK`, los `ENUM`, `DECIMAL(15,2)`, `JSON` y los índices; `down_revision = None`
- [x] T010 Test unitario del decorador en `api/app/common/tests/test_idempotency.py` con una ruta de prueba: sin cabecera → `400 missing_idempotency_key`; cabecera no UUID → `400`; clave nueva → ejecuta la vista y deja `g.idempotency` con `key` y `request_hash` sha256 de `método + ruta + cuerpo canónico`; clave existente con mismo hash → responde el `response_body` guardado con `status_code` guardado y cabecera `Idempotent-Replayed: true` sin ejecutar la vista; clave existente con hash distinto → `422 idempotency_key_mismatch` (HU-08 CA-6, FR-007). Usa un `IdempotencyStore` falso inyectado
- [x] T011 Implementar `api/app/common/idempotency.py`: `IdempotencyContext(key, request_hash)` dataclass frozen, `MissingIdempotencyKeyError` (400) e `IdempotencyKeyMismatchError` (422) en `api/app/common/errors.py`, función `request_hash(method, path, body: bytes) -> str` (JSON canónico `sort_keys`, sin espacios), `find_existing(user_id, key)` (consulta `IdempotencyKey`), y decorador `idempotent` que aplica las reglas de T010 y lanza los errores; la persistencia de la clave NO ocurre aquí (la hace el repositorio dentro de la transacción)

**Checkpoint**: `pytest api/app/common` verde; `flask db upgrade` contra MySQL crea las tres tablas.

---

## Phase 3: User Story 1 - Recargar saldo con un monto válido (Priority: P1) 🎯 MVP

**Goal**: `POST /api/v1/wallet/recharges` acredita el monto en una sola transacción, registra el movimiento `recarga/exitosa` y devuelve el nuevo saldo; la pantalla `/recargar` permite hacerlo con dos clics.

**Independent Test**: con `logged_in_client(user_id=1)` y una billetera en 0, enviar `{"amount":"50000.00"}` con `Idempotency-Key` válida → `201`, `balance_after == "50000.00"`, una fila en `transactions` tipo `recarga` estado `exitosa`.

### Tests for User Story 1 ⚠️ (escribir primero, deben fallar)

- [x] T012 [P] [US1] Crear `api/app/modules/wallet/tests/unit/fakes.py` con `FakeWalletRepository` (billeteras en memoria, `lock_wallet_for_user`, `add_transaction`, `add_idempotency_key`, registro de llamadas) y `api/app/modules/wallet/tests/unit/test_recharge_service.py` con: `test_recharge_min_amount_increases_balance_and_records_transaction` (HU-08 CA-1, CA-3, CA-4), `test_recharge_max_amount_has_no_balance_cap` (CA-7, con saldo previo 4.995.000), `test_recharge_keeps_two_decimals_exactly` (RNF-04.3, `"120500.50"`), `test_recharge_persists_idempotency_key_in_same_unit_of_work` (FR-006: la clave se escribe antes de cerrar la transacción), `test_recharge_without_wallet_raises_wallet_not_found` (edge case)
- [x] T013 [P] [US1] Test de contrato en `api/tests/contract/test_openapi_recharges.py`: la respuesta `201` de `POST /api/v1/wallet/recharges` valida contra el schema `RechargeOut` de `api/openapi.yaml` (montos como cadena `^\d{1,13}\.\d{2}$`, `type == "recarga"`, `status == "exitosa"`, `created_at` ISO 8601) usando `jsonschema` sobre el YAML cargado (sin `schemathesis` si no está instalado)
- [x] T014 [P] [US1] Test e2e por HTTP en `api/tests/e2e_api/test_recharge_flow.py` (marker `mysql`): crear billetera vía `wallet_service.create_wallet(1)`, `POST` con `logged_in_client` → `201` y saldo; segundo `POST` de `"20000.00"` → `balance_after == "70000.00"`; consulta directa a `transactions` muestra dos filas `exitosa` (HU-08 CA-3, CA-4, RNF-05.1)

### Implementation for User Story 1

- [x] T015 [US1] Implementar `api/app/modules/wallet/repository.py`: `get_wallet_by_user(user_id) -> Wallet | None`, `create_wallet(user_id) -> Wallet`, `lock_wallet_for_user(user_id) -> Wallet | None` (`select(Wallet).where(...).with_for_update()`), `add_transaction(**fields) -> Transaction` (`session.add` + `flush` para obtener `id`), `add_idempotency_key(user_id, key, request_hash, status_code, response_body)`; sin `commit`
- [x] T016 [US1] Implementar `api/app/modules/wallet/service.py`: `RechargeResult` dataclass frozen; `create_wallet(user_id)` (para HU-01); `recharge(user_id, amount: Decimal, idempotency: IdempotencyContext, repo=default_repository) -> RechargeResult` con `with db.session.begin():` → lock → `WalletNotFoundError` (404 `wallet_not_found`) → validar rango con `RECHARGE_MIN/MAX` → `wallet.balance += amount` → `add_transaction(recarga, exitosa, receiver=wallet.id)` → `add_idempotency_key(201, body)`; el cuerpo guardado es `RechargeResult` serializado con `to_json`; logs `recharge.applied` con `user_id`, `amount`, `transaction_id`, sin datos personales (RNF-06)
- [x] T017 [US1] Implementar `api/app/modules/wallet/schemas.py`: `RechargeIn(amount: str)` con validador que usa `parse_amount` y convierte errores a `ValidationError(errors=[{"field":"amount","message":...}])`, rechazando `int`/`float` JSON (`strict=True`); `RechargeOut(id, type, status, amount: str, balance_after: str, created_at)` con `from_result(RechargeResult)`
- [x] T018 [US1] Implementar `api/app/modules/wallet/routes.py`: `bp = Blueprint("wallet", __name__)`, `@bp.post("/recharges")` con `@login_required` y `@idempotent`, parsea `RechargeIn`, llama `service.recharge(current_user_id(), payload.amount, g.idempotency)`, devuelve `RechargeOut`, `201`; registrar `bp` en `api/app/__init__.py` con `url_prefix="/api/v1/wallet"`
- [x] T019 [US1] Fusionar `specs/002-ppa-8-recarga-saldo/contracts/recharges.openapi.yaml` en `api/openapi.yaml` (path, `securitySchemes.sessionCookie`, schemas `Money`, `RechargeIn`, `RechargeOut`) y regenerar `webapp/src/shared/api/types.gen.ts` con `npm run api:types`
- [x] T020 [P] [US1] Tests de `webapp/src/shared/money/__tests__/money.test.ts`: `parseAmountInput("50.000")`, `("50000,50")`, `("50000.5")` → `"50000.00"`/`"50000.50"`; `("abc")`, `("")`, `("-1")`, `("1.234")` → `null`; `isWithinRange("4999.00", RECHARGE_MIN, RECHARGE_MAX) === false`, `("5000.00") === true`, `("5000000.00") === true`, `("5000000.01") === false`; `formatCOP("50000.00") === "$ 50.000,00"` (sin `Number` para decidir; comparación por `BigInt` de centavos). Cobertura 100 % (`testing.md`)
- [x] T021 [P] [US1] Implementar `webapp/src/shared/money/index.ts`: `parseAmountInput(raw: string): string | null`, `isWithinRange(amount, min, max): boolean`, `formatCOP(amount: string): string` con `Intl.NumberFormat("es-CO")`, constantes `RECHARGE_MIN = "5000.00"`, `RECHARGE_MAX = "5000000.00"`
- [x] T022 [P] [US1] Test de componente `webapp/src/features/wallet/__tests__/RechargePage.test.tsx` con MSW: escribir `50000`, pulsar "Recargar" → se llama `POST /api/v1/wallet/recharges` con `Idempotency-Key` UUID y `X-Requested-With: fetch`; se muestra `role="status"` "Recarga exitosa" y "Saldo: $ 50.000,00" (HU-08 CA-3, CA-9); el botón queda deshabilitado mientras la petición está en vuelo (FR-011)
- [x] T023 [US1] Implementar `webapp/src/features/wallet/api.ts` (`postRecharge(amount, idempotencyKey)` usando `request<RechargeOut>`), `webapp/src/features/wallet/useRecharge.ts` (estado `idle|submitting|success|rejected`, genera `crypto.randomUUID()` al abrir y lo renueva solo cuando cambia el monto, FR-011) y `webapp/src/features/wallet/RechargePage.tsx` (`IonPage` + `IonHeader` "Recargar saldo" + `IonContent` con `IonInput label="Monto (COP)" inputmode="decimal" required`, `IonButton` "Recargar", y `ResultBanner`)
- [x] T024 [US1] Crear `webapp/src/shared/ui/ResultBanner.tsx`: variante `success` (`role="status"`, icono `checkmarkCircle`) y `rejected` (`role="alert"`, icono `closeCircle`), texto e importe formateado; sin color como único indicador (RNF-03.4)
- [x] T025 [US1] Enrutar: `webapp/src/app/routes.tsx` con `IonReactRouter` + `IonRouterOutlet`, rutas `/` (pantalla de estado actual, movida a `webapp/src/app/HomePage.tsx` con `IonButton routerLink="/recargar"` "Recargar saldo") y `/recargar` (`RechargePage`); `App.tsx` renderiza `IonApp` + `routes`; actualizar `webapp/src/app/__tests__/App.test.tsx` para la nueva estructura
- [x] T026 [US1] Page object `webapp/e2e/pages/recharge.page.ts` (`goto()`, `fillAmount()`, `submit()`, `result()`, `fieldError()`) y spec `webapp/e2e/hu-08-recarga-saldo.spec.ts` con el escenario de navegación: desde `/` el botón "Recargar saldo" lleva a `/recargar` en un clic (RNF-03.1) y la página no tiene violaciones `serious`/`critical` de axe (SC-006)

**Checkpoint**: `pytest` verde (incluido `e2e_api` contra MySQL), `npm run test`, `npm run e2e` con los escenarios de US1.

---

## Phase 4: User Story 2 - Rechazo de montos inválidos sin tocar el saldo (Priority: P1)

**Goal**: fuera de rango → `422 amount_out_of_range` con movimiento `rechazada`; formato inválido → `422 validation` sin movimiento; el saldo nunca cambia; la pantalla muestra el motivo junto al campo.

**Independent Test**: con saldo 10.000, enviar `"4999.00"`, `"5000000.01"`, `"abc"`, `""`, `"-5"`, `"1.234"`: todas `422`, saldo sigue en 10.000; solo las dos primeras dejan fila `rechazada`.

### Tests for User Story 2 ⚠️

- [x] T027 [P] [US2] Añadir a `test_recharge_service.py`: `test_recharge_below_min_is_rejected_without_changing_balance` (HU-08 CA-2, CA-5), `test_recharge_above_max_is_rejected` (CA-2), `test_rejected_recharge_records_rejected_transaction_and_idempotency_key_in_second_unit_of_work` (FR-006, FR-007: tras el rollback el fake registra una segunda unidad de trabajo con `status=rechazada`, `rejection_reason="amount_out_of_range"` y clave con `422`)
- [x] T028 [P] [US2] Añadir a `api/app/modules/wallet/tests/unit/test_schemas.py`: `RechargeIn` rechaza `""`, `"abc"`, `"-5"`, `"1.234"`, `50000` (número JSON) y `null` con `errors[0].field == "amount"` y mensaje en español; acepta `"5000"` → `Decimal("5000.00")` (HU-08 CA-2, FR-003)
- [x] T029 [P] [US2] Añadir a `test_recharge_flow.py`: `"4999.00"` → `422 amount_out_of_range`, `errors[0].message` menciona `5000.00` y `5000000.00`, saldo intacto y una fila `rechazada`; `"abc"` → `422 validation` y sin fila nueva (HU-08 CA-2, CA-5)
- [x] T030 [P] [US2] Añadir a `RechargePage.test.tsx`: `4999` muestra error junto al campo sin llamar a la API; respuesta MSW `422 amount_out_of_range` muestra `role="alert"` con el `detail`; `422 validation` muestra `errors[0].message` en el campo (HU-08 CA-9, RNF-03.2)

### Implementation for User Story 2

- [x] T031 [US2] En `api/app/modules/wallet/service.py`: `AmountOutOfRangeError(AppError)` (422, `amount_out_of_range`, `title="Monto fuera de rango"`, `detail` y `errors=[{"field":"amount","message":"Debe estar entre 5000.00 y 5000000.00"}]`); envolver la transacción principal en `try/except AppError` que abre una segunda `with db.session.begin()` con `add_transaction(status=rechazada, rejection_reason=exc.code)` y `add_idempotency_key(exc.status, problem_body(exc))`, y relanza (patrón de `architecture.md`); log `recharge.rejected` con `reason`
- [x] T032 [US2] Añadir en `api/app/common/errors.py` la función `problem_body(exc: AppError, instance: str) -> dict` reutilizada por el handler y por el servicio para guardar el mismo cuerpo que se devolverá
- [x] T033 [US2] En `webapp/src/features/wallet/RechargePage.tsx`: validación en cliente con `parseAmountInput` + `isWithinRange` (mensaje "Debe estar entre $ 5.000,00 y $ 5.000.000,00"), `errorText` y clases `ion-invalid ion-touched` en `IonInput`, mapeo de `ApiError.messagesByField()` al campo y de `ApiError.message` al `ResultBanner rejected`
- [x] T034 [US2] Añadir a `hu-08-recarga-saldo.spec.ts`: `4999` y `abc` muestran el error junto al campo y no disparan petición (interceptar con `page.waitForRequest` negativo), en escritorio y móvil (HU-08 CA-2, CA-9)

**Checkpoint**: US1 y US2 verdes de forma independiente.

---

## Phase 5: User Story 3 - La misma solicitud no se acredita dos veces (Priority: P2)

**Goal**: replay exacto con la misma clave, conflicto con cuerpo distinto, rechazo sin clave; concurrencia segura.

**Independent Test**: dos `POST` idénticos con la misma clave → un solo movimiento, segunda respuesta igual a la primera con `Idempotent-Replayed: true`.

### Tests for User Story 3 ⚠️

- [x] T035 [P] [US3] Añadir a `test_recharge_flow.py`: misma clave y cuerpo → `201` + `Idempotent-Replayed: true`, saldo y número de filas sin cambio; misma clave y monto distinto → `422 idempotency_key_mismatch`; sin cabecera → `400 missing_idempotency_key` y sin fila (HU-08 CA-6, FR-007)
- [x] T036 [P] [US3] Test de integración `api/app/modules/wallet/tests/integration/test_recharge_db.py` (marker `mysql`): `test_concurrent_same_key_applies_once` (dos hilos con `threading.Barrier`, misma clave: un `201` real y un replay; saldo = monto; una fila `exitosa`), `test_concurrent_distinct_keys_apply_both` (saldo = suma, RNF-04.2), `test_failure_after_update_rolls_back_everything` (inyectar excepción en `add_idempotency_key` con `mocker`: saldo y `transactions` sin cambios, RNF-04.5, FR-006), `test_lock_wallet_uses_for_update` (inspeccionar el SQL emitido con `sqlalchemy.event` por `FOR UPDATE`)
- [x] T037 [P] [US3] Añadir a `RechargePage.test.tsx`: doble clic en "Recargar" produce una sola petición y la misma `Idempotency-Key`; cambiar el monto tras un intento genera una clave distinta (FR-011)

### Implementation for User Story 3

- [x] T038 [US3] En `api/app/common/idempotency.py` y `api/app/modules/wallet/service.py`: capturar `IntegrityError` por PK duplicada en `add_idempotency_key` (carrera entre dos peticiones con la misma clave): rollback y responder con el replay de la fila ganadora (research §2); test en T036 lo cubre
- [x] T039 [US3] En `useRecharge.ts`: `submitting` bloquea envíos repetidos; la clave se conserva entre reintentos con el mismo monto y se regenera al editar el monto; en `RechargePage.tsx` el `IonButton` lleva `disabled={state === "submitting"}` (FR-011)
- [x] T040 [US3] Añadir a `hu-08-recarga-saldo.spec.ts`: el botón queda deshabilitado durante el envío (interceptar la petición con `page.route` y retrasarla 1 s) y vuelve a habilitarse al terminar

**Checkpoint**: idempotencia probada en unidad, HTTP, base de datos y navegador.

---

## Phase 6: User Story 4 - Solo el titular autenticado puede recargar (Priority: P2)

**Goal**: sin sesión → `401`; con sesión, siempre la billetera propia.

**Independent Test**: `client` sin `g.user_id` → `401 unauthenticated` y sin filas; `logged_in_client(user_id=1)` con cuerpo que intenta `{"amount":"5000.00","user_id":2}` → `422 validation` por campo no permitido (`additionalProperties: false`).

### Tests for User Story 4 ⚠️

- [x] T041 [P] [US4] Añadir a `test_recharge_flow.py`: sin sesión → `401 unauthenticated`, `transactions` vacía (RNF-01.1); con sesión de usuario 1 y campo extra `user_id` → `422 validation`, y la billetera del usuario 2 no cambia (RNF-01.4, RNF-06.1)
- [x] T042 [P] [US4] Añadir a `RechargePage.test.tsx`: respuesta MSW `401 session_expired` invoca el manejador de sesión expirada (redirige a `/login`) y no muestra éxito (HU-04 CA-2)

### Implementation for User Story 4

- [x] T043 [US4] En `api/app/modules/wallet/schemas.py`: `RechargeIn` con `model_config = ConfigDict(extra="forbid", strict=True)`; en `routes.py` el `user_id` proviene exclusivamente de `current_user_id()` (ya en T018; verificar y añadir comentario de regla `security.md`)
- [x] T044 [US4] Añadir a `hu-08-recarga-saldo.spec.ts`: con `page.route` devolviendo `401 session_expired` al enviar, la webapp redirige a `/login` (hasta HU-02 la ruta `/login` muestra el placeholder "Inicio de sesión pendiente (HU-02)" en `webapp/src/app/routes.tsx`)
- [ ] T045 [US4] **BLOQUEADA POR HU-02**: escenario de éxito en navegador en `hu-08-recarga-saldo.spec.ts` (iniciar sesión real, recargar `50000`, ver "Recarga exitosa" y el saldo); dejar `test.skip(true, "Bloqueado por HU-02: requiere login real")` con la referencia a PPA-2 y crear la tarea de seguimiento en Jira al abrir el PR

**Checkpoint**: todas las historias verdes; cobertura de `api` ≥ 90 %.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [x] T046 [P] Actualizar `api/.env.example` si se añadió alguna variable (no se prevé) y `README.md` con la ruta `/recargar` en el mapa de la webapp
- [x] T047 [P] Añadir en `api/tests/load/locustfile.py` la tarea `POST /api/v1/wallet/recharges` documentada pero desactivada (`@task(0)` con comentario "activar cuando HU-02 provea login en Locust"), sin romper la ejecución nocturna (CA-10, RNF-02.3)
- [x] T048 Ejecutar `cd api && .venv/bin/ruff format . && .venv/bin/ruff check . && .venv/bin/mypy app && .venv/bin/pytest` y `cd webapp && npm run lint && npm run typecheck && npm run test -- --coverage && npm run build && npm run e2e`; corregir hallazgos
- [x] T049 Seguir `specs/002-ppa-8-recarga-saldo/quickstart.md` de principio a fin con la pila Docker (`docker compose --profile app up --build`) y anotar en el PR el resultado
- [ ] T050 Comentar en Jira PPA-1 (Melanny) que `wallet_service.create_wallet(user_id)` existe para HU-01 y que la FK `wallets.user_id → users.id` va en una migración posterior; comentar en PPA-2 (Moisés) el contrato de `app/common/auth.py` (`g.user_id`); crear tarea de seguimiento "Añadir FK wallets.user_id y escenario E2E de recarga con login"

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias; T001/T003 antes de T002/T004; T005 tras T004
- **Foundational (Phase 2)**: tras Phase 1; T006, T007, T008 en paralelo; T009 tras los tres; T010 antes de T011
- **US1 (Phase 3)**: tras Phase 2; es el MVP
- **US2 (Phase 4)**: tras US1 (extiende servicio y pantalla)
- **US3 (Phase 5)**: tras US1 (necesita el camino exitoso); independiente de US2
- **US4 (Phase 6)**: tras US1; independiente de US2 y US3
- **Polish (Phase 7)**: tras todas

### Within Each User Story

- Tests primero y en rojo; modelos → repositorio → servicio → ruta → contrato → webapp → E2E

### Parallel Opportunities

- Phase 1: T001, T002, T003, T004 en paralelo (archivos distintos)
- Phase 2: T006, T007, T008 en paralelo
- US1: T012, T013, T014 en paralelo; T020, T021, T022 en paralelo con la API
- US2/US3/US4: sus tests `[P]` en paralelo; US3 y US4 pueden avanzar a la vez que US2

---

## Parallel Example: User Story 1

```bash
# Tests de API en paralelo:
Task: "FakeWalletRepository + test_recharge_service.py"   (T012)
Task: "test_openapi_recharges.py"                         (T013)
Task: "test_recharge_flow.py"                             (T014)

# Webapp en paralelo con la API:
Task: "money.test.ts + money/index.ts"                    (T020, T021)
Task: "RechargePage.test.tsx"                             (T022)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2 (cimientos: ~10 tareas)
2. US1 completa (API + pantalla + E2E de navegación)
3. **STOP y validar** con `quickstart.md` §1 a §4
4. PR 1 si el diff supera 400 líneas significativas: cimientos (Phase 1 y 2) en un PR, US1 en otro

### Incremental Delivery

1. US1 → recarga funcional (MVP)
2. US2 → rechazos registrados y mensajes en pantalla
3. US3 → idempotencia y concurrencia
4. US4 → autenticación y titularidad; T045 queda `skip` hasta HU-02

---

## Notes

- Todas las tareas de prueba citan `HU-08 CA-n`, `RNF-x` o `FR-nnn` (constitución II y III)
- `[P]` = archivos distintos, sin dependencias
- Commits: `test(PPA-8): ...` junto con `feat(PPA-8): ...` por grupo lógico; migración en commit propio `feat(PPA-8): add wallets, transactions and idempotency_keys migration`
- Nada se confirma sin revisión del autor (`git-workflow.md`)
