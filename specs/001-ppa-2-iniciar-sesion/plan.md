# Implementation Plan: Iniciar sesión

**Branch**: `001-ppa-2-iniciar-sesion` | **Date**: 2026-10-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-ppa-2-iniciar-sesion/spec.md`

## Summary

HU-02: un usuario con cuenta existente inicia sesión con teléfono y contraseña y recibe
una sesión del lado del servidor; credenciales inválidas (teléfono inexistente o
contraseña incorrecta) se rechazan con el mismo error genérico, sin filtrar cuál falló;
sin sesión válida no se puede llamar a ninguna función privada. Se implementa con dos
módulos nuevos: `accounts` (modelo `User` mínimo: id, teléfono único, hash de contraseña
— sin el flujo de registro de HU-01, que queda fuera de esta historia) y `auth`
(modelo `Session`, `POST /auth/login`, `POST /auth/logout`, decorador `@login_required`
y `current_user()` reutilizable por cualquier módulo futuro). El ciclo completo de
expiración deslizante de 5 minutos es HU-03 y se deja preparado en el modelo
(`expires_at`, `last_activity_at`) pero esta tarea solo prueba que login/logout
funcionan como puerta de acceso (FR-005/FR-006), no la expiración por inactividad.

## Technical Context

**Language/Version**: Python 3.12, Flask 3, SQLAlchemy 2 (fijado en `AGENTS.md`, sin alternativas evaluadas)

**Primary Dependencies**: Flask, SQLAlchemy 2, Pydantic 2, `argon2-cffi` (hash Argon2id, RNF-01.2) y `flask-limiter` (rate limit de login, `.claude/rules/security.md`) — ninguna estaba en `pyproject.toml`, se añaden en commit `build(PPA-2)` propio

**Storage**: MySQL 8 vía SQLAlchemy/Alembic; tablas nuevas `users` (mínima, solo lo que HU-02 necesita leer) y `sessions`

**Testing**: pytest + pytest-cov (unit en `accounts`/`auth` con repositorios falsos, integración contra MySQL de pruebas para unicidad y expiración), `tests/contract` contra `openapi.yaml`

**Target Platform**: servicio web Flask detrás de WSGI/gunicorn, mismo origen que la webapp (sin CORS)

**Project Type**: web application (backend `api/` + frontend `webapp/`, estructura ya fijada en `architecture.md`)

**Performance Goals**: sin objetivo propio de RNF-02 para login (no está en la lista de endpoints medidos); se mantiene bajo el techo general de la app

**Constraints**: contraseña nunca en texto plano en logs/errores (FR-004); mismo código/mensaje para ambos tipos de credencial inválida (FR-003); comparación de hash con tiempo de respuesta aproximado aunque el teléfono no exista (RNF-01.5); identificador de sesión hasheado y comparado con `hmac.compare_digest`; cookie `HttpOnly; SameSite=Lax; Secure` (no-`Secure` en `testing`/`e2e`)

**Scale/Scope**: un endpoint de login, uno de logout, un decorador transversal; sin UI de registro ni edición de perfil en esta historia

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento |
| --- | --- |
| I. Especificación antes de código | `spec.md` y este `plan.md` existen en `specs/001-ppa-2-iniciar-sesion/`; `tasks.md` se genera a continuación con `/speckit-tasks`. PASA. |
| II. Trazabilidad a requisitos | Cada regla del plan cita HU-02 CA-n o RNF-01.n; no se añade nada fuera de la spec. PASA. |
| III. Pruebas primero y cobertura ≥ 90% | Tareas de prueba (unit de `accounts`/`auth`, integración con MySQL, contrato) se escriben antes del código en `tasks.md`. PASA (se verifica en `/speckit-implement`). |
| IV. Monolito modular con vertical slicing | Dos módulos nuevos (`accounts`, `auth`) con su propia tabla; `auth` llama a `accounts.service.get_user_by_phone`, nunca a su repositorio. PASA. |
| V. Integridad del dinero | No aplica: esta historia no toca saldos ni transacciones. N/A. |
| VI. Seguridad y privacidad por defecto | Argon2id, sesión server-side, cookie `HttpOnly/SameSite/Secure`, mensaje de error genérico, sin contraseña en logs, rate limit de login. PASA. |
| VII. Simplicidad | `User` se crea con solo los campos que HU-02 necesita leer (id, teléfono, hash); los campos exclusivos de HU-01 (nombre, identificación, correo) se añaden cuando se implemente esa historia, no antes. PASA. |

Sin violaciones; no se llena "Complexity Tracking".

## Project Structure

### Documentation (this feature)

```text
specs/001-ppa-2-iniciar-sesion/
├── plan.md              # este archivo
├── research.md          # Fase 0
├── data-model.md         # Fase 1
├── quickstart.md         # Fase 1
├── contracts/
│   └── auth.openapi.yaml # Fase 1: fragmento de contrato para /auth/login y /auth/logout
└── tasks.md               # Fase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
api/
├── app/
│   ├── common/
│   │   ├── passwords.py       # hash_password, verify_password (Argon2id)
│   │   └── auth.py            # @login_required, current_user(), SESSION_COOKIE helpers
│   └── modules/
│       ├── accounts/
│       │   ├── __init__.py
│       │   ├── models.py      # User (mínimo para HU-02: id, phone, password_hash, timestamps)
│       │   ├── repository.py  # get_by_phone
│       │   ├── service.py     # get_user_by_phone (función pública para auth)
│       │   └── tests/
│       │       └── unit/test_service.py
│       └── auth/
│           ├── __init__.py
│           ├── models.py      # Session
│           ├── repository.py  # create, get_by_token_hash, revoke
│           ├── service.py     # login, logout, get_current_user
│           ├── schemas.py     # LoginIn / LoginOut
│           ├── routes.py      # POST /auth/login, POST /auth/logout
│           └── tests/
│               ├── unit/test_service.py
│               └── integration/test_routes.py
├── migrations/
│   └── versions/<rev>_create_users_and_sessions.py
└── tests/
    ├── factories.py           # UserFactory (para accounts y auth)
    └── contract/test_auth_contract.py

webapp/
└── src/
    └── features/
        └── auth/
            ├── LoginPage.tsx
            ├── useLogin.ts        # TanStack Query mutation contra POST /auth/login
            ├── __tests__/LoginPage.test.tsx
            └── api.ts             # tipos y llamada HTTP, basada en types.gen.ts

webapp/e2e/
└── hu-02-iniciar-sesion.spec.ts
```

**Structure Decision**: Web application ya definida por `architecture.md` (vertical
slicing por módulo de negocio). Esta historia introduce los dos primeros módulos del
backend (`accounts`, `auth`) y la primera feature del frontend (`auth`); no se crean
capas nuevas ni se reorganiza lo existente.

## Complexity Tracking

Sin violaciones que justificar.
