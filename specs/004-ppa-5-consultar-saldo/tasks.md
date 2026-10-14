---

description: "Tareas de implementación de HU-05 Consultar el saldo (PPA-5)"
---

# Tasks: Consultar el saldo (HU-05)

**Input**: Design documents from `specs/004-ppa-5-consultar-saldo/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/wallet.openapi.yaml, quickstart.md

**Tests**: OBLIGATORIAS (constitución, principio III). Cada test se escribe antes de la
implementación que cubre, falla primero, y cita en su nombre o docstring el criterio
(`HU-05 CA-n`, `RNF-x`, `FR-nnn`).

**Organization**: por historia de usuario de `spec.md` (US1 saldo propio por API, US2
billetera ausente, US3 tarjeta en la pantalla principal). No hay fase de setup: no hay
dependencias ni infraestructura nueva.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede ejecutarse en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: historia a la que pertenece (US1, US2, US3)
- Rutas exactas en cada tarea; todas relativas a la raíz del repo

---

## Phase 1: User Story 1 - Consultar el saldo propio (Priority: P1) 🎯 MVP

**Goal**: `GET /api/v1/wallet` devuelve `{"balance": "<decimal>"}` de la billetera del usuario de la sesión; ignora parámetros; `401` sin sesión.

**Independent Test**: con login real, saldo `0.00`; tras una recarga de `5000.00`, `5000.00`; `?user_id=2` ignorado; sin cookie `401 invalid_session`.

### Tests for User Story 1

- [x] T001 [P] [US1] Unitarias en `api/app/modules/wallet/tests/unit/test_balance_service.py` (tomadas del borrador y adaptadas a `get_balance -> WalletBalance`): devuelve exactamente `Decimal("123456.70")` persistido (HU-05 CA-1, CA-2; RNF-04.3); no bloquea la billetera (`repo.locked == []`) ni escribe (`repo.transactions == []`) (FR-008); con dos billeteras devuelve la del `user_id` pedido (HU-05 CA-4)
- [x] T002 [P] [US1] e2e por HTTP en `api/tests/e2e_api/test_balance_flow.py` (`mysql`; tomado del borrador con el código `invalid_session`): login real → `{"balance": "0.00"}` → recarga `5000.00` → `{"balance": "5000.00"}` y coincide con la fila (HU-05 CA-1, CA-2, CA-3); `?user_id=2` responde el saldo del usuario 1 y el 2 sigue en `0.00` (HU-05 CA-4, RNF-01.4); sin sesión `401 invalid_session` (RNF-01.1)
- [x] T003 [P] [US1] Contrato en `api/tests/contract/test_openapi_wallet.py` (`mysql`, patrón `test_openapi_movements.py`): la respuesta `200` valida contra `WalletOut`; el path `/api/v1/wallet` declara `get` con `200`, `401` y `404` (FR-002)

### Implementation for User Story 1

- [x] T004 [US1] `api/app/modules/wallet/service.py`: `get_balance(user_id: int, repo: WalletRepository = default_repository) -> WalletBalance` con `repo.get_wallet_by_user` (sin `transaction()`, sin `lock_*`); `WalletNotFoundError` si no hay billetera (el log va en T008)
- [x] T005 [US1] `api/app/modules/wallet/schemas.py`: `WalletOut(balance: str)` con `from_balance(cls, result: WalletBalance)` que usa `to_json`; `api/app/modules/wallet/routes.py`: `@bp.get("", strict_slashes=False)` + `@login_required` → `jsonify(WalletOut.from_balance(service.get_balance(current_user_id())).model_dump()), 200`
- [x] T006 [US1] Fusionar `specs/004-ppa-5-consultar-saldo/contracts/wallet.openapi.yaml` en `api/openapi.yaml` (path antes de `/api/v1/wallet/recharges`; schema `WalletOut` tras `Money`) y regenerar `webapp/src/shared/api/types.gen.ts` con `cd webapp && npm run api:types`

**Checkpoint**: `pytest app/modules/wallet tests/e2e_api/test_balance_flow.py tests/contract/test_openapi_wallet.py` verde.

---

## Phase 2: User Story 2 - Informar una billetera ausente (Priority: P2)

**Goal**: sin billetera, `404 wallet_not_found`, ninguna escritura y `WARNING wallet.missing` con `user_id`.

**Independent Test**: usuario 1 sembrado sin `create_wallet` → `404`, `code == "wallet_not_found"`, cero filas en `wallets`, y `caplog` contiene `wallet.missing`.

### Tests for User Story 2

- [x] T007 [P] [US2] En `test_balance_service.py`: sin billetera lanza `WalletNotFoundError` con `code == "wallet_not_found"`, no crea billetera (`repo.wallets` sin cambios) y emite `wallet.missing` en `WARNING` con `extra user_id` (`caplog`) (HU-05 CA-5, FR-005); en `test_balance_flow.py`: `404` y `wallets` sigue vacía (HU-05 CA-5)

### Implementation for User Story 2

- [x] T008 [US2] En `get_balance`: `log.warning("wallet.missing", extra={"user_id": user_id})` antes de lanzar `WalletNotFoundError("El usuario no tiene una billetera asociada.")` (observability.md: evento con nombre fijo, sin datos personales)

**Checkpoint**: unitarias de `wallet/` al 100 %.

---

## Phase 3: User Story 3 - Saldo en la pantalla principal (Priority: P1)

**Goal**: `HomePage` muestra la tarjeta "Saldo disponible" con `formatCOP(balance)`, estados de carga, no disponible y error; la recarga invalida la query.

**Independent Test**: con MSW devolviendo `{"balance": "150000.00"}`, la pantalla muestra `$ 150.000,00`; con `404 wallet_not_found`, "Saldo no disponible"; tras `useRecharge.submit()` exitoso se vuelve a pedir `/api/v1/wallet`.

### Tests for User Story 3

- [x] T009 [P] [US3] `webapp/src/features/wallet/__tests__/useWallet.test.ts` con MSW y `renderHookWithProviders`: `GET /api/v1/wallet` sin `X-Requested-With` expone `data.balance === "150000.00"` (HU-05 CA-1, CA-2); `404 wallet_not_found` → `isError` y `error.code === "wallet_not_found"` (HU-05 CA-5); `401 invalid_session` invoca el manejador de sesión expirada (HU-04 CA-2); error de red → `isError` y `refetch()` recupera (edge case)
- [x] T010 [P] [US3] `webapp/src/app/__tests__/HomePage.test.tsx` con `renderWithProviders`: encabezado `h2` "Saldo disponible"; `role="status"` "Consultando saldo…" mientras carga; luego `$ 150.000,00`; con `404` muestra `role="alert"` "Saldo no disponible" y ningún `$`; con `504` muestra "No se pudo consultar el saldo"; conserva "Recargar saldo" y "Ver movimientos" (HU-05 CA-1, CA-2, CA-5; FR-007; RNF-03.4)
- [x] T011 [P] [US3] En `webapp/src/features/wallet/__tests__/useRecharge.test.ts`: tras un `201`, la query `["wallet"]` se invalida (segunda petición a `/api/v1/wallet`, patrón del test de movimientos) (HU-05 CA-3; webapp.md)
- [x] T012 [P] [US3] Añadir en `webapp/src/test/server.ts` el handler por defecto `GET /api/v1/wallet → {"balance": "0.00"}` para que `App.test.tsx` y otros renders de `HomePage` no fallen por petición no manejada

### Implementation for User Story 3

- [x] T013 [US3] `webapp/src/features/wallet/api.ts`: `export type WalletOut = components["schemas"]["WalletOut"]` y `getWallet(signal?) => request<WalletOut>("/api/v1/wallet", { signal })`; `webapp/src/features/wallet/useWallet.ts`: `export const WALLET_QUERY_KEY = ["wallet"] as const` y `useWallet()` con `useQuery({ queryKey: WALLET_QUERY_KEY, queryFn: ({ signal }) => getWallet(signal) })`
- [x] T014 [US3] `webapp/src/app/HomePage.tsx`: tarjeta `section.tai-card` `aria-labelledby="saldo-title"` con `h2#saldo-title` "Saldo disponible"; `isPending` → `<p role="status">Consultando saldo…</p>`; éxito → `<p>{formatCOP(balance)}</p>`; `ApiError` con `code === "wallet_not_found"` → `<p role="alert">Saldo no disponible</p>`; otro error → `role="alert"` "No se pudo consultar el saldo". Mantener la tarjeta de estado de la API y los botones existentes
- [x] T015 [US3] `webapp/src/features/wallet/useRecharge.ts`: tras `201`, `invalidateQueries({ queryKey: WALLET_QUERY_KEY })` además de `MOVEMENTS_QUERY_KEY`
- [x] T016 [US3] Playwright: `webapp/e2e/hu-05-consultar-saldo.spec.ts` con `LoginPage.signIn("3009876543", "Clave1234")`: "CA-1, CA-2: el panel muestra la tarjeta Saldo disponible con un monto en COP" + axe (SC-006); "CA-3: tras recargar 20.000 en /recargar el panel muestra el saldo anterior + $ 20.000,00" (el texto de la tarjeta cambia); "RNF-01.1: sin sesión, / redirige a /login". Actualizar `webapp/e2e/smoke.spec.ts` para iniciar sesión antes de abrir `/` y localizar el estado de la API por texto

**Checkpoint**: `npm run lint && npm run typecheck && npm run test -- --coverage && npm run build` verde; el spec Playwright queda listo (lo ejecuta el orquestador, puertos compartidos).

---

## Phase 4: Polish & Cross-Cutting Concerns

- [x] T017 [P] `api/tests/load/locustfile.py`: `@task(2) def wallet(self)` → `GET /api/v1/wallet` con `name="GET /api/v1/wallet"`; docstring "HU-05 CA-6, RNF-02.1: p95 <= 2 s con 20 usuarios"
- [x] T018 [P] Verificar `ruff format . && ruff check . && mypy app && pytest` en `api/` (cobertura ≥ 90 %) y `npm run lint && npm run typecheck && npm run test -- --coverage && npm run build` en `webapp/`
- [x] T019 Marcar tareas, registrar en el informe final qué tests fallaron antes y pasan después, y listar los archivos compartidos tocados para el orquestador

---

## Dependencies & Execution Order

- **US1**: tests T001–T003 primero (fallan por `AttributeError`/`404`), luego T004 → T005 → T006
- **US2**: T007 tras T004 (falla por el log ausente), luego T008
- **US3**: depende de T006 (tipos generados); T009–T012 primero, luego T013 → T014 → T015 → T016
- **Polish**: al final

### Parallel Opportunities

- T001 ∥ T002 ∥ T003; T009 ∥ T010 ∥ T011 ∥ T012; T017 ∥ T018

---

## Implementation Strategy

1. US1 (API) → commit `feat(PPA-5): add wallet balance endpoint` con la carpeta `specs/004-…`
2. US2 → mismo commit que US1 si es pequeño (solo el log), o `feat(PPA-5): log missing wallet`
3. US3 (webapp + Playwright + smoke) → commit `feat(PPA-5): show wallet balance on home`
4. Polish → `test(PPA-5): add wallet balance load task`

## Notes

- Todas las tareas de prueba citan `HU-05 CA-n`, `RNF-x`, `FR-nnn` o `SC-nnn` (constitución II y III)
- Del borrador de moagu se toman `test_balance_service.py` y `test_balance_flow.py` (ajustados); no se toma el renombre `invalid_session → unauthenticated` ni el cambio de `seed_test_user.py`
