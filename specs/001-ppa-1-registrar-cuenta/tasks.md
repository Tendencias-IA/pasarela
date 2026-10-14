# Tasks: Registrar una cuenta

**Input**: Design documents from `specs/001-ppa-1-registrar-cuenta/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/accounts.openapi.yaml](contracts/accounts.openapi.yaml)

**Tests**: Obligatorios y escritos primero por el Principio III de la constitución.
Cada tarea de prueba debe ejecutarse y fallar por la ausencia del comportamiento antes
de comenzar las tareas de implementación correspondientes.

**Organization**: Existe una sola historia P1. Setup y Foundational crean únicamente el
andamiaje compartido indispensable; toda conducta de registro se mantiene en US1.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Puede ejecutarse en paralelo una vez satisfechas sus dependencias previas.
- **[US1]**: Pertenece a HU-01 Crear una cuenta y billetera.
- Todas las rutas son relativas a la raíz del repositorio.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Crear los proyectos mínimos de API y webapp que todavía no existen.

- [X] T001 [P] Configurar Python 3.12 con Flask, Flask-SQLAlchemy, Flask-Migrate, SQLAlchemy, Alembic, PyMySQL, Pydantic, argon2-cffi, Flask-Limiter, python-json-logger y gunicorn; extras dev pytest, pytest-cov, pytest-mock, Ruff, mypy, testcontainers[mysql] y Schemathesis; y gates de Ruff, mypy estricto y cobertura de líneas/ramas ≥90 % en `api/pyproject.toml`
- [X] T002 [P] Crear los paquetes vacíos del monolito modular en `api/app/__init__.py`, `api/app/common/__init__.py`, `api/app/modules/__init__.py`, `api/app/modules/accounts/__init__.py` y `api/app/modules/wallet/__init__.py`
- [X] T003 [P] Inicializar React 18 con react-dom, Ionic React 9, Ionic React Router 9, Ionicons, react-router-dom 6, TanStack Query y React Hook Form; dev dependencies Vite, TypeScript, Vitest, Testing Library, MSW, Playwright, axe, openapi-typescript, ESLint/JSX-a11y y Prettier con versiones fijadas; y scripts `lint`, `typecheck`, `test`, `build`, `e2e` y `api:types` en `webapp/package.json` y `webapp/package-lock.json`
- [X] T004 [P] Configurar TypeScript estricto, Vite con proxy `/api`, Vitest, ESLint, jsx-a11y y Prettier en `webapp/tsconfig.json`, `webapp/vite.config.ts`, `webapp/vitest.config.ts`, `webapp/eslint.config.js` y `webapp/.prettierrc.json`
- [X] T005 [P] Configurar Playwright con proyectos `desktop-chromium` 1280×800 y `mobile-chromium` Pixel 7, reintentos 0 local/1 CI y trazas/vídeo solo al fallar en `webapp/playwright.config.ts`
- [X] T006 Crear la entrada de Vite, cargar `setupIonicReact`, el CSS base y las variables de tema de Ionic, y configurar el entorno de pruebas con Testing Library, MSW y axe en `webapp/index.html`, `webapp/src/main.tsx`, `webapp/src/theme/variables.css`, `webapp/src/test/setup.ts` y `webapp/src/test/server.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Proveer configuración, errores, observabilidad, migraciones y cliente HTTP
compartidos antes de implementar HU-01.

**⚠️ CRITICAL**: Ninguna tarea de US1 comienza hasta completar esta fase.

### Foundational tests (write and run red first)

- [X] T007 [P] Escribir pruebas fallidas para app factory, `GET /health`, límite de cuerpo de 16 KB, cabeceras de seguridad, `X-Request-Id` y problemas RFC 9457 en `api/tests/test_app_factory.py`
- [X] T008 [P] Escribir pruebas fallidas del parseo de `application/problem+json` y asociación de `errors[]` por campo en `webapp/src/shared/api/__tests__/problem.test.ts`

### Foundational implementation

- [X] T009 [P] Implementar configuraciones `development`, `testing`, `e2e` y `production` con `DATABASE_URL`, `SECRET_KEY`, `LOG_LEVEL`, `MAX_CONTENT_LENGTH=16384` y cookies seguras por ambiente en `api/app/config.py`
- [X] T010 [P] Declarar SQLAlchemy, Flask-Migrate y Flask-Limiter sin inicialización global de aplicación y preparar fixtures compartidas con testcontainers MySQL, migraciones, rollback, cliente HTTP y factories ficticias en `api/app/extensions.py`, `api/tests/conftest.py` y `api/tests/factories.py`
- [X] T011 [P] Implementar `AppError`, validación agregada y manejadores RFC 9457 sin incluir valores enviados por el usuario en `api/app/common/errors.py`
- [X] T012 [P] Implementar logs JSON, propagación/generación de `request_id` y medición `duration_ms` sin cuerpos, contraseñas, hashes, identificación ni teléfonos completos en `api/app/common/logging.py`
- [X] T013 Implementar `create_app`, registrar extensiones y manejadores, aplicar cabeceras de seguridad y exponer `GET /health` con chequeo `SELECT 1` en `api/app/__init__.py`
- [X] T014 Inicializar Flask-Migrate/Alembic sin `create_all()` y conectado a los metadatos de SQLAlchemy en `api/migrations/env.py`, `api/migrations/script.py.mako` y `api/migrations/alembic.ini`
- [X] T015 [P] Implementar el cliente same-origin que envía `X-Requested-With: fetch`, conserva cookies y traduce problemas RFC 9457 en `webapp/src/shared/api/client.ts` y `webapp/src/shared/api/problem.ts`
- [X] T016 [P] Configurar QueryClient, `IonReactRouter`, `IonApp` e `IonRouterOutlet` para la estructura pública inicial de la aplicación en `webapp/src/app/providers.tsx` y `webapp/src/app/App.tsx`

**Checkpoint**: Los tests foundational pasan y la API/webapp arrancan sin comportamiento
de registro todavía.

---

## Phase 3: User Story 1 — Crear una cuenta y billetera (Priority: P1) 🎯 MVP

**Goal**: Permitir que un visitante registre una cuenta con datos válidos y únicos y
reciba exactamente una billetera con saldo inicial `0.00`, sin iniciar sesión.

**Independent Test**: Enviar el formulario con datos ficticios válidos, recibir `201`,
verificar una sola fila en `users`, una sola fila relacionada en `wallets`, saldo exacto
`0.00` y ausencia de contraseña en texto plano; repetir o invalidar datos debe rechazar
sin persistencia parcial.

### Tests for User Story 1 (write and run red first) ⚠️

- [X] T017 [P] [US1] Escribir pruebas de schemas para HU-01 CA-3/CA-5: `full_name` 2–100 letras Unicode/diacríticos/espacios/apóstrofos/guiones, `phone` exactamente 10 dígitos iniciando en `3`, `national_id` 5–20 alfanuméricos, correo válido y contraseña de 8+ con letra y número, acumulando todos los errores, en `api/app/modules/accounts/tests/unit/test_schemas.py`
- [X] T018 [P] [US1] Escribir pruebas unitarias para HU-01 CA-1/CA-2/CA-4/CA-6: normalización, hash Argon2id, error genérico por duplicado, llamada única a wallet y rollback lógico sin texto plano en resultados/logs, en `api/app/modules/accounts/tests/unit/test_service.py`
- [ ] T019 [P] [US1] Escribir pruebas MySQL para HU-01 CA-1/CA-2/CA-4 y SC-003: unicidad de teléfono, `national_id` y correo, dos registros concurrentes con una sola creación y rollback completo si falla la billetera, en `api/app/modules/accounts/tests/integration/test_registration_transaction.py`
- [ ] T020 [P] [US1] Escribir pruebas MySQL para HU-01 CA-2: relación uno-a-uno, saldo `Decimal("0.00")`, `DECIMAL(15,2)` y rechazo de una segunda billetera para el mismo usuario, en `api/app/modules/wallet/tests/integration/test_create_wallet.py`
- [ ] T021 [P] [US1] Escribir pruebas HTTP/contrato para HU-01 CA-1–CA-6 sobre `POST /api/v1/accounts`: `201`, `400`, `409`, `413`, `422`, `500`, cabecera `X-Request-Id`, ausencia de cookie y conformidad OpenAPI, en `api/tests/contract/test_accounts_contract.py` y `api/tests/e2e_api/test_account_registration.py`
- [ ] T022 [P] [US1] Escribir pruebas de componente para HU-01 CA-1/CA-3/CA-4/CA-5: etiquetas, campos obligatorios, errores con `aria-describedby`, respuesta duplicada genérica, estado de envío único y confirmación sin login, en `webapp/src/features/accounts/__tests__/RegisterPage.test.tsx`
- [ ] T023 [P] [US1] Escribir primero el escenario Playwright fallido de HU-01 con camino exitoso y rechazado, selectores accesibles y axe sin violaciones serious/critical, en `webapp/e2e/pages/register.page.ts` y `webapp/e2e/hu-01-registrar-cuenta.spec.ts`

**Red checkpoint**: Ejecutar T017–T023 y conservar evidencia de que fallan por el
comportamiento aún no implementado, no por errores de configuración.

### Data model and migration for User Story 1

- [X] T024 [P] [US1] Extender el `User` compartido con login: mantener `id`, `phone` y `password_hash`; añadir `full_name VARCHAR(100)`, `national_id VARCHAR(20)` y `email VARCHAR(254)` obligatorios en el contrato HU-01 pero anulables en almacenamiento para usuarios preexistentes de HU-02; conservar normalización, unicidad e inmutabilidad, en `api/app/modules/accounts/models.py`
- [X] T025 [P] [US1] Implementar `Wallet` con `id BIGINT` generado; `user_id BIGINT` requerido, FK restrictiva y único; `balance DECIMAL(15,2)` requerido, default `0.00` y `CHECK balance >= 0`; timestamps UTC generados por servidor, en `api/app/modules/wallet/models.py`
- [X] T026 [US1] Encadenar HU-01 después de `0002_wallet_tables` de HU-08: extender `users` con `uq_users_email` y `uq_users_national_id` sin recrear `users` ni `wallets`, en `api/migrations/versions/0003_extend_users_registration.py`

### API implementation for User Story 1

- [X] T027 [P] [US1] Implementar `RegisterAccountIn`, `RegisterAccountOut` y validadores de todas las restricciones de T017, rechazando propiedades desconocidas y serializando el saldo como cadena, en `api/app/modules/accounts/schemas.py`
- [X] T028 [US1] Implementar inserción, `flush` y consultas de unicidad con `select()` SQLAlchemy 2, sin `commit()` ni consultas a `wallets`, en `api/app/modules/accounts/repository.py`
- [X] T029 [US1] Implementar `wallet.repository.create_for_user` y el servicio público `create_wallet_for_account` sin abrir/cerrar la transacción recibida y usando `Decimal("0.00")`, en `api/app/modules/wallet/repository.py` y `api/app/modules/wallet/service.py`
- [X] T030 [US1] Implementar `register_account` con canonicalización y Argon2id antes de persistir, abrir una sola `db.session.begin()` antes de cualquier consulta/inserción, llamar a `wallet.service` dentro de ella, traducir de forma segura `IntegrityError` a `duplicate_identity` después del rollback y emitir `account.registered` sin PII, en `api/app/modules/accounts/service.py`
- [X] T031 [US1] Implementar el blueprint público `POST /api/v1/accounts` limitado a parsear JSON, validar schema, llamar al servicio y devolver `201`/RFC 9457 sin crear sesión, en `api/app/modules/accounts/routes.py`
- [X] T032 [P] [US1] Incorporar el recorte revisado de `specs/001-ppa-1-registrar-cuenta/contracts/accounts.openapi.yaml` al contrato canónico completo `api/openapi.yaml`
- [X] T033 [US1] Registrar el blueprint de accounts y cargar los modelos para migraciones sin importar repositorios entre módulos en `api/app/__init__.py`

### Webapp implementation for User Story 1

- [X] T034 [P] [US1] Adoptar directamente los componentes Ionic `IonInput`, `IonButton`, `IonList`, `IonItem` e `IonToast`, con errores accesibles y estados que no dependan solo del color, sin crear wrappers que no agreguen comportamiento de dominio, en `webapp/src/features/accounts/RegisterPage.tsx`
- [X] T035 [P] [US1] Generar tipos desde `api/openapi.yaml` e implementar `registerAccount` sin tipos manuales ni exposición de contraseña en errores, en `webapp/src/shared/api/types.gen.ts` y `webapp/src/features/accounts/api.ts`
- [X] T036 [US1] Implementar el formulario responsive como `IonPage` con `IonHeader`, `IonToolbar`, `IonTitle` e `IonContent`; incluir nombre, teléfono, número de identificación, correo y contraseña, feedback inmediato equivalente al servidor, envío único y resultados accesibles, en `webapp/src/features/accounts/RegisterPage.tsx`
- [X] T037 [US1] Exponer la página pública `/registro`, mover foco al título al navegar y no crear estado de sesión tras éxito, en `webapp/src/app/App.tsx`
- [ ] T038 [US1] Ejecutar y corregir T017–T023 hasta que todos los tests de HU-01 pasen sin debilitar aserciones, excluir ramas de cobertura ni silenciar accesibilidad, en `api/app/modules/accounts/tests/`, `api/app/modules/wallet/tests/`, `api/tests/`, `webapp/src/features/accounts/__tests__/` y `webapp/e2e/`

**Checkpoint**: HU-01 funciona y puede demostrarse de forma independiente; no existen
login, verificación, recuperación ni datos financieros reales.

---

## Phase 4: Polish & Cross-Cutting Validation

**Purpose**: Comprobar trazabilidad, seguridad, empaquetado y todos los gates antes de
considerar terminada la historia.

- [ ] T039 [P] Auditar que cada prueba cite HU-01 CA-1–CA-6 o RNF aplicable y que ninguna respuesta/log incluya contraseña, hash o `national_id`, en `api/app/modules/accounts/tests/`, `api/tests/`, `webapp/src/features/accounts/__tests__/` y `webapp/e2e/hu-01-registrar-cuenta.spec.ts`
- [ ] T040 [P] Ejecutar `ruff format --check .`, `ruff check .`, `mypy app` y `pytest`, dejando cobertura de líneas y ramas ≥90 %, sobre `api/pyproject.toml` y `api/`
- [ ] T041 [P] Ejecutar `npm run lint`, `npm run typecheck`, `npm run test -- --coverage`, `npm run build` y `npm run e2e` sobre `webapp/package.json` y `webapp/`
- [ ] T042 Validar migraciones y el flujo manual `201`/`409`/`422` con `docker compose --profile app up --build` siguiendo `specs/001-ppa-1-registrar-cuenta/quickstart.md`, `docker-compose.yml` y `docker/`
- [ ] T043 Revisar secretos y alcance con `gitleaks`, confirmar que `.env` no esté versionado y medir el diff para dividir el PR si supera 400 líneas significativas, usando `.gitleaksignore`, `.gitignore` y `.github/PULL_REQUEST_TEMPLATE.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 — Setup**: no tiene dependencias y puede comenzar de inmediato.
- **Phase 2 — Foundational**: depende de Phase 1 y bloquea HU-01.
- **Phase 3 — US1**: depende de Phase 2; las pruebas T017–T023 se escriben y fallan antes
  de T024–T037.
- **Phase 4 — Polish**: depende de que T038 deje HU-01 completamente verde.

### Task Dependencies

- T004–T006 dependen de T003; T007 depende de T001–T002; T008 depende de T003–T006.
- T013 depende de T009–T012; T014 depende de T009–T010; T015 depende de T008;
  T016 depende de T003–T006.
- T017–T023 dependen de completar T007–T016, pero pueden escribirse en paralelo entre sí.
- T026 depende de T024–T025; T028 depende de T024; T029 depende de T025; T030 depende de
  T027–T029; T031 depende de T030; T033 depende de T031–T032.
- T035 depende de T032; T036 depende de T034–T035; T037 depende de T036; T038 depende de
  T024–T037.
- T039–T041 dependen de T038 y pueden ejecutarse en paralelo; T042 depende de T040–T041;
  T043 es la revisión final.

### User Story Dependencies

- **US1 (P1)**: no depende de otra historia. Setup y Foundational son infraestructura,
  no comportamiento funcional adicional.

## Parallel Opportunities

- T001–T003 pueden ejecutarse en paralelo.
- Después de T003, T004 y T005 pueden ejecutarse en paralelo.
- T007 y T008 pueden escribirse en paralelo; T009–T012 también ocupan archivos distintos.
- T017–T023 son pruebas independientes y pueden redactarse en paralelo antes del red gate.
- T024 y T025 pueden implementarse en paralelo; T027 y T032 también son independientes.
- Después de T032, T034 y T035 pueden ejecutarse en paralelo.
- T039–T041 son validaciones paralelizables antes de la prueba integrada T042.

## Parallel Example: User Story 1

```text
Task: "T017 schemas de registro en api/app/modules/accounts/tests/unit/test_schemas.py"
Task: "T018 servicio de registro en api/app/modules/accounts/tests/unit/test_service.py"
Task: "T019 transacción y concurrencia en api/app/modules/accounts/tests/integration/test_registration_transaction.py"
Task: "T020 billetera inicial en api/app/modules/wallet/tests/integration/test_create_wallet.py"
Task: "T021 contrato y HTTP en api/tests/contract/ y api/tests/e2e_api/"
Task: "T022 formulario React en webapp/src/features/accounts/__tests__/RegisterPage.test.tsx"
Task: "T023 Playwright en webapp/e2e/hu-01-registrar-cuenta.spec.ts"
```

Después del red gate:

```text
Task: "T024 modelo User en api/app/modules/accounts/models.py"
Task: "T025 modelo Wallet en api/app/modules/wallet/models.py"
Task: "T027 schemas Pydantic en api/app/modules/accounts/schemas.py"
Task: "T032 contrato canónico en api/openapi.yaml"
Task: "T034 adopción de componentes Ionic en webapp/src/features/accounts/RegisterPage.tsx"
```

## Implementation Strategy

### MVP First

1. Completar Setup y Foundational.
2. Escribir T017–T023 y confirmar el red gate.
3. Implementar T024–T037 respetando las dependencias.
4. Completar T038 y validar HU-01 de forma independiente.
5. Ejecutar Phase 4 antes de preparar el PR.

### Review strategy

- Mantener los cambios sin stage para que la persona responsable revise el diff antes de
  decidir los commits, conforme al flujo vigente del repositorio.
- Mantener pruebas y comportamiento relacionados juntos al proponer grupos lógicos y
  conservar evidencia del red gate en el cuerpo del PR.
- Si el diff supera 400 líneas significativas, proponer dividirlo antes del PR en
  incrementos revisables: scaffold/foundation, modelos+migración, API+pruebas y webapp+E2E.
- No hacer `git add`, commit, push ni abrir PR sin solicitud explícita de la persona responsable.

## Notes

- `[P]` significa archivos distintos; no elimina las dependencias indicadas.
- Ninguna tarea añade login, sesión, verificación, recuperación de contraseña, movimientos
  por saldo inicial ni integraciones financieras.
- MySQL real es obligatorio para unicidad concurrente y rollback; SQLite no sustituye
  esas pruebas.
- Nunca se usa `float` para el saldo, ni se guardan contraseñas o datos reales.
