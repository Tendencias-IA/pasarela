---

description: "Task list for Iniciar sesión (HU-02 / PPA-2)"
---

# Tasks: Iniciar sesión

**Input**: Design documents from `/specs/001-iniciar-sesion/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/auth.openapi.yaml, quickstart.md

**Tests**: Incluidas. Principio III de la constitución exige pruebas antes de la
implementación; HU-07/HU-08 tienen pruebas de concurrencia obligatorias pero HU-02 no
las necesita (no hay saldo).

**Organization**: Tareas agrupadas por historia de usuario (US1, US2, US3 de `spec.md`).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Puede ejecutarse en paralelo (archivos distintos, sin dependencias)
- **[Story]**: US1 = login exitoso, US2 = credenciales inválidas sin filtrar cuál,
  US3 = sin sesión no hay acceso a funciones privadas

## Path Conventions

Monolito modular, estructura de `architecture.md`: `api/app/modules/<modulo>/`,
`api/app/common/`, `webapp/src/features/<modulo>/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Dependencias y scaffolding de los dos módulos nuevos.

- [ ] T001 Añadir `argon2-cffi~=23.1` y `flask-limiter~=3.9` a `dependencies` en
  `api/pyproject.toml` (commit propio `build(PPA-2): add argon2-cffi y flask-limiter`,
  ver `.claude/rules/git-workflow.md`)
- [ ] T002 [P] Crear `api/app/modules/accounts/__init__.py`,
  `api/app/modules/accounts/tests/__init__.py`,
  `api/app/modules/accounts/tests/unit/__init__.py` (paquetes vacíos)
- [ ] T003 [P] Crear `api/app/modules/auth/__init__.py`,
  `api/app/modules/auth/tests/__init__.py`,
  `api/app/modules/auth/tests/unit/__init__.py`,
  `api/app/modules/auth/tests/integration/__init__.py` (paquetes vacíos)
- [ ] T004 [P] Crear `webapp/src/features/auth/` (carpeta) y
  `webapp/src/features/auth/__tests__/` (carpeta) para la feature de login

**Checkpoint**: estructura de carpetas lista; sin lógica todavía.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Infraestructura transversal que toda historia de usuario necesita:
hash de contraseña, el modelo `User` (mínimo), `Session`, el decorador
`@login_required`, la migración de esquema y las factories de prueba.

**⚠️ CRITICAL**: ninguna historia de usuario puede probarse sin esta fase completa.

- [ ] T005 [P] Crear `api/app/common/passwords.py` con `hash_password(raw: str) -> str`
  y `verify_password(raw: str, hashed: str) -> bool` usando
  `argon2.PasswordHasher()` (Argon2id por defecto); nunca `hashlib` (RNF-01.2,
  `.claude/rules/security.md`)
- [ ] T006 [P] Crear `api/app/modules/accounts/models.py` con el modelo `User`
  (`__tablename__ = "users"`): `id: Mapped[int]` PK autoincremental,
  `phone: Mapped[str]` `VARCHAR(10)` UNIQUE NOT NULL, `password_hash: Mapped[str]`
  `VARCHAR(255)` NOT NULL, `created_at`/`updated_at` con `server_default=func.now()`
  (y `onupdate=func.now()` en `updated_at`) — exactamente los campos de
  `data-model.md`, sin adelantar `full_name`/`national_id`/`email` de HU-01
- [ ] T007 [US-shared] Crear `api/app/modules/accounts/repository.py` con
  `get_by_phone(phone: str) -> User | None` usando `select(User).where(User.phone ==
  phone)`, sin `Model.query` legado (depende de T006)
- [ ] T008 [US-shared] Crear `api/app/modules/accounts/service.py` con
  `get_user_by_phone(phone: str) -> User | None`, única función pública que otros
  módulos (como `auth`) pueden importar (`architecture.md`: nunca importar
  `repository.py` ajeno) (depende de T007)
- [ ] T009 [P] Crear `api/app/modules/auth/models.py` con el modelo `Session`
  (`__tablename__ = "sessions"`): `id` PK, `user_id: Mapped[int]` FK a `users.id` NOT
  NULL con índice, `token_hash: Mapped[str]` `VARCHAR(64)` UNIQUE NOT NULL,
  `created_at` `server_default=func.now()`, `last_activity_at`
  `server_default=func.now(), onupdate=func.now()`, `expires_at: Mapped[datetime]`
  NOT NULL, `revoked_at: Mapped[datetime | None]` NULL — campos exactos de
  `data-model.md`
- [ ] T010 Generar la migración Alembic `create_users_and_sessions` con
  `flask db migrate -m "ppa-2 crear users y sessions"` en `api/migrations/versions/`
  y revisarla a mano: `phone` y `token_hash` con índice único explícito, tipos
  `VARCHAR`/`DATETIME` correctos (autogenerate no siempre acierta el `UNIQUE`)
  (depende de T006, T009)
- [ ] T011 Crear `api/app/common/auth.py` con `current_user() -> User | None`
  (lee la cookie de sesión, busca por SHA-256 del token con
  `hmac.compare_digest`, valida `revoked_at IS NULL and expires_at > utcnow()`)
  y el decorador `@login_required` que devuelve `401` vía `InvalidSessionError`
  (`AppError`, código `invalid_session`) cuando `current_user()` es `None`
  (depende de T008, T009)
- [ ] T012 [P] Añadir `limiter = Limiter(key_func=get_remote_address)` a
  `api/app/extensions.py` e inicializarlo en `create_app` (`api/app/__init__.py`)
  con `app.config["RATELIMIT_ENABLED"]`
- [ ] T013 [P] Crear `api/tests/factories.py` con `UserFactory` (usa
  `hash_password` de T005; teléfonos ficticios tipo `3xxxxxxxxx` generados, nunca
  reales, RNF-06.3) para sembrar usuarios en pruebas de integración
- [ ] T014 [P] Extender `api/tests/conftest.py` (o crearlo si no existe fuera de
  módulos) con la fixture `db_session` (rollback por test) y `logged_in_client
  (user)` que llama a `auth.service.login` y adjunta la cookie resultante al
  cliente de pruebas de Flask, para que las futuras historias puedan reutilizarla
  sin repetir el flujo de login

**Checkpoint**: con esta fase lista, las tres historias de usuario pueden probarse.

---

## Phase 3: User Story 1 - Iniciar sesión con credenciales correctas (Priority: P1) 🎯 MVP

**Goal**: un usuario con cuenta existente envía teléfono y contraseña correctos y
recibe una sesión activa (FR-001).

**Independent Test**: sembrar un usuario con `UserFactory`, llamar a
`POST /api/v1/auth/login` con sus credenciales reales y verificar `200` + cookie de
sesión + que una ruta protegida de prueba acepta esa cookie después.

### Tests for User Story 1

- [ ] T015 [P] [US1] Test unitario `test_login_valid_credentials_returns_session` en
  `api/app/modules/auth/tests/unit/test_service.py`: con un repositorio de
  `accounts` falso que devuelve un `User` cuyo `password_hash` corresponde a
  "Clave1234", `auth.service.login("3009876543", "Clave1234")` devuelve un
  `Session` nuevo con `revoked_at is None` y `expires_at` ≈ `utcnow() +
  SESSION_IDLE` (HU-02 CA-1)
- [ ] T016 [P] [US1] Test de integración
  `test_post_login_valid_credentials_sets_session_cookie` en
  `api/app/modules/auth/tests/integration/test_routes.py`: con un usuario creado
  por `UserFactory` contra MySQL de pruebas, `POST /api/v1/auth/login` con
  teléfono/contraseña reales responde `204` sin cuerpo y con header `Set-Cookie`
  presente (HU-02 CA-1; contrato fijo en `.claude/rules/api-design.md`: éxito es
  `204` + cookie, nunca `200` con cuerpo)
- [ ] T017 [P] [US1] Test de contrato en
  `api/tests/contract/test_auth_contract.py`: la respuesta de
  `POST /api/v1/auth/login` cumple `specs/001-iniciar-sesion/contracts/auth.openapi.yaml`
  (`204` sin cuerpo en éxito, `401`/`422`/`429` como `Problem` en error)

### Implementation for User Story 1

- [ ] T018 [US1] Crear `api/app/modules/auth/repository.py` con
  `create_session(user_id: int, token_hash: str, expires_at: datetime) -> Session`
  usando `db.session.add` (sin `commit`, lo abre el servicio) (depende de T009)
- [ ] T019 [US1] Implementar `login(phone: str, password: str) -> LoginResult` en
  `api/app/modules/auth/service.py`: llama a
  `accounts_service.get_user_by_phone(phone)`, genera
  `secrets.token_urlsafe(32)`, calcula su SHA-256, abre `with db.session.begin():`
  y llama a `auth_repository.create_session(...)` con
  `expires_at = utcnow() + current_app.config["SESSION_IDLE"]`; devuelve un
  `LoginResult(session, token)` para que la ruta ponga el token en la cookie
  (depende de T008, T018; implementa FR-001)
- [ ] T020 [US1] Crear `api/app/modules/auth/schemas.py` con `LoginIn` (Pydantic:
  `phone: str` con patrón `^3[0-9]{9}$`, `password: str` `min_length=8`); sin
  schema de salida: el éxito es `204` sin cuerpo (`.claude/rules/api-design.md`),
  mensajes de validación en español nombrando el campo (`.claude/rules/api.md`)
- [ ] T021 [US1] Crear `api/app/modules/auth/routes.py` con blueprint
  `auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")` y
  `POST /login`: valida con `LoginIn`, llama a `service.login`, pone el token en
  una cookie `httponly=True, samesite="Lax", secure=app.config
  ["SESSION_COOKIE_SECURE"]` y responde `("", 204)` (depende de T019, T020)
- [ ] T022 [US1] Registrar `auth_bp` en `create_app` (`api/app/__init__.py`),
  aplicar `@limiter.limit("5 per 15 minutes", key_func=lambda: request.json.get
  ("phone", ""))` y `@limiter.limit("20 per 15 minutes")` (por IP) sobre la ruta
  de login, y registrar un `errorhandler(RateLimitExceeded)` que responda
  `problem(429, "too_many_attempts", "Demasiados intentos de inicio de sesión")`
  para que el `code` coincida con el contrato fijo de
  `.claude/rules/api-design.md` (depende de T012, T021;
  `.claude/rules/security.md`: 5 por teléfono y 20 por IP cada 15 min)
- [ ] T023 [US1] Loguear el evento `auth.login_ok` (nivel `INFO`, `extra` con
  `user_id`, sin teléfono completo: usar un helper de enmascaramiento mínimo
  inline hasta que `app/common/masking.py` exista en su propia historia) al
  final de `login()` en `api/app/modules/auth/service.py`
  (`.claude/rules/observability.md`)

**Checkpoint**: login exitoso funciona de punta a punta y es verificable solo.

---

## Phase 4: User Story 2 - Rechazar credenciales incorrectas sin revelar cuál falló (Priority: P1)

**Goal**: teléfono inexistente y contraseña incorrecta devuelven exactamente el
mismo error, y la contraseña nunca aparece en logs ni respuestas (FR-002, FR-003,
FR-004).

**Independent Test**: llamar a login con un teléfono que no existe y, por separado,
con un teléfono real y contraseña incorrecta; comparar que el código, el mensaje y
el `status` son idénticos en ambos, y que ninguno crea una `Session`.

### Tests for User Story 2

- [ ] T024 [P] [US2] Test unitario
  `test_login_unknown_phone_raises_invalid_credentials` en
  `api/app/modules/auth/tests/unit/test_service.py`: con el repositorio falso de
  `accounts` devolviendo `None`, `auth.service.login` lanza
  `InvalidCredentialsError` (HU-02 CA-2, CA-3)
- [ ] T025 [P] [US2] Test unitario
  `test_login_wrong_password_raises_same_invalid_credentials_error` en el mismo
  archivo: con un `User` real pero contraseña distinta, lanza la misma
  `InvalidCredentialsError` con el mismo `code` que T024 (HU-02 CA-2, CA-3)
- [ ] T026 [P] [US2] Test unitario
  `test_login_never_logs_or_raises_with_raw_password` en el mismo archivo: usando
  `caplog`/un logger de prueba, verifica que ningún registro ni la excepción
  contienen la contraseña enviada, en ningún de los dos casos anteriores (HU-02
  CA-4, RNF-06.4)
- [ ] T027 [P] [US2] Test de integración
  `test_post_login_unknown_phone_and_wrong_password_return_identical_body` en
  `api/app/modules/auth/tests/integration/test_routes.py`: dos llamadas a
  `POST /api/v1/auth/login` (teléfono inexistente; teléfono real + contraseña
  incorrecta) responden `401` con el mismo `code` (`invalid_credentials`) y
  ninguna crea fila en `sessions` (HU-02 CA-2, CA-3)

### Implementation for User Story 2

- [ ] T028 [US2] Añadir `InvalidCredentialsError(AppError)` (`status = 401`,
  `code = "invalid_credentials"`, `title` genérico sin mencionar teléfono o
  contraseña) en `api/app/modules/auth/service.py` o `api/app/common/errors.py`
  si se reutiliza en otra historia (sufijo `Error`, regla N818 de Ruff)
- [ ] T029 [US2] En `login()` (`api/app/modules/auth/service.py`), calcular un
  hash señuelo constante al importar el módulo
  (`_DECOY_HASH = PasswordHasher().hash(secrets.token_urlsafe(16))`) y, cuando
  `get_user_by_phone` devuelve `None`, verificar la contraseña recibida contra
  `_DECOY_HASH` igual que si el usuario existiera, para que el tiempo de
  respuesta no delate la diferencia (RNF-01.5); en cualquier caso de fallo,
  lanzar `InvalidCredentialsError()` sin `detail` que incluya el teléfono o la
  contraseña (depende de T005, T028)
- [ ] T030 [US2] Verificar en `login()` que ninguna llamada a `log.info`/
  `log.warning` incluya `password` ni `phone` sin enmascarar; el evento de
  rechazo se loguea como `auth.login_failed` sin el motivo exacto (CA-3,
  `.claude/rules/observability.md`: "sin decir por qué")

**Checkpoint**: credenciales inválidas rechazadas de forma indistinguible, sin
exponer la contraseña.

---

## Phase 5: User Story 3 - Impedir el acceso a funciones privadas sin sesión válida (Priority: P1)

**Goal**: sin sesión, con una sesión revocada o con una ya vencida, ninguna ruta
protegida con `@login_required` se ejecuta, y los tres casos son indistinguibles
en la respuesta (FR-005, FR-006). `POST /auth/logout` es HU-03 y no se construye
aquí: la revocación se simula escribiendo `revoked_at` directamente en la fila de
prueba.

**Independent Test**: llamar a una ruta protegida de prueba sin cookie → `401`;
hacer login y luego marcar esa `Session` como revocada en la base de datos de
prueba → la misma cookie vuelve a dar `401`.

### Tests for User Story 3

- [ ] T031 [P] [US3] Test unitario `test_current_user_without_cookie_returns_none`
  en `api/app/modules/auth/tests/unit/test_service.py` (o un nuevo
  `test_decorator.py`): sin cookie de sesión en el contexto de petición,
  `current_user()` devuelve `None` (FR-005)
- [ ] T032 [P] [US3] Test unitario `test_current_user_with_revoked_session_returns_none`
  en el mismo archivo: una `Session` con `revoked_at` ya asignado hace que
  `current_user()` devuelva `None` aunque el token sea válido (FR-005, HU-02 US3
  escenario 2)
- [ ] T033 [P] [US3] Test de integración en
  `api/app/modules/auth/tests/integration/test_routes.py`: registra en el mismo
  archivo de prueba una ruta mínima `GET /api/v1/auth/_private_probe` decorada
  con `@login_required` (solo para esta prueba, hasta que exista una función
  privada real como `GET /wallet` en HU-05) y verifica: sin cookie → `401`; con
  cookie de un login reciente → `200` (FR-005)
- [ ] T034 [P] [US3] Test de integración
  `test_revoked_session_blocks_further_access_like_no_session` en el mismo
  archivo: login → en la prueba, actualizar directamente la fila `sessions`
  (`revoked_at = utcnow()`) → una llamada posterior a la ruta protegida de
  prueba con la misma cookie responde `401`, con el mismo cuerpo que sin cookie
  (FR-005, FR-006)
- [ ] T035 [P] [US3] Test unitario
  `test_current_user_with_expired_session_returns_none` en
  `api/app/modules/auth/tests/unit/test_service.py`: una `Session` con
  `expires_at` en el pasado hace que `get_current_session` devuelva `None`
  aunque `revoked_at` sea `NULL` (FR-005, FR-006)

### Implementation for User Story 3

- [ ] T036 [US3] Verificar que `api/app/modules/auth/service.py`
  (`get_current_session`) y `api/app/common/auth.py` (`current_user()`) tratan
  "no existe sesión", `revoked_at IS NOT NULL` y `expires_at <= utcnow()` como
  el mismo resultado `None`/`401`, sin exponer cuál de los tres ocurrió (ya
  implementado en T011/T019 de Foundational y US1; esta tarea es la
  verificación final con los tests T031-T035)

**Checkpoint**: las tres historias de HU-02 funcionan juntas: login, rechazo
uniforme de credenciales inválidas, y puerta de acceso real sin distinguir
ausencia, revocación o expiración de sesión. `POST /auth/logout` queda para
HU-03.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: contrato completo, documentación mínima y la primera pantalla de la
webapp (login), que consume lo construido en las fases anteriores.

- [ ] T039 [P] Crear `api/openapi.yaml` como fuente de verdad de la API (no existía
  aún) a partir de `specs/001-iniciar-sesion/contracts/auth.openapi.yaml`, dejando
  la estructura lista para que futuras historias añadan sus propios `paths`
- [ ] T040 Ejecutar `api/tests/contract/test_auth_contract.py` con `schemathesis`
  apuntando a `api/openapi.yaml` (no solo al fragmento de `specs/`) y corregir
  cualquier respuesta fuera de contrato
- [ ] T041 [P] Crear `webapp/src/features/auth/api.ts`: tipos `LoginRequest`/
  `LoginResponse` y `login(phone, password)` que llama a
  `POST /api/v1/auth/login` vía `webapp/src/shared/api/client.ts`, con
  `X-Requested-With: fetch`
- [ ] T042 [P] Crear `webapp/src/features/auth/useLogin.ts`: hook de TanStack
  Query (`useMutation`) que llama a `api.ts#login` y traduce un `401
  invalid_credentials` a un mensaje único (reutiliza
  `webapp/src/shared/api/problem.ts`)
- [ ] T043 [US1][US2] Crear `webapp/src/features/auth/LoginPage.tsx` siguiendo el
  diseño de `Main.dc.html` del artifact de diseño (layout de dos columnas,
  paleta `--ink`/`--teal`/`--ground`, campos teléfono/contraseña, mensaje de
  error único bajo el formulario, componentes Ionic React ya adoptados en
  PPA-26): usa `useLogin`, sin lógica de negocio en el componente (solo
  feedback), la decisión final de aceptar/rechazar es siempre del servidor
- [ ] T044 [P] Test unitario `webapp/src/features/auth/__tests__/LoginPage.test.tsx`
  con Testing Library + MSW: envío válido navega/muestra éxito; envío con
  credenciales inválidas (mockeadas como `401`) muestra el mismo mensaje sin
  distinguir teléfono de contraseña
- [ ] T045 Spec Playwright `webapp/e2e/hu-02-iniciar-sesion.spec.ts`: camino
  exitoso (login → la UI refleja la sesión concedida) y camino rechazado
  (credenciales inválidas → mensaje genérico, sin distinguir cuál falló), en
  `desktop-chromium` y `mobile-chromium`, con verificación de accesibilidad
  (`axe`) sin violaciones `serious`/`critical`; no prueba logout (HU-03)
- [ ] T046 Ejecutar `cd api && ruff format . && ruff check . && mypy app && pytest`
  y `cd webapp && npm run lint && npm run typecheck && npm run test` (ver
  `.claude/rules/git-workflow.md`, "Antes de hacer push") y confirmar cobertura
  de `api` ≥ 90 %
- [ ] T047 Ejecutar `specs/001-iniciar-sesion/quickstart.md` paso a paso contra un
  entorno local (`docker compose up -d mysql && flask db upgrade`) para validar
  manualmente los tres escenarios de usuario

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias.
- **Foundational (Phase 2)**: depende de Setup — bloquea las tres historias.
- **User Stories (Phase 3, 4, 5)**: dependen de Foundational. US1 (login) es
  prerrequisito práctico de US2 y US3 porque ambas reutilizan `login()`
  internamente (US2 en sus tests negativos, US3 en su test de logout), aunque sus
  tareas de implementación son archivos distintos y pueden avanzar en paralelo
  una vez existen T018-T021.
- **Polish (Phase 6)**: depende de que US1, US2 y US3 estén completas (la UI de
  login necesita el contrato final y el comportamiento de error uniforme).

### Parallel Opportunities

- T002, T003, T004 en paralelo (Setup).
- T005, T006, T009, T012, T013, T014 en paralelo (Foundational, archivos distintos).
- T015, T016, T017 en paralelo (tests de US1, antes de implementar).
- T024, T025, T026, T027 en paralelo (tests de US2).
- T031, T032, T033, T034, T035 en paralelo (tests de US3).
- T041, T042 en paralelo; T044 puede empezar en paralelo con T043 si se escribe
  contra el diseño del componente antes de que exista (fallará primero, como
  pide el Principio III).

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Fase 1 (Setup) → Fase 2 (Foundational) → Fase 3 (US1).
2. Parar y validar: login exitoso funciona de punta a punta (sin aún el rechazo
   uniforme ni logout).
3. Esto no es desplegable solo: HU-02 exige las tres historias para considerarse
   terminada (CA-2 a CA-5), así que el "MVP" aquí es un punto de control interno,
   no una entrega parcial a producción.

### Incremental Delivery

1. Setup + Foundational.
2. US1 (login exitoso) → US2 (rechazo uniforme) → US3 (puerta de acceso + logout)
   → Polish (contrato, webapp, e2e).
3. Cada fase deja el árbol verde (`pytest`, `npm run test`) antes de pasar a la
   siguiente, por commit, según `.claude/rules/git-workflow.md`.
