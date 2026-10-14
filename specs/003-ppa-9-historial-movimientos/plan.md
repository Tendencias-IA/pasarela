# Implementation Plan: Historial de movimientos (HU-09)

**Branch**: `feat/PPA-9-historial-movimientos` | **Date**: 2026-10-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-ppa-9-historial-movimientos/spec.md`

## Summary

Un usuario autenticado consulta los movimientos de su billetera (recargas, transferencias
enviadas y recibidas, exitosas y rechazadas) en páginas de 20, del más reciente al más
antiguo, con la contraparte de una transferencia enmascarada desde el servidor. Se crea el
módulo `movements` (API y webapp) con el endpoint `GET /api/v1/movements?page=` que **solo
lee** la tabla compartida `transactions` (ADR-0006) y resuelve billetera y contraparte a
través de los servicios de `wallet` y `accounts`. No hay migración ni tablas nuevas. La
pantalla usa Ionic con TanStack Query para el estado del servidor y reemplaza la página
"Próximamente" de `/movimientos`. La consulta y la pantalla quedan listas para que HU-10
añada filtros sin reestructurar nada.

## Technical Context

**Language/Version**: Python 3.12 (API), TypeScript 5.9 / React 18 (webapp)

**Primary Dependencies**: Flask 3, SQLAlchemy 2, Pydantic 2 (ya instaladas); Ionic React 9, react-router-dom 6 (ya instaladas); **nueva**: `@tanstack/react-query` (en la lista permitida de `webapp.md`, commit `build(PPA-9)` propio)

**Storage**: MySQL 8. Solo lectura de `transactions`; sin migración

**Testing**: pytest + pytest-cov (unitarias con repositorio falso, integración MySQL con 45 movimientos sembrados, contrato con `openapi.yaml`, e2e_api con login real), Vitest + MSW, Playwright (`hu-09-historial-movimientos.spec.ts`)

**Target Platform**: web responsive (escritorio y móvil) servida por nginx; API en gunicorn

**Project Type**: web application (`api/` + `webapp/`)

**Performance Goals**: p95 ≤ 3 s por consulta del historial con 20 usuarios concurrentes (RNF-02.2, RNF-02.4)

**Constraints**: página fija de 20, `page` desde 1, sin `page_size`/`offset` libres; orden `created_at DESC, id DESC`; titularidad por sesión; contraparte enmascarada en servidor; montos como cadena decimal; un módulo solo importa `service.py` de otro

**Scale/Scope**: 1 endpoint, 0 tablas, 1 pantalla, ~12 archivos nuevos en `api/`, ~9 en `webapp/`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cómo se cumple en este plan |
| --- | --- |
| I. Especificación antes de código | `spec.md` con 16/16 en el checklist; este plan y `tasks.md` preceden al código. |
| II. Trazabilidad | Cada test cita `HU-09 CA-n` o `RNF-x`; `direction`, paginación y enmascaramiento salen de FR-003, FR-007 y FR-004. Nada fuera de RF-05 (los filtros son HU-10). |
| III. Pruebas primero, cobertura ≥ 90 % | Tareas de test antes de cada implementación; unitarias de `movements.service` con `FakeMovementsRepository`; integración con 45 filas sembradas (titularidad, orden estable, 3 páginas); contrato; Vitest; Playwright con login real. |
| IV. Monolito modular, vertical slicing | Todo en `app/modules/movements/`; `transactions` se consulta desde su propio `repository.py` (compartida por ADR-0006); `wallets` y `users` solo vía `wallet_service` y `accounts_service` (research §1). `masking.py` va en `app/common/` como ya prevé `architecture.md`. |
| V. Integridad del dinero | Solo lectura; `Decimal` → cadena con `to_json`. No se abre transacción de escritura. |
| VI. Seguridad y privacidad | `@login_required`; billetera derivada de `current_user_id()`, nunca de la query; contraparte enmascarada en servidor; logs con `request_id`, `user_id` y `page`, sin teléfonos ni nombres de terceros. |
| VII. Simplicidad | Sin cursores, sin caché de servidor, sin abstracciones nuevas; una dependencia que la regla ya exige. |

**Gate pre-research**: PASS. **Desviaciones**: ninguna.

## Project Structure

### Documentation (this feature)

```text
specs/003-ppa-9-historial-movimientos/
├── plan.md              # Este archivo
├── spec.md
├── research.md          # Fase 0: decisiones de diseño y alternativas
├── data-model.md        # Fase 1: columnas usadas, entidades, contratos entre módulos
├── quickstart.md        # Fase 1: cómo validar de punta a punta
├── contracts/
│   └── movements.openapi.yaml   # Fase 1: fragmento que se fusiona en api/openapi.yaml
├── checklists/requirements.md
└── tasks.md             # Lo genera /speckit-tasks
```

### Source Code (repository root)

```text
api/
├── app/
│   ├── __init__.py                      # + registra movements.bp con prefijo /api/v1/movements
│   ├── common/
│   │   ├── masking.py                   # NUEVO: mask_phone, mask_name (architecture.md, RNF-06)
│   │   └── tests/test_masking.py        # NUEVO
│   └── modules/
│       ├── accounts/service.py          # + get_users_by_ids(ids) -> dict[int, UserSummary]
│       ├── accounts/repository.py       # + get_by_ids(ids)
│       ├── wallet/service.py            # + get_wallet_owners(wallet_ids) -> dict[int, WalletOwner]
│       ├── wallet/repository.py         # + get_wallets_by_ids(ids)
│       └── movements/
│           ├── __init__.py              # NUEVO
│           ├── schemas.py               # NUEVO: MovementsQuery, MovementOut, MovementsPageOut
│           ├── repository.py            # NUEVO: list_for_wallet(wallet_id, offset, limit), count_for_wallet
│           ├── service.py               # NUEVO: list_movements(user_id, page) -> MovementsPage; Direction, Movement, Counterparty
│           ├── routes.py                # NUEVO: GET ""  (prefijo /api/v1/movements)
│           └── tests/
│               ├── unit/fakes.py        # FakeMovementsRepository + fakes de wallet/accounts
│               ├── unit/test_list_movements_service.py
│               └── integration/test_movements_db.py   # titularidad, orden estable, 45 filas, 3 páginas
├── tests/
│   ├── factories.py                     # + make_transaction(...)
│   ├── contract/test_openapi_movements.py
│   ├── e2e_api/test_movements_flow.py   # login real → recarga → historial; 401; page inválida
│   └── load/locustfile.py               # + GET /api/v1/movements con login real
├── scripts/seed_test_user.py            # + segundo usuario sin movimientos (estado vacío E2E)
└── openapi.yaml                         # + /api/v1/movements, schemas Counterparty, MovementOut, MovementsPageOut

webapp/
├── package.json                         # + @tanstack/react-query (commit build)
├── src/
│   ├── app/
│   │   ├── App.tsx                      # + QueryClientProvider
│   │   ├── queryClient.ts               # NUEVO: QueryClient con defaults (retry 0 en 4xx)
│   │   └── routes.tsx                   # /movimientos → MovementsPage (quita ComingSoonPage de esa ruta)
│   ├── features/
│   │   ├── movements/
│   │   │   ├── MovementsPage.tsx        # NUEVO: IonPage, IonList de MovementItem, Pagination, EmptyState
│   │   │   ├── MovementItem.tsx         # NUEVO: fecha, monto, tipo/dirección, estado, contraparte
│   │   │   ├── Pagination.tsx           # NUEVO: anterior/siguiente + "página X de Y"
│   │   │   ├── useMovements.ts          # NUEVO: useQuery(["movements", page]) + corrección de página fuera de rango
│   │   │   ├── api.ts                   # NUEVO: getMovements(page)
│   │   │   └── __tests__/{useMovements.test.ts, MovementsPage.test.tsx}
│   │   └── wallet/useRecharge.ts        # + invalida ["movements"] tras éxito
│   └── shared/
│       ├── dates/index.ts               # NUEVO: formatDateTime (es-CO, zona del navegador)
│       ├── dates/__tests__/dates.test.ts
│       └── api/types.gen.ts             # regenerado con npm run api:types
└── e2e/
    ├── pages/movements.page.ts          # NUEVO
    └── hu-09-historial-movimientos.spec.ts  # NUEVO
```

**Structure Decision**: aplicación web `api/` + `webapp/` existente; la HU vive en el slice
`movements` de ambos lados. Los dos añadidos a `wallet` y `accounts` son funciones públicas
de `service.py` (y la consulta mínima en su repositorio) que esta HU necesita para no tocar
tablas ajenas; HU-06 (preview con destinatario enmascarado) las reutilizará.

## Phase 0: Research

Ver [research.md](research.md). Resumen de decisiones:

1. **Contraparte sin tocar tablas ajenas**: `movements` lee `transactions`; la billetera
   del usuario y los titulares de las billeteras ajenas se piden a `wallet_service`, que a
   su vez usa `accounts_service`. Tres consultas acotadas por página.
2. **`app/common/masking.py`** con `mask_phone` y `mask_name`, formato de `architecture.md`.
3. **`users.full_name` aún no existe** (HU-01 en progreso): `name_masked` es `null` hasta
   entonces; el contrato, la pantalla y las pruebas ya lo contemplan.
4. **Paginación** fija de 20, `page >= 1`, página fuera de rango responde vacía con el total,
   `page` inválida `422 validation`.
5. **Orden** `created_at DESC, id DESC` (desempate estable).
6. **TanStack Query** en la webapp, como fija `webapp.md`, en commit `build(PPA-9)` propio.
7. **E2E con login real** y segundo usuario sembrado para el estado vacío.

## Phase 1: Design

- [data-model.md](data-model.md): columnas usadas, entidades de dominio, contratos entre
  módulos, validación de `page`.
- [contracts/movements.openapi.yaml](contracts/movements.openapi.yaml): `GET
  /api/v1/movements`, `MovementOut`, `MovementsPageOut`, `Counterparty`.
- [quickstart.md](quickstart.md): cómo levantar, probar y verificar con curl, pytest y
  Playwright.

**Constitution Check post-diseño**: PASS. La dependencia nueva está en la lista permitida y
la regla de `webapp.md` la exige para este tipo de estado; no hay otra desviación.

## Complexity Tracking

> Sin violaciones a la constitución. Riesgos y acuerdos con el equipo:

| Riesgo | Mitigación |
| --- | --- |
| HU-01 (Melanny) añade `full_name` a `users` | `accounts_service.get_users_by_ids` devuelve `full_name=None` hoy; el PR le indica la única línea a cambiar cuando llegue la columna. `mask_name` ya queda implementado y probado. |
| HU-05 (Moisés) también montará TanStack Query | Esta HU deja `QueryClientProvider` y `queryClient.ts` en `app/`; se le avisa en el PR para que reutilice la clave `["wallet"]` e invalide desde recargas. |
| HU-06/HU-07 producen transferencias reales | El historial ya las muestra (dirección, contraparte); las pruebas de esta HU las cubren con filas sembradas. HU-07 debe invalidar `["movements"]` tras confirmar. |
| Nuevo movimiento mientras el usuario pagina puede repetir un ítem | Aceptado en v1.0 (spec, edge cases); cursores quedan como mejora si molesta. |
