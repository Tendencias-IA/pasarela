---

description: "Tareas de implementación de HU-09 Historial de movimientos (PPA-9)"
---

# Tasks: Historial de movimientos (HU-09)

**Input**: Design documents from `specs/003-ppa-9-historial-movimientos/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/movements.openapi.yaml, quickstart.md

**Tests**: OBLIGATORIAS (constitución, principio III). Cada test se escribe antes de la
implementación que cubre, falla primero, y cita en su nombre o docstring el criterio
(`HU-09 CA-n`, `RNF-x`, `FR-nnn`).

**Organization**: por historia de usuario de `spec.md` (US1 lista ordenada, US2 titularidad y
enmascaramiento, US3 paginación, US4 estado vacío). Las fases 1 y 2 crean lo transversal
(`masking.py`, servicios públicos de `accounts` y `wallet`, TanStack Query, factory de
transacciones) que ninguna historia puede saltarse.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede ejecutarse en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: historia a la que pertenece (US1, US2, US3, US4)
- Rutas exactas en cada tarea; todas relativas a la raíz del repo

## Path Conventions

- API: `api/app/...`, pruebas en `api/app/modules/movements/tests/` y `api/tests/`
- Webapp: `webapp/src/...`, E2E en `webapp/e2e/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: enmascaramiento, factory de transacciones y dependencia de la webapp.

- [x] T001 [P] Test de `app/common/masking.py` en `api/app/common/tests/test_masking.py`: `mask_phone("3001234567") == "***4567"`, `mask_phone("12") == "***"`, `mask_phone("") == "***"`; `mask_name("Maria Garcia") == "Mar** G*****"`, `mask_name("Ana") == "Ana"`, `mask_name("Jose Luis Perez") == "Jos* L*** P****"`, `mask_name("")` y `mask_name(None)` → `"***"` (HU-09 CA-3, RNF-06.1)
- [x] T002 [P] Implementar `api/app/common/masking.py`: `mask_phone(phone: str) -> str` (tres asteriscos + últimos cuatro dígitos; `"***"` si tiene menos de cuatro) y `mask_name(full_name: str | None) -> str` (primera palabra: tres primeras letras y `*` por cada letra restante; palabras siguientes: inicial y `*` por cada letra restante; `"***"` si es `None` o vacío)
- [x] T003 [P] Añadir a `api/tests/factories.py` la función `make_transaction(*, type_: TransactionType, status: TransactionStatus, amount: Decimal, receiver_wallet_id: int, sender_wallet_id: int | None = None, rejection_reason: str | None = None, created_at: datetime | None = None) -> Transaction` que devuelve la fila sin persistir (`created_at` controlado para orden y paginación; si es `None`, `utcnow()` de `app/common/clock.py`)
- [x] T004 Instalar `@tanstack/react-query` con `cd webapp && npm install --save-exact @tanstack/react-query@5` (versión exacta en `webapp/package.json` y `package-lock.json`); verificar que `npm run build` sigue en verde. Commit propio `build(PPA-9): add @tanstack/react-query` (webapp.md, research §7)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: contratos entre módulos y QueryClient; sin esto `movements` no puede resolver la contraparte ni la webapp consultar.

**⚠️ CRITICAL**: ninguna tarea de US1 a US4 empieza hasta cerrar esta fase.

- [x] T005 [P] Test en `api/app/modules/accounts/tests/unit/test_get_users_by_ids.py`: con MySQL (`@pytest.mark.mysql`, `seeded_users`), `accounts_service.get_users_by_ids([1, 2, 99])` devuelve `{1: UserSummary(id=1, phone=..., full_name=None), 2: ...}` sin la clave 99; con lista vacía devuelve `{}` sin consultar (HU-09 CA-3)
- [x] T006 [P] Implementar `get_by_ids(user_ids: Iterable[int]) -> list[User]` en `api/app/modules/accounts/repository.py` (`select(User).where(User.id.in_(ids))`) y `UserSummary(id: int, phone: str, full_name: str | None)` dataclass frozen + `get_users_by_ids(user_ids) -> dict[int, UserSummary]` en `api/app/modules/accounts/service.py`; `full_name=None` hasta que HU-01 añada la columna (research §3, con comentario que lo indique)
- [x] T007 [P] Test en `api/app/modules/wallet/tests/integration/test_wallet_owners.py` (`mysql`): con dos billeteras creadas por `service.create_wallet`, `wallet_service.get_wallet_owners([w1, w2, 999])` devuelve `{w1: WalletOwner(wallet_id=w1, user_id=1, phone=<teléfono de seeded_users[0]>, full_name=None), w2: ...}`; vacío → `{}` (HU-09 CA-3)
- [x] T008 Implementar `get_wallets_by_ids(wallet_ids) -> list[Wallet]` en `api/app/modules/wallet/repository.py` (añadirlo también al Protocol `WalletRepository` y a `FakeWalletRepository` en `api/app/modules/wallet/tests/unit/fakes.py`) y `WalletOwner(wallet_id, user_id, phone, full_name)` + `get_wallet_owners(wallet_ids, repo=default_repository) -> dict[int, WalletOwner]` en `api/app/modules/wallet/service.py`, que importa `from app.modules.accounts import service as accounts_service` (nunca su repositorio ni modelos)
- [x] T009 [P] Crear `webapp/src/app/queryClient.ts` con `new QueryClient({ defaultOptions: { queries: { retry: false, staleTime: 0, refetchOnWindowFocus: false } } })` y envolver `AppRoutes` con `QueryClientProvider` en `webapp/src/app/App.tsx`; añadir en `webapp/src/test/setup.ts` (o un helper `webapp/src/test/render.tsx`) un `wrapper` con un `QueryClient` nuevo por test para `renderHook`/`render`
- [x] T010 [P] Crear `webapp/src/shared/dates/__tests__/dates.test.ts` y `webapp/src/shared/dates/index.ts`: `formatDateTime("2026-10-14T21:40:00Z")` devuelve fecha y hora legibles en `es-CO` (`Intl.DateTimeFormat` con `dateStyle: "medium"`, `timeStyle: "short"`) en la zona horaria del navegador; el test fija `TZ` o compara contra `Intl` con la misma configuración (FR-002)

**Checkpoint**: `pytest api/app/common api/app/modules/accounts api/app/modules/wallet` verde; `npm run test` verde con el provider.

---

## Phase 3: User Story 1 - Ver los movimientos ordenados (Priority: P1) 🎯 MVP

**Goal**: `GET /api/v1/movements` devuelve los movimientos de la billetera del usuario con fecha, monto, tipo/dirección y estado, del más reciente al más antiguo, y la pantalla `/movimientos` los muestra.

**Independent Test**: con tres recargas (una rechazada) del usuario 1 en momentos distintos, la respuesta las lista en orden descendente con `direction: recarga`, `status` correcto y montos como cadena; en la pantalla se ven las tres filas con fecha, monto, tipo y estado.

### Tests for User Story 1

- [x] T011 [P] [US1] Crear `api/app/modules/movements/tests/unit/fakes.py` con `FakeMovementsRepository(rows: list[Transaction-like])` que implementa `list_for_wallet(wallet_id, *, offset, limit)` (filtra sender/receiver, ordena `created_at DESC, id DESC`, aplica offset/limit) y `count_for_wallet(wallet_id)`, más fakes `fake_wallet_id(user_id)` y `fake_wallet_owners(ids)` inyectables; y `api/app/modules/movements/tests/unit/test_list_movements_service.py` con: recarga exitosa y rechazada se listan con `direction=recarga`, `status` y `rejection_reason` (HU-09 CA-1, CA-2); orden descendente y desempate por `id` con dos filas del mismo `created_at` (HU-09 CA-4, FR-005); transferencia con `sender == billetera` → `enviada`, con `receiver == billetera` → `recibida` (HU-09 CA-1, FR-003); `amount` sigue siendo `Decimal` en el dominio (RNF-04.3)
- [x] T012 [P] [US1] Test de contrato en `api/tests/contract/test_openapi_movements.py` (`mysql`): la respuesta `200` de `GET /api/v1/movements` tras una recarga valida contra el schema `MovementsPageOut` de `api/openapi.yaml` con `jsonschema` (como `test_openapi_recharges.py`); incluye un caso con `items: []` (FR-007)
- [x] T013 [P] [US1] Test e2e por HTTP en `api/tests/e2e_api/test_movements_flow.py` (`mysql`): con `logged_in_client`, dos recargas válidas y una de `"4999.00"` → `GET /api/v1/movements` responde `200`, `total == 3`, `items[0]` es la última recarga, `items[2].status == "rechazada"` con `rejection_reason == "amount_out_of_range"`, montos como cadena `^\d+\.\d{2}$`, `created_at` termina en `Z` (HU-09 CA-1, CA-2, CA-4; SC-007); y `test_real_login_cookie_lists_movements` con login real por `/api/v1/auth/login` (HU-02 CA-5)

### Implementation for User Story 1

- [x] T014 [US1] Crear `api/app/modules/movements/__init__.py` y `api/app/modules/movements/repository.py`: Protocol `MovementsRepository` con `list_for_wallet(wallet_id: int, *, offset: int, limit: int) -> list[Transaction]` y `count_for_wallet(wallet_id: int) -> int`; `SqlMovementsRepository` que consulta solo `app.common.models.transaction.Transaction` con `or_(Transaction.receiver_wallet_id == w, Transaction.sender_wallet_id == w)`, `order_by(Transaction.created_at.desc(), Transaction.id.desc())`, `offset/limit`, y `count` con `select(func.count())` sobre la misma condición; `default_repository`
- [x] T015 [US1] Crear `api/app/modules/movements/service.py`: `PAGE_SIZE = 20`; `Direction(StrEnum) {recarga, enviada, recibida}`; dataclasses frozen `Counterparty(name_masked: str | None, phone_masked: str)`, `Movement(id, direction, type, status, amount: Decimal, created_at: datetime, rejection_reason: str | None, counterparty: Counterparty | None)`, `MovementsPage(items, page, page_size, total)`; `list_movements(user_id: int, page: int, *, repo=default_repository, wallet_id_for=wallet_service.get_wallet_id, owners_for=wallet_service.get_wallet_owners) -> MovementsPage`: billetera `None` → página vacía con `total 0` y `log.warning("movements.wallet_missing")`; `offset = (page - 1) * PAGE_SIZE`; deriva `direction`; reúne los `wallet_id` ajenos de las transferencias de la página, llama a `owners_for` una sola vez y construye `Counterparty` con `mask_name`/`mask_phone`; `log.info("movements.listed", extra={"user_id", "page", "total"})` (sin datos de terceros, FR-012)
- [x] T016 [US1] Crear `api/app/modules/movements/schemas.py`: `MovementsQuery` (Pydantic, `extra="ignore"`: `from`, `to`, `type` de HU-10 se ignoran hoy) con `page: int = 1`, validador `ge=1`, método `parse(args: Mapping[str, str]) -> MovementsQuery` que convierte errores a `ValidationError` con `errors=[{"field": "page", "message": "La página debe ser un entero desde 1."}]`; `CounterpartyOut`, `MovementOut` (`amount` y `created_at` como cadena, `created_at` con sufijo `Z` como `RechargeOut`) y `MovementsPageOut.from_page(page: MovementsPage)`
- [x] T017 [US1] Crear `api/app/modules/movements/routes.py`: `bp = Blueprint("movements", __name__)`, `@bp.get("")` con `@login_required`, `query = MovementsQuery.parse(request.args)`, `service.list_movements(current_user_id(), query.page)`, `jsonify(MovementsPageOut.from_page(result).model_dump()), 200`; registrar en `api/app/__init__.py` con `url_prefix="/api/v1/movements"` (verificar que `GET /api/v1/movements` y `/api/v1/movements/` no den 308 confuso: usar `strict_slashes=False`)
- [x] T018 [US1] Fusionar `specs/003-ppa-9-historial-movimientos/contracts/movements.openapi.yaml` en `api/openapi.yaml` (path `/api/v1/movements` tras `/api/v1/wallet/recharges`; schemas `Counterparty`, `MovementOut`, `MovementsPageOut` tras `RechargeOut`) y regenerar `webapp/src/shared/api/types.gen.ts` con `cd webapp && npm run api:types`
- [x] T019 [P] [US1] Test de `useMovements` en `webapp/src/features/movements/__tests__/useMovements.test.ts` con MSW (`src/test/server.ts`): página 1 con dos ítems expone `data.items`, `data.total`; la petición es `GET /api/v1/movements?page=1` sin `X-Requested-With`; `401 invalid_session` invoca el manejador de sesión expirada (HU-04 CA-2); error de red → `isError` (HU-09 CA-1, CA-2)
- [x] T020 [P] [US1] Test de `MovementsPage` en `webapp/src/features/movements/__tests__/MovementsPage.test.tsx` con MSW: renderiza una fila por ítem con fecha formateada, `formatCOP(amount)`, etiqueta de tipo ("Recarga", "Transferencia enviada", "Transferencia recibida") y estado ("Exitosa"/"Rechazada", con `data-status`), encabezado `h1` "Movimientos", y `role="status"` "Cargando…" mientras carga (HU-09 CA-2, FR-002)
- [x] T021 [US1] Crear `webapp/src/features/movements/api.ts` (`getMovements(page: number, signal?) -> Promise<MovementsPageOut>` con `request<...>(\`/api/v1/movements?page=${page}\`)`, tipos desde `types.gen.ts`) y `webapp/src/features/movements/useMovements.ts` (`useQuery({ queryKey: ["movements", page], queryFn, placeholderData: keepPreviousData })`, exporta `MOVEMENTS_QUERY_KEY = ["movements"]`)
- [x] T022 [US1] Crear `webapp/src/features/movements/MovementItem.tsx` (`IonItem` con `IonLabel`: línea 1 tipo/dirección + contraparte si existe, línea 2 fecha con `formatDateTime`; `slot="end"` monto con `formatCOP` y `IonBadge` de estado con color `success`/`danger`; `aria-label` completo de la fila) y `webapp/src/features/movements/MovementsPage.tsx` (`IonPage` con `IonHeader` + `IonMenuButton`, `h1.tai-title` "Movimientos", `IonList` de `MovementItem`, estados `isPending` → `role="status"` "Cargando…", `isError` → `role="alert"` con mensaje y botón "Reintentar")
- [x] T023 [US1] Reemplazar en `webapp/src/app/routes.tsx` la ruta `/movimientos` (`ComingSoonPage`) por `<MovementsPage />`; mantener `ComingSoonPage` para `/transferir` y `/perfil`
- [x] T024 [US1] Invalidar la query de movimientos tras una recarga exitosa: en `webapp/src/features/wallet/useRecharge.ts` usar `useQueryClient()` y `queryClient.invalidateQueries({ queryKey: MOVEMENTS_QUERY_KEY })` al recibir `201`; actualizar `webapp/src/features/wallet/__tests__/useRecharge.test.ts` y `RechargePage.test.tsx` para usar el wrapper con `QueryClientProvider` y comprobar la invalidación (webapp.md, SC-007)
- [x] T025 [US1] Crear `webapp/e2e/pages/movements.page.ts` (`goto()`, `heading()`, `rows()`, `emptyState()`, `nextButton()`, `prevButton()`, `pageIndicator()`) y `webapp/e2e/hu-09-historial-movimientos.spec.ts` con login real (`LoginPage.signIn("3009876543", "Clave1234")`): "desde el panel se llega a Movimientos en un clic" (RNF-03.1, FR-013); "CA-1, CA-2, CA-4: una recarga hecha en /recargar aparece de primera en /movimientos con monto, tipo Recarga y estado Exitosa" (SC-007); axe sin violaciones `serious`/`critical` (SC-006)

**Checkpoint**: `quickstart.md` §1 a §4 en verde para la lista básica; la pantalla muestra recargas reales.

---

## Phase 4: User Story 2 - Titularidad y contraparte enmascarada (Priority: P1)

**Goal**: solo se devuelven movimientos de la billetera del usuario de la sesión; en transferencias la contraparte llega enmascarada desde el servidor; sin sesión, `401`.

**Independent Test**: con dos usuarios A y B y transferencias sembradas A→B y B→A más recargas propias de cada uno, A no ve las recargas de B, ve A→B como `enviada` y B→A como `recibida`, y la contraparte es `{name_masked: null, phone_masked: "***" + últimos 4 del teléfono de B}`; ninguna respuesta contiene el teléfono completo de B.

### Tests for User Story 2

- [x] T026 [P] [US2] Test de integración en `api/app/modules/movements/tests/integration/test_movements_db.py` (`mysql`, `seeded_users`, billeteras por `wallet_service.create_wallet(1)` y `(2)`): sembrar con `make_transaction` dos recargas de A, una de B, transferencia exitosa A→B, transferencia rechazada A→B (`rejection_reason="insufficient_balance"`), transferencia exitosa B→A; `list_movements(1, 1)` devuelve 5 ítems (sin la recarga de B), direcciones `enviada`/`recibida` correctas, la rechazada solo aparece para A; `list_movements(2, 1)` devuelve 3 (su recarga, la recibida y la enviada), sin la rechazada (HU-09 CA-1, CA-5, FR-003, FR-006; RNF-06.1)
- [x] T027 [P] [US2] En el mismo archivo: `counterparty` de cada transferencia tiene `phone_masked == "***" + phone[-4:]` del otro usuario y `name_masked is None`; serializando con `MovementsPageOut`, el JSON completo no contiene el teléfono completo de ningún `seeded_user` (`assert phone not in json.dumps(body)`) (HU-09 CA-3, FR-004, SC-002)
- [x] T028 [P] [US2] Añadir a `api/tests/e2e_api/test_movements_flow.py`: sin sesión → `401` problem `invalid_session` (RNF-01.1, HU-02 CA-5); con sesión, `GET /api/v1/movements?user_id=2&wallet_id=2` ignora esos parámetros y responde los movimientos del usuario 1 (HU-09 CA-5, RNF-01.4)
- [x] T029 [P] [US2] Test unitario adicional en `test_list_movements_service.py`: `owners_for` se invoca una sola vez por página con el conjunto de billeteras ajenas (sin la propia, sin duplicados) y no se invoca si la página solo tiene recargas (eficiencia, research §1); contraparte ausente en `owners_for` (dato inconsistente) → `Counterparty(name_masked=None, phone_masked="***")` sin fallar (edge case)
- [x] T030 [P] [US2] Test en `MovementsPage.test.tsx`: una transferencia enviada muestra "a ***4567" y una recibida "de ***4567"; si `name_masked` no es `null`, se antepone ("a Mar** G**** · ***4567"); nunca aparece un teléfono de 10 dígitos en el DOM (HU-09 CA-3)

### Implementation for User Story 2

- [x] T031 [US2] Ajustar `api/app/modules/movements/service.py` según T029: contraparte faltante → `"***"`; una sola llamada a `owners_for`; comentario que cite RNF-06.1
- [x] T032 [US2] Ajustar `MovementItem.tsx` según T030 (texto "a"/"de" + contraparte; helper `counterpartyLabel(c)` en el mismo archivo o en `webapp/src/features/movements/labels.ts` junto con `directionLabel` y `statusLabel`)
- [x] T033 [US2] Añadir al spec Playwright `hu-09-historial-movimientos.spec.ts`: "sin sesión, /movimientos redirige a /login" (HU-04 CA-2, RNF-01.1) y, con el usuario sembrado, "ningún texto de la lista contiene un teléfono de 10 dígitos" (SC-002)

**Checkpoint**: `quickstart.md` §2 verde; ninguna respuesta expone datos de terceros.

---

## Phase 5: User Story 3 - Paginación de 20 (Priority: P2)

**Goal**: páginas de 20 numeradas desde 1, con `total`; página fuera de rango vacía; `page` inválida `422`; la pantalla permite avanzar y retroceder con los controles deshabilitados en los extremos.

**Independent Test**: con 45 movimientos sembrados, las páginas 1, 2 y 3 devuelven 20, 20 y 5 ítems, 45 ids distintos en orden descendente; `page=9` → `items: []`, `total: 45`; `page=0` y `page=abc` → `422`; en la pantalla, "página 1 de 3", "Anterior" deshabilitado en la 1 y "Siguiente" en la 3.

### Tests for User Story 3

- [x] T034 [P] [US3] Test unitario en `test_list_movements_service.py`: con 45 filas en el fake, `page=1` → 20 ítems y `total=45`, `page=3` → 5, `page=9` → `[]` y `total=45`; `page_size` siempre 20; offset correcto (HU-09 CA-6, FR-007, FR-009)
- [x] T035 [P] [US3] Test de integración en `test_movements_db.py`: 45 movimientos del usuario 1 con `created_at` espaciados un segundo y tres del mismo segundo (desempate por `id`); las tres páginas suman 45 ids distintos, estrictamente descendentes por `(created_at, id)`; `count_for_wallet == 45` (HU-09 CA-4, CA-6, SC-003)
- [x] T036 [P] [US3] Test en `api/tests/e2e_api/test_movements_flow.py`: `?page=0`, `?page=-1`, `?page=abc`, `?page=1.5` → `422 validation` con `errors[0].field == "page"`; sin `page` → página 1; `?page=9` con pocos movimientos → `200`, `items == []` (FR-009)
- [x] T037 [P] [US3] Test de schema en `api/app/modules/movements/tests/unit/test_schemas.py`: `MovementsQuery.parse({})` → `page=1`; `{"page": "3"}` → 3; `{"page": "0"}` lanza `ValidationError` con el mensaje "La página debe ser un entero desde 1."; `{"page": "2", "type": "sent"}` ignora `type` (HU-10 llegará después)
- [x] T038 [P] [US3] Test de `useMovements` para paginación: al cambiar `page` de 1 a 2, `data` conserva la página 1 (`isPlaceholderData`) hasta que llega la 2; con `page=9` y `total=45`, el hook expone `lastPage=3` y `isOutOfRange=true` (FR-009)
- [x] T039 [P] [US3] Test de `Pagination` y `MovementsPage` en `webapp/src/features/movements/__tests__/Pagination.test.tsx`: con `page=1,total=45` muestra "Página 1 de 3", "Anterior" deshabilitado y "Siguiente" habilitado; `page=3` al revés; `total=20` → una página sin controles habilitados; clic en "Siguiente" llama `onPageChange(2)`; navegación por teclado (HU-09 CA-6, RNF-03.6)

### Implementation for User Story 3

- [x] T040 [US3] Completar `MovementsQuery` en `schemas.py` y la aritmética de paginación en `service.py` según T034, T036 y T037 (la validación vive en el schema, la aritmética en el servicio, nunca en la ruta)
- [x] T041 [US3] Crear `webapp/src/features/movements/Pagination.tsx` (`nav aria-label="Paginación"`, dos `IonButton` `fill="outline"` "Anterior"/"Siguiente" con `disabled`, texto `Página {page} de {lastPage}` en `aria-live="polite"`) y completar `useMovements.ts` con `lastPage = Math.max(1, Math.ceil(total / page_size))`, `isOutOfRange`
- [x] T042 [US3] En `MovementsPage.tsx`: estado `page` en la URL (`useSearchParams`, `?page=N`, por defecto 1) para que "atrás" del navegador funcione; si `isOutOfRange`, reemplazar la URL por `?page={lastPage}`; `IonContent` hace `scrollToTop` al cambiar de página
- [x] T043 [US3] Añadir al spec Playwright: "los controles de paginación están presentes y 'Anterior' está deshabilitado en la primera página" (con el usuario sembrado; la paginación con 45 filas se cubre en integración, quickstart §4)

**Checkpoint**: `quickstart.md` §2 con 45 filas verde; la pantalla pagina.

---

## Phase 6: User Story 4 - Estado vacío (Priority: P2)

**Goal**: un usuario sin movimientos ve un mensaje informativo con acceso a recargar, sin lista ni paginación.

**Independent Test**: con el segundo usuario sembrado (`3009876544`, sin movimientos), `/movimientos` muestra "Aún no tienes movimientos" y un enlace "Recargar saldo" que lleva a `/recargar`.

### Tests for User Story 4

- [x] T044 [P] [US4] Test en `MovementsPage.test.tsx`: con `{items: [], total: 0}` se muestra `role="status"` "Aún no tienes movimientos", un enlace "Recargar saldo" con `href="/recargar"`, ninguna fila y ningún control de paginación (HU-09 CA-7, FR-010)
- [x] T045 [P] [US4] Test en `test_list_movements_service.py` y `test_movements_db.py`: usuario con billetera y sin movimientos → `items == []`, `total == 0`; usuario sin billetera → igual, y se emite `movements.wallet_missing` en `WARNING` (`caplog`) sin crear billetera (HU-09 CA-7, edge case)

### Implementation for User Story 4

- [x] T046 [US4] Crear `webapp/src/features/movements/EmptyState.tsx` (texto, `IonButton routerLink="/recargar"` "Recargar saldo", icono `walletOutline` decorativo) y usarlo en `MovementsPage.tsx` cuando `total === 0`
- [x] T047 [US4] Ampliar `api/scripts/seed_test_user.py` para crear también el usuario `3009876544` / `Clave1234` con billetera y sin movimientos (idempotente, misma estructura que el primero) y documentarlo en el docstring; actualizar `.github/workflows/ci.yml` solo si el job E2E necesita un paso nuevo (no debería: ya ejecuta el seed)
- [x] T048 [US4] Añadir al spec Playwright: con `LoginPage.signIn("3009876544", "Clave1234")`, `/movimientos` muestra el estado vacío y el enlace lleva a `/recargar` (HU-09 CA-7); axe sobre el estado vacío (SC-006)

**Checkpoint**: `npm run e2e` verde en los dos proyectos.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [x] T049 [P] Añadir a `api/tests/load/locustfile.py` la tarea `movements` (`@task(1)`): `GET /api/v1/movements?page=1` con la cookie obtenida en `on_start` por `POST /api/v1/auth/login` (usuario sembrado); verificar `p95 ≤ 3000 ms` en el reporte nocturno (HU-09 CA-8, RNF-02.2)
- [x] T050 [P] Verificar `ruff format . && ruff check . && mypy app && pytest` en `api/` con cobertura ≥ 90 % y `movements/` al 100 %; `npm run lint && npm run typecheck && npm run test -- --coverage && npm run build` en `webapp/`
- [x] T051 [P] Revisar `.claude/rules/architecture.md` y `api-design.md`: si el patrón "servicio público para resolver titulares de billeteras" merece una línea, añadirla en un PR aparte de reglas (git-workflow.md); en este PR solo código y specs. Resultado: no hace falta; `architecture.md` ya dice que un módulo expone funciones de `service.py` a los demás
- [x] T052 Ejecutar `quickstart.md` completo (§1 a §5) con Docker: login real, recarga, historial por curl, Playwright; registrar en el PR qué tests fallaron antes y pasan después (testing.md, "Definición de probado")
- [ ] T053 Avisar en el PR a Melanny (HU-01: llenar `full_name` en `accounts_service.get_users_by_ids`), Moisés (HU-05: reutilizar `QueryClientProvider` y la clave `["wallet"]`) y a quien tome HU-07 (invalidar `["movements"]` al confirmar)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias; T001–T003 en paralelo; T004 es un commit `build` aparte
- **Foundational (Phase 2)**: depende de Phase 1 (T003 para sembrar; T004 para T009); bloquea todas las historias
- **US1 (Phase 3)**: depende de Phase 2; es el MVP
- **US2 (Phase 4)**: depende de US1 (reutiliza servicio, ruta y pantalla); añade titularidad y contraparte
- **US3 (Phase 5)**: depende de US1; independiente de US2
- **US4 (Phase 6)**: depende de US1; independiente de US2 y US3
- **Polish (Phase 7)**: depende de todas

### Within Each User Story

- Tests antes que la implementación, y deben fallar primero
- API: repositorio → servicio → schemas → ruta → contrato OpenAPI → tipos de la webapp
- Webapp: api.ts → hook → componentes → página → ruta → E2E

### Parallel Opportunities

- Phase 1: T001+T002, T003, T004 (cuatro frentes)
- Phase 2: T005+T006 (accounts) ∥ T007+T008 (wallet) ∥ T009 ∥ T010
- US1: T011, T012, T013 (tests de API) ∥ T019, T020 (tests de webapp)
- US2: T026, T027, T028, T029 ∥ T030
- US3: T034–T037 ∥ T038, T039
- US4: T044 ∥ T045

---

## Parallel Example: User Story 1

```bash
# Tests de API en paralelo:
Task: "fakes.py + test_list_movements_service.py"   (T011)
Task: "test_openapi_movements.py"                   (T012)
Task: "test_movements_flow.py"                      (T013)

# Webapp en paralelo con la API:
Task: "useMovements.test.ts"                        (T019)
Task: "MovementsPage.test.tsx"                      (T020)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2 (cimientos: 10 tareas, dos de ellas un commit `build`)
2. US1 completa (API + pantalla + E2E con recarga real)
3. **STOP y validar** con `quickstart.md` §1 a §4
4. Si el diff supera 400 líneas significativas, se divide: cimientos + US1 en un PR, US2–US4 en otro (git-workflow.md)

### Incremental Delivery

1. US1 → historial funcional con recargas (MVP)
2. US2 → titularidad verificada con dos usuarios y contraparte enmascarada
3. US3 → paginación con 45 filas
4. US4 → estado vacío con segundo usuario sembrado

---

## Notes

- Todas las tareas de prueba citan `HU-09 CA-n`, `RNF-x`, `FR-nnn` o `SC-nnn` (constitución II y III)
- `[P]` = archivos distintos, sin dependencias
- Commits: `build(PPA-9): add @tanstack/react-query` primero; luego `feat(PPA-9): ...` por grupo lógico con sus tests
- Nada se confirma sin revisión del autor (`git-workflow.md`)
