# Implementation Plan: Consultar el saldo

**Branch**: `001-ppa-5-consultar-el-saldo` | **Date**: 2026-10-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-ppa-5-consultar-el-saldo/spec.md`

## Summary

Implementar `GET /api/v1/wallet` sobre el módulo `wallet` ya creado por HU-08. El endpoint
deriva el usuario de la sesión, consulta únicamente su billetera existente y devuelve el
monto decimal como cadena. La webapp reemplazará el contenido provisional de inicio por
una pantalla de saldo y enlazará el éxito de inicio de sesión con esa pantalla. La historia
no crea ni altera saldos: reutiliza el saldo que HU-08 ya actualiza mediante recargas.

## Technical Context

**Language/Version**: Python 3.12; TypeScript estricto con React 18

**Primary Dependencies**: Flask 3, SQLAlchemy 2, Alembic, Pydantic 2; Ionic React,
TanStack Query, React Hook Form, Vitest y Playwright

**Storage**: MySQL 8; tabla `wallets` existente, creada por la migración
`0002_wallet_tables` de HU-08

**Testing**: pytest + pytest-cov, pruebas de integración contra MySQL, pruebas de
contrato contra `api/openapi.yaml`, Vitest y Playwright

**Target Platform**: API HTTP y webapp responsive servidas en el mismo origen

**Project Type**: Aplicación web con API y frontend

**Performance Goals**: p95 de `GET /api/v1/wallet` de dos segundos o menos bajo la carga
acordada

**Constraints**: Saldo exacto con `Decimal`/`DECIMAL(15,2)`/cadena JSON; autenticación y
titularidad en servidor; no exponer el saldo de otra cuenta; no añadir dependencias;
cobertura API de líneas y ramas >= 90 %

**Scale/Scope**: Una ruta privada sobre `wallets` existente, una pantalla de saldo y
pruebas para los seis criterios de HU-05; 20 usuarios concurrentes en la verificación de
rendimiento

## Constitution Check

| Principio | Cumplimiento del plan |
| --- | --- |
| I. Especificación antes de código | `spec.md` fue aprobado; este plan precede a `tasks.md` y a cualquier implementación. |
| II. Trazabilidad | Requisitos, tareas y pruebas citarán HU-05 CA-1 a CA-6, RF-03, RNF-01.1/.4, RNF-02.1, RNF-05.1 y RNF-06.1/.2/.4. |
| III. Pruebas primero | Las tareas crearán primero pruebas unitarias, de integración, contrato, UI, E2E y carga; la cobertura API no puede bajar de 90 %. |
| IV. Monolito modular | `wallet`, ya dueño de `wallets` desde HU-08, recibe la lectura de saldo en sus rutas, schemas, servicio, repositorio y pruebas. Usará el usuario de sesión a través de `app.common.auth`, sin importar repositorios ni modelos de otro módulo. |
| V. Integridad del dinero | Es una lectura sin escritura. El saldo se modelará como `DECIMAL(15,2)`, se leerá como `Decimal` y se serializará con dos decimales en cadena. |
| VI. Seguridad y privacidad | `@login_required` protege la ruta; el id se deriva de la sesión, no de la solicitud; la ausencia de billetera usa un problema RFC 9457 sin datos sensibles y el log no expone PII. |
| VII. Simplicidad y legibilidad | No se agregan dependencias, capas, cachés ni servicios. Se reutilizan Flask, SQLAlchemy, Pydantic, el cliente HTTP y los patrones del repositorio. |

**Resultado**: pasa el Constitution Check. No hay desviaciones que registrar en
Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/001-ppa-5-consultar-el-saldo/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── wallet.yaml
└── tasks.md                 # se generará en la siguiente fase
```

### Source Code (repository root)

```text
api/
├── app/
│   ├── __init__.py                              # blueprint wallet ya registrado
│   ├── common/
│   │   ├── auth.py                              # alinear 401 privado al contrato canónico
│   │   └── money.py                             # helper decimal/serialización existente
│   └── modules/
│       └── wallet/
│           ├── models.py                        # Wallet existente, dueño de wallets
│           ├── repository.py                    # reutilizar get_wallet_by_user
│           ├── service.py                       # añadir consulta de saldo y error ausente
│           ├── schemas.py                       # añadir respuesta BalanceOut
│           ├── routes.py                        # añadir GET /api/v1/wallet
│           └── tests/
│               ├── unit/
│               └── integration/
├── openapi.yaml
└── tests/
    ├── contract/test_wallet_contract.py          # ampliar con GET /wallet
    └── load/locustfile.py                        # activar saldo con login real

webapp/
├── src/
│   ├── app/App.tsx                              # ruta privada principal
│   ├── features/
│   │   ├── auth/LoginPage.tsx                   # navegar a saldo tras login válido
│   │   └── wallet/
│   │       ├── api.ts                           # añadir getBalance
│   │       ├── BalancePage.tsx
│   │       └── __tests__/
│   └── shared/money/                            # formato COP, si debe crearse
└── e2e/hu-05-consultar-el-saldo.spec.ts
```

**Structure Decision**: Se selecciona el monolito modular existente. HU-05 amplía el
módulo y la feature `wallet` creados por HU-08; no introduce una tabla, migración,
blueprint ni helper monetario duplicados. Los cambios limitados en `app` y `auth` integran
la navegación y normalizan la respuesta de sesión inválida.

## Complexity Tracking

No aplica: el plan no requiere ninguna violación a la constitución.

