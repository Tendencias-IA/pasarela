# Tasks: Consultar el saldo (HU-05)

**Input**: Design documents from `/specs/001-ppa-5-consultar-el-saldo/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/wallet.yaml`

**Tests**: Obligatorios por la constitución y `.claude/rules/testing.md`. Deben escribirse
y fallar antes de la implementación que cubren.

## Phase 1: Setup and contract alignment

**Purpose**: Fijar el contrato común de sesión y preparar los tipos generados antes de
conectar la pantalla de saldo.

- [ ] T001 [P] Actualizar `api/app/common/tests/test_auth.py` y `api/app/modules/auth/tests/integration/test_routes.py` para que una ruta privada sin sesión espere `401 unauthenticated`, conforme a `.claude/rules/api-design.md` y RNF-01.1.
- [ ] T002 [P] Actualizar `webapp/src/shared/api/__tests__/client.test.ts` para esperar que el manejador de sesión redirija ante `401 unauthenticated` y conserve el `ApiError` recibido.
- [ ] T003 Implementar la normalización de sesión inválida en `api/app/modules/auth/service.py`, `api/app/common/auth.py`, `webapp/src/shared/api/client.ts` y sus pruebas de T001-T002; no introducir un tercer código de error y actualizar los tests de HU-08 afectados.
- [ ] T004 Ampliar `api/openapi.yaml` con `GET /api/v1/wallet`, `BalanceOut` y el `401 unauthenticated` consistente con `contracts/wallet.yaml`; ejecutar `npm run api:types` desde `webapp/` para regenerar `webapp/src/shared/api/types.gen.ts`.

**Checkpoint**: Las rutas privadas y el cliente usan un único código de sesión inválida;
el contrato de saldo existe y los tipos generados están actualizados.

---

## Phase 2: User Story 1 - Consultar el saldo propio (Priority: P1) 🎯 MVP

**Goal**: Un usuario con sesión válida consulta exclusivamente el saldo persistido de su
billetera y ve el importe en COP desde la pantalla principal.

**Independent Test**: Crear una billetera de prueba con saldo conocido, autenticar su
titular y ejecutar `GET /api/v1/wallet`; la respuesta es `200` con la cadena decimal
exacta. Tras una recarga exitosa, una segunda consulta devuelve el nuevo saldo.

### Tests for User Story 1 (write first; must fail)

- [ ] T005 [P] [US1] Crear `api/app/modules/wallet/tests/unit/test_balance_service.py` con pruebas de `get_balance`: devuelve `Decimal` exacto de la billetera del `user_id` solicitado y lanza `WalletNotFoundError` si no existe (HU-05 CA-1, CA-2, CA-5; RNF-04.3), reutilizando `FakeWalletRepository` de `api/app/modules/wallet/tests/unit/fakes.py`.
- [ ] T006 [P] [US1] Crear o ampliar `api/tests/contract/test_wallet_contract.py` para validar contra `api/openapi.yaml` la respuesta `200` (`balance` como cadena con dos decimales), `401 unauthenticated` y `404 wallet_not_found` de `GET /api/v1/wallet` (HU-05 CA-1, CA-2, CA-5).
- [ ] T007 [P] [US1] Crear `api/tests/e2e_api/test_balance_flow.py`, con marcador `mysql`, que use una cookie real de HU-02: consulta la billetera del usuario 1, rechaza una solicitud con un campo/identificador de otro usuario sin exponer su saldo y, tras `POST /api/v1/wallet/recharges` exitoso, comprueba que `GET /api/v1/wallet` devuelve el saldo actualizado (HU-05 CA-1 a CA-4; RNF-01.4; RNF-05.1).
- [ ] T008 [P] [US1] Crear `webapp/src/features/wallet/__tests__/BalancePage.test.tsx` con MSW: estado de carga accesible, saldo `"50000.00"` mostrado como COP, `404 wallet_not_found` mostrado sin inventar saldo y `401 unauthenticated` redirigiendo a `/login` (HU-05 CA-1, CA-2, CA-5; RNF-03.2/.4).
- [ ] T009 [P] [US1] Ampliar `webapp/src/features/auth/__tests__/useLogin.test.ts` o añadir una prueba de `LoginPage` que verifique navegación a `/` después del `204` de inicio de sesión, sin guardar sesión o saldo en almacenamiento del navegador (HU-02 CA-1, HU-05 RF-03).

### Implementation for User Story 1

- [ ] T010 [US1] Extender `api/app/modules/wallet/service.py` con un resultado inmutable de consulta y `get_balance(user_id, repo=default_repository)`, reutilizando `get_wallet_by_user`, `WalletNotFoundError` y `to_json`; la lectura no abre una escritura ni crea una billetera (HU-05 CA-1, CA-2, CA-5).
- [ ] T011 [US1] Extender `api/app/modules/wallet/schemas.py` con `BalanceOut` que serialice el `Decimal` como cadena de exactamente dos decimales, y `api/app/modules/wallet/routes.py` con `@bp.get("")`, `@login_required` y `current_user_id()`; nunca aceptar `user_id` o `wallet_id` en URL, query o cuerpo (HU-05 CA-1, CA-4; RNF-01.1/.4).
- [ ] T012 [US1] Extender `webapp/src/features/wallet/api.ts` con `getBalance()` tipado desde `types.gen.ts` y crear `webapp/src/features/wallet/BalancePage.tsx` con `IonPage`, estados de carga/error accesibles y presentación COP usando `shared/money`; no usar `Number` para decidir ni `fetch` directamente en el componente (HU-05 CA-1, CA-2; RNF-03.2).
- [ ] T013 [US1] Actualizar `webapp/src/app/routes.tsx`, `webapp/src/app/HomePage.tsx` y `webapp/src/features/auth/LoginPage.tsx` para que `/` muestre `BalancePage`, conserve la navegación a recarga y lleve a ese panel tras un login exitoso; actualizar las pruebas de `webapp/src/app/__tests__/App.test.tsx` afectadas (RF-03 flujo principal; RNF-03.1).

**Checkpoint**: El usuario autenticado ve exclusivamente su saldo persistido en la pantalla
principal; una recarga exitosa se refleja en una consulta posterior.

---

## Phase 3: User Story 2 - Informar una billetera ausente (Priority: P2)

**Goal**: Una cuenta válida sin billetera recibe un problema claro sin que la consulta
cree datos ni muestre un saldo ficticio.

**Independent Test**: Autenticar una cuenta sin fila en `wallets`, ejecutar la consulta y
comprobar `404 wallet_not_found`, cero filas nuevas y mensaje accesible en la webapp.

### Tests for User Story 2 (write first; must fail)

- [ ] T014 [P] [US2] Añadir a `api/tests/e2e_api/test_balance_flow.py` el escenario de cuenta autenticada sin billetera: `404 wallet_not_found`, sin insertar `wallets`, `transactions` ni `idempotency_keys` (HU-05 CA-5; RF-03 flujo alternativo).
- [ ] T015 [P] [US2] Añadir a `webapp/src/features/wallet/__tests__/BalancePage.test.tsx` la aserción de que `wallet_not_found` produce una explicación accesible, no presenta `$ 0,00` y no expone datos de otras cuentas (HU-05 CA-5; RNF-06.1/.2).

### Implementation for User Story 2

- [ ] T016 [US2] Ajustar los manejos de error de `api/app/modules/wallet/service.py`, `api/app/modules/wallet/routes.py` y `webapp/src/features/wallet/BalancePage.tsx` según los resultados de T014-T015; reutilizar `WalletNotFoundError` y el formato RFC 9457, sin crear billeteras en una lectura (HU-05 CA-5).

**Checkpoint**: La ausencia de billetera es observable, segura y no tiene efectos laterales.

---

## Phase 4: Performance and end-to-end validation

**Purpose**: Cubrir la métrica transversal de HU-05 CA-6 y la experiencia de navegador.

- [ ] T017 [P] Crear `webapp/e2e/pages/balance.page.ts` y `webapp/e2e/hu-05-consultar-el-saldo.spec.ts`: iniciar sesión real, verificar saldo exacto, recargar y volver al panel para comprobar saldo actualizado; ejecutar en `desktop-chromium` y `mobile-chromium` con axe sin violaciones `serious` ni `critical` (HU-05 CA-1 a CA-5; RNF-03).
- [ ] T018 [P] Extender `api/tests/load/locustfile.py` con inicio de sesión real y una tarea activa `GET /api/v1/wallet`; documentar en `specs/001-ppa-5-consultar-el-saldo/quickstart.md` las credenciales ficticias y la precondición de una billetera sembrada, sin codificar secretos ni datos personales (HU-05 CA-6; RNF-02.1/.4, RNF-06.3).
- [ ] T019 Ejecutar la carga de T018 con 20 usuarios concurrentes y conservar como evidencia del PR que el p95 de `GET /api/v1/wallet` es <= 2000 ms; si faltan datos ficticios de carga, crear la tarea de seguimiento antes de declarar HU-05 terminada (HU-05 CA-6; RNF-02.1).
- [ ] T020 Ejecutar los comandos de calidad de `AGENTS.md`: API (`ruff format .`, `ruff check .`, `mypy app`, `pytest`) y webapp (`npm run lint`, `npm run typecheck`, `npm run test`, `npm run e2e`); corregir hallazgos sin reducir umbrales ni silenciar pruebas.

## Dependencies and execution order

- Phase 1 bloquea las historias: el contrato de sesión y los tipos generados deben ser
  consistentes antes de conectar el endpoint o la UI.
- US1 comienza tras Phase 1. T005-T009 pueden ejecutarse en paralelo; T010 precede T011;
  T012 puede avanzar en paralelo con la API una vez existe el contrato; T013 integra ambos.
- US2 sigue a US1 porque reutiliza el endpoint y la pantalla de saldo.
- T017 puede empezar después de T013; T018 depende de que el endpoint y el login real
  funcionen; T019 y T020 son gates finales.

## Parallel opportunities

- T001 y T002 modifican suites distintas y pueden avanzar en paralelo.
- T005 a T009 son pruebas en archivos distintos y pueden escribirse en paralelo.
- T014 y T015 pueden ejecutarse en paralelo.
- T017 y T018 pueden prepararse en paralelo tras el endpoint estable.

## Implementation strategy

1. Resolver el contrato compartido de sesión y el contrato OpenAPI.
2. Entregar US1 como incremento mínimo: endpoint de lectura y panel de saldo.
3. Añadir y verificar explícitamente el flujo de billetera ausente.
4. Completar navegador, carga y gates de calidad antes del PR.

## Notes

- Todas las tareas preservan el módulo `wallet`, la migración `0002_wallet_tables` y los
  helpers monetarios existentes de HU-08; no se duplican.
- `[P]` identifica archivos independientes. El autor revisa el diff y realiza cualquier
  commit; este flujo no autoriza `git add`, `git commit` ni `git push`.
