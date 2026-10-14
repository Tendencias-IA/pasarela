# Implementation Plan: Registrar una cuenta

**Branch**: `feat/PPA-1-registrar-cuenta` | **Date**: 2026-10-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-ppa-1-registrar-cuenta/spec.md`

## Summary

Implementar HU-01 como la primera vertical completa de la billetera: una pantalla pública
de registro en React envía los datos a `POST /api/v1/accounts`; el módulo `accounts` de
Flask valida y normaliza la entrada, protege la contraseña con Argon2id y persiste la
cuenta, mientras el servicio público de `wallet` crea una única billetera con saldo
`0.00` dentro de la misma transacción MySQL. Restricciones `UNIQUE` y su traducción a un
problema RFC 9457 garantizan la unicidad aun con solicitudes concurrentes.

## Technical Context

**Language/Version**: Python 3.12; TypeScript estricto sobre Node.js 22

**Primary Dependencies**: Flask 3, SQLAlchemy 2, Flask-Migrate/Alembic, Pydantic 2,
`argon2-cffi`; React 18, Vite, Ionic React 9, Ionic React Router 9, React Router 6,
TanStack Query y React Hook Form

**Storage**: MySQL 8/InnoDB con `utf8mb4`; tablas `users` y `wallets`

**Testing**: pytest, pytest-cov, testcontainers MySQL y Schemathesis; Vitest, Testing
Library, MSW, Playwright y axe

**Target Platform**: aplicación web responsive; API Linux detrás del proxy nginx del
repositorio y navegadores Chromium de escritorio y móvil

**Project Type**: aplicación web con despliegues separados de API y webapp dentro de un
monolito modular

**Performance Goals**: el registro debe mantenerse por debajo de 3 s p95 con la carga
académica de 20 usuarios concurrentes; la creación nunca deja datos parciales

**Constraints**: cuenta y billetera atómicas; contraseña solo como hash Argon2id;
teléfono, correo y número de identificación únicos; sin sesión, verificación ni
datos financieros reales; API y webapp desde el mismo origen

**Scale/Scope**: una HU, un endpoint público, una página responsive, dos entidades y
los cimientos mínimos de `api/` y `webapp/` necesarios para probar la vertical

## Constitution Check

*GATE: Passed for design. Re-check completed after Phase 1.*

| Principle or constraint | Pre-design result | Evidence / required treatment |
| --- | --- | --- |
| I. Specification before code | PASS | `spec.md` exists and this plan defines the owning modules. `tasks.md` remains mandatory before implementation. |
| II. Traceability to requirements | PASS | HU-01 maps to RF-01 and CA-01.1–CA-01.5; the globally unique identification number matches the central requirement. |
| III. Tests first and ≥90% API coverage | PASS | The design assigns unit, MySQL integration, contract, component and Playwright coverage to every acceptance criterion. |
| IV. Modular monolith / vertical slicing | PASS | Account behavior lives in `accounts`; wallet creation is called through `wallet.service`, never through its model or repository. |
| V. Money integrity | PASS | Initial balance uses `Decimal("0.00")` and `DECIMAL(15,2)`; account and wallet are committed in one transaction. |
| VI. Security and privacy by default | PASS | Argon2id, request validation, generic duplicate errors, no credential logging and no session creation. |
| VII. Simplicity and readability | PASS | Uses the prescribed three layers and Ionic primitives from ADR-0007 without adding a feature-specific UI abstraction. |
| Fixed stack and web-only scope | PASS | Uses the constitution stack and the existing same-origin deployment model. |

The feature specification and the central requirement use the same identification rule,
so no requirement synchronization is needed before implementation.

## Project Structure

### Documentation (this feature)

```text
specs/001-ppa-1-registrar-cuenta/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── accounts.openapi.yaml
└── tasks.md                       # generated later by $speckit-tasks
```

### Source Code (repository root)

```text
api/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── extensions.py
│   ├── common/
│   │   ├── errors.py
│   │   └── logging.py
│   └── modules/
│       ├── accounts/
│       │   ├── routes.py
│       │   ├── schemas.py
│       │   ├── service.py
│       │   ├── repository.py
│       │   ├── models.py
│       │   └── tests/
│       │       ├── unit/
│       │       └── integration/
│       └── wallet/
│           ├── service.py
│           ├── repository.py
│           ├── models.py
│           └── tests/
├── migrations/
├── tests/
│   ├── conftest.py
│   └── contract/
│       └── test_accounts_contract.py
├── openapi.yaml
└── pyproject.toml

webapp/
├── src/
│   ├── app/
│   │   ├── App.tsx
│   │   └── providers.tsx
│   ├── features/accounts/
│   │   ├── RegisterPage.tsx
│   │   ├── api.ts
│   │   └── __tests__/
│   ├── shared/api/
│   │   ├── client.ts
│   │   ├── problem.ts
│   │   └── types.gen.ts
│   └── theme/
│       └── variables.css
├── e2e/
│   ├── pages/register.page.ts
│   └── hu-01-registrar-cuenta.spec.ts
├── package.json
└── playwright.config.ts
```

**Structure Decision**: Se utiliza la estructura web de dos proyectos ya fijada por la
constitución. La primera HU crea solo el esqueleto transversal indispensable. La cuenta
pertenece a `accounts`; la billetera pertenece a `wallet`; `accounts.service` orquesta
ambos servicios dentro de una transacción sin importar modelos ni repositorios ajenos.

## Phase 0: Research Decisions

Las decisiones y alternativas se consolidan en [research.md](research.md). No quedan
asuntos técnicos pendientes de aclaración.

## Phase 1: Design

- [data-model.md](data-model.md) define `User` y `Wallet`, sus invariantes, índices y el
  límite transaccional.
- [contracts/accounts.openapi.yaml](contracts/accounts.openapi.yaml) define el contrato
  de `POST /api/v1/accounts`, incluidos los problemas `422` y `409`.
- [quickstart.md](quickstart.md) describe la validación local, automática y manual.
- Durante implementación, el contrato se incorporará al `api/openapi.yaml` canónico; el
  archivo de esta carpeta es el recorte revisable de la HU.

## Post-Design Constitution Re-check

| Gate | Result | Design evidence |
| --- | --- | --- |
| Traceable, testable behavior | PASS | Contract and quickstart map every scenario to HU-01/CA-01, with one globally unique identification number. |
| Module ownership | PASS | The data model assigns one table to each module and uses only `wallet.service` across the boundary. |
| Atomicity and exact money | PASS | A single SQLAlchemy transaction creates both rows and the wallet default is exact `0.00`. |
| Security and privacy | PASS | The design stores only an Argon2id hash, rejects unknown fields, limits body size and avoids echoing PII in errors. |
| Test-first quality | PASS | The validation guide covers red-first tests, concurrency, rollback, contract, UI and E2E accessibility. |
| Simplicity | PASS | Ionic React and its router are the approved component stack from ADR-0007; no feature-specific wrapper is needed. |

## Complexity Tracking

No additional architecture layers are introduced. The initial scaffold is reused from
`main`, including HU-02 login, its tests, HTTP client and Ionic configuration.

The complete HU is submitted in one PR at the author's request to expedite delivery.
Its diff exceeds the 400-line review target; commits separate dependencies, persistence,
backend and UI to support review. This is a documented review-size deviation, not a
change to repository quality thresholds.
