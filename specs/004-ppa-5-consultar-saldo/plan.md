# Implementation Plan: Consultar el saldo (HU-05)

**Branch**: `feat/PPA-9-historial-movimientos` (integradora) | **Date**: 2026-10-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/004-ppa-5-consultar-saldo/spec.md`

## Summary

Un usuario autenticado consulta el saldo persistido de su billetera con `GET /api/v1/wallet`
y lo ve en la tarjeta "Saldo disponible" de la pantalla principal. La historia amplía el
módulo `wallet` (API y feature) que HU-08 creó: una función de servicio de **solo lectura**
(`get_balance`), un schema de salida (`WalletOut`), una ruta privada y el path en el
contrato. En la webapp, un hook `useWallet` con TanStack Query (ya montado por HU-09) y la
tarjeta en `HomePage`; `useRecharge` invalida la clave `["wallet"]` para que el panel
refleje la recarga (CA-3). Sin migración, sin tablas nuevas, sin dependencias nuevas. Se
reutilizan del borrador de moagu (`feat/PPA-5-consultar-el-saldo`) la spec, la investigación
y los tests de API; se descarta su renombre del código `invalid_session`.

## Technical Context

**Language/Version**: Python 3.12 (API), TypeScript 5.9 / React 18 (webapp)

**Primary Dependencies**: Flask 3, SQLAlchemy 2, Pydantic 2; Ionic React 9, TanStack Query 5 (ya instaladas). Ninguna nueva.

**Storage**: MySQL 8. Solo lectura de `wallets`; sin migración

**Testing**: pytest + pytest-cov (unitarias con `FakeWalletRepository`, e2e_api con login real, contrato con `openapi.yaml`), Vitest + MSW, Playwright (`hu-05-consultar-saldo.spec.ts`), Locust (nocturno)

**Target Platform**: web responsive (escritorio y móvil) servida por nginx; API en gunicorn

**Project Type**: web application (`api/` + `webapp/`)

**Performance Goals**: p95 ≤ 2 s en `GET /api/v1/wallet` con 20 usuarios concurrentes (RNF-02.1, RNF-02.4)

**Constraints**: id de usuario solo desde la sesión; lectura sin `FOR UPDATE` ni transacción de escritura; `Decimal` → cadena con `to_json`; `401 invalid_session` (no se renombra); `404 wallet_not_found` + `WARNING wallet.missing`; un módulo solo importa `service.py` de otro

**Scale/Scope**: 1 endpoint, 0 tablas, 1 tarjeta en una pantalla existente, ~5 archivos tocados en `api/`, ~6 en `webapp/`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cómo se cumple en este plan |
| --- | --- |
| I. Especificación antes de código | `spec.md` con 16/16 en el checklist; este plan y `tasks.md` preceden al código. |
| II. Trazabilidad | Cada test cita `HU-05 CA-n`, `RNF-x` o `FR-nnn`. Nada fuera de RF-03: no se crea billetera al consultar, no se muestran otros datos. |
| III. Pruebas primero, cobertura ≥ 90 % | Tareas de test antes de cada implementación y verificación de que fallan; unitarias con repositorio falso; e2e_api con login real; contrato; Vitest con MSW; Playwright con login real. |
| IV. Monolito modular, vertical slicing | Todo en `app/modules/wallet/` y `webapp/src/features/wallet/`; `HomePage` (en `app/`) consume el hook de la feature. Ningún import de repositorios ajenos. |
| V. Integridad del dinero | Lectura pura: sin transacción de escritura ni bloqueo; `Decimal` hasta el schema, cadena en JSON; la webapp formatea con `formatCOP` sin `Number`. |
| VI. Seguridad y privacidad | `@login_required`; `current_user_id()` de la sesión, nunca de la query; `404` sin filtrar existencia de otros; log `wallet.missing` con `user_id` y sin datos personales. |
| VII. Simplicidad | Una función de servicio, un schema, una ruta, un hook, una tarjeta. Sin dataclass intermedia ni pantalla nueva. |

**Gate pre-research**: PASS. **Desviaciones**: ninguna.

## Project Structure

### Documentation (this feature)

```text
specs/004-ppa-5-consultar-saldo/
├── plan.md              # Este archivo
├── spec.md
├── research.md          # Fase 0: decisiones y lo que se tomó o descartó del borrador
├── data-model.md        # Fase 1: columnas usadas, contrato de dominio, clave de caché
├── quickstart.md        # Fase 1: cómo validar de punta a punta
├── contracts/
│   └── wallet.openapi.yaml   # Fase 1: fragmento que se fusiona en api/openapi.yaml
├── checklists/requirements.md
└── tasks.md             # Lo genera /speckit-tasks
```

### Source Code (repository root)

```text
api/
├── app/modules/wallet/
│   ├── service.py                       # + get_balance(user_id, repo) -> Decimal; WARNING wallet.missing
│   ├── schemas.py                       # + WalletOut.from_balance(Decimal)
│   ├── routes.py                        # + GET "" (prefijo /api/v1/wallet) con @login_required
│   └── tests/unit/test_balance_service.py   # NUEVO (del borrador, ampliado con caplog)
├── tests/
│   ├── contract/test_openapi_wallet.py  # NUEVO: 200 vs WalletOut; path declarado
│   ├── e2e_api/test_balance_flow.py     # NUEVO (del borrador, código 401 corregido)
│   └── load/locustfile.py               # + @task wallet: GET /api/v1/wallet
└── openapi.yaml                         # + /api/v1/wallet, schema WalletOut

webapp/
├── src/
│   ├── app/
│   │   ├── HomePage.tsx                 # + tarjeta "Saldo disponible" (useWallet)
│   │   └── __tests__/HomePage.test.tsx  # NUEVO: saldo, cargando, no disponible, error
│   ├── features/wallet/
│   │   ├── api.ts                       # + getWallet(signal)
│   │   ├── useWallet.ts                 # NUEVO: useQuery(["wallet"]), WALLET_QUERY_KEY
│   │   ├── useRecharge.ts               # + invalida ["wallet"] tras 201
│   │   └── __tests__/useWallet.test.ts  # NUEVO
│   ├── shared/api/types.gen.ts          # regenerado con npm run api:types
│   └── test/server.ts                   # + handler por defecto GET /api/v1/wallet
└── e2e/
    ├── pages/home.page.ts               # NUEVO
    ├── hu-05-consultar-saldo.spec.ts    # NUEVO
    └── smoke.spec.ts                    # inicia sesión antes de abrir "/" (ahora es privada)
```

**Structure Decision**: aplicación web `api/` + `webapp/` existente; la HU vive en el slice
`wallet` de ambos lados. `HomePage` está en `app/` porque es la pantalla principal del
esqueleto y agrupa accesos de varias features; solo importa el hook público de `wallet`.

## Phase 0: Research

Ver [research.md](research.md). Resumen:

1. Titularidad desde la sesión; parámetros de query ignorados.
2. Lectura pura en `wallet.service.get_balance`; `WalletNotFoundError` + `WARNING`.
3. Contrato `200 {balance}`, `404 wallet_not_found`, `401 invalid_session` (se descarta el
   renombre a `unauthenticated` del borrador).
4. Tarjeta en `HomePage` con `useWallet` y clave `["wallet"]`; `useRecharge` la invalida.
5. Carga con Locust para CA-6.
6. `/` pasa a ser privada de hecho; `smoke.spec.ts` inicia sesión.

## Phase 1: Design

- [data-model.md](data-model.md), [contracts/wallet.openapi.yaml](contracts/wallet.openapi.yaml),
  [quickstart.md](quickstart.md).

**Constitution Check post-diseño**: PASS. Sin desviaciones.

## Complexity Tracking

> Sin violaciones a la constitución. Riesgos y acuerdos:

| Riesgo | Mitigación |
| --- | --- |
| Archivos compartidos con otras sesiones (`wallet/service.py`, `openapi.yaml`, `types.gen.ts`, `HomePage.tsx`, `useRecharge.ts`, `smoke.spec.ts`) | Cambios aditivos y pequeños; el orquestador los revisa al fusionar. Listados en el informe final. |
| HU-07 también debe invalidar `["wallet"]` | `WALLET_QUERY_KEY` exportada desde `features/wallet/useWallet.ts`; se avisa en el PR. |
| El borrador de moagu quedó en una rama aparte | No se fusiona; se tomaron solo los archivos útiles y se documenta en `spec.md`. |
