# Research: Recarga simulada de saldo (HU-08)

Fase 0 del plan. Cada punto resuelve una duda del Technical Context o fija cómo se aplica
una regla ya existente del proyecto a esta historia.

## 1. Cómo exigir sesión (actualizado: HU-02 ya está en `main`)

- **Decisión**: `api/app/common/auth.py` combina la versión de HU-02 (`current_session`,
  `current_user`, `login_required` sobre la cookie `session`) con `current_user_id() ->
  int`, que resuelve la sesión una vez por petición, cachea el id en `g.user_id` y lanza
  `InvalidSessionError` (401, code `invalid_session`) si no hay sesión válida. Los
  módulos de negocio usan solo `current_user_id()`. En pruebas unitarias el fixture
  `logged_in_client` fija `g.user_id` sin base de datos; las pruebas HTTP con MySQL
  además verifican el flujo con login real (`POST /api/v1/auth/login` y cookie).
- **Razón**: `architecture.md` ya ubica `login_required` y `current_user` en
  `app/common/auth.py`; definir solo la interfaz evita pisar el módulo `auth` y deja un
  contrato de una línea para Moisés.
- **Alternativas**: (a) implementar una sesión mínima dentro de esta HU: duplicaría HU-02 y
  generaría conflictos de merge; (b) cabecera `X-User-Id` en configuración `e2e`: abre un
  agujero si se despliega mal, rechazada por `security.md`.

## 2. Dónde vive la lógica de idempotencia

- **Decisión**: dos capas. `app/common/idempotency.py` provee (a) el decorador `@idempotent`
  para rutas: exige la cabecera `Idempotency-Key` (400 `missing_idempotency_key` si falta
  o no es UUID), calcula `request_hash = sha256(método + ruta + cuerpo canónico JSON)`,
  busca `(user_id, key)`; si existe con el mismo hash devuelve la respuesta guardada con
  `Idempotent-Replayed: true`; si existe con otro hash responde 422
  `idempotency_key_mismatch`; si no existe, deja `g.idempotency = IdempotencyContext(key,
  request_hash)` y ejecuta la vista. (b) El servicio recibe el `IdempotencyContext` y el
  repositorio inserta la fila `idempotency_keys` **dentro** de la transacción que mueve el
  saldo (éxito) o de la segunda transacción que registra el movimiento rechazado. La fila
  guarda `status_code` y `response_body` (JSON del resultado o del problem).
- **Razón**: ADR-0005 y `architecture.md` exigen que no pueda quedar operación sin clave ni
  clave sin operación; eso solo se garantiza persistiendo la clave en la misma transacción,
  y la transacción la abre el servicio, no la ruta.
- **Alternativas**: guardar la clave en el decorador después de la vista (dos
  transacciones en el éxito: una caída entre ambas permitiría acreditar dos veces).
  Rechazada.
- **Detalle**: la PK compuesta `(user_id, key)` hace que dos peticiones concurrentes con
  la misma clave compitan en el `INSERT`; la segunda falla por clave duplicada, se captura
  como `IntegrityError`, se hace rollback y se responde con el replay de la primera.

## 3. `wallets.user_id` y la tabla `users`

- **Decisión (actualizada)**: HU-02 llegó a `main` durante esta historia con la migración
  `0001_create_users_and_sessions`, así que la migración de esta HU es la `0002`,
  encadenada a esa, y ya incluye `FOREIGN KEY (user_id) REFERENCES users(id)`. Dejó de
  hacer falta la tarea de seguimiento.
- **Razón**: una sola cadena de revisiones en Alembic (dos cabezas obligarían a una
  migración de merge) e integridad referencial desde el primer día.
- **Alternativas**: dejar la FK para después (ya innecesario).

## 4. Qué se registra cuando la recarga se rechaza

- **Decisión**: siguiendo "Estados de una operación" en `architecture.md`: un monto fuera de
  rango llega a validación de negocio con sesión válida, así que se registra una
  `transaction` con `status = rechazada`, `rejection_reason = amount_out_of_range`, y se
  guarda la clave idempotente con el problem 422, ambas en una segunda transacción tras el
  rollback de la principal. Un monto no numérico, vacío, negativo o con más de dos decimales
  falla en el schema Pydantic (`422 validation`) y **no** crea registro ni clave.
- **Razón**: HU-09 muestra el estado de cada movimiento; "rechazada" solo tiene sentido
  para intentos reales. Los errores de formato no son intentos de negocio.
- **Alternativas**: no registrar rechazos (contradice CA-05.2 del documento) o registrar
  también errores de formato (ruido en el historial).

## 5. Bloqueo de la billetera en una recarga

- **Decisión**: `repository.lock_wallet_for_user(user_id)` hace `SELECT ... FOR UPDATE`
  sobre la fila de `wallets` aunque la recarga solo toque una billetera.
- **Razón**: RNF-04.2; una recarga concurrente con una transferencia (HU-07) sobre la
  misma billetera debe serializarse. Mantener el mismo patrón en ambas evita que una
  historia posterior tenga que "arreglar" esta. Coste: una fila bloqueada unos milisegundos.
- **Alternativas**: `UPDATE wallets SET balance = balance + :m` atómico sin bloqueo: válido
  para la recarga aislada, pero no deja leer el saldo previo para la respuesta ni
  compone con las transferencias.

## 6. Representación del dinero de punta a punta

- **Decisión**: entrada JSON como cadena (`"50000.00"`); Pydantic la convierte a `Decimal`
  con `condecimal(max_digits=15, decimal_places=2, gt=0)` y rechaza números JSON
  (`strict`); el servicio compara con `RECHARGE_MIN`/`RECHARGE_MAX` de
  `app/common/money.py`; SQLAlchemy `Numeric(15, 2, asdecimal=True)`; salida como cadena
  cuantizada a dos decimales. En la webapp el monto se captura como texto,
  `parseAmountInput` normaliza separadores y valida `≤ 2` decimales; nunca `Number` para
  decidir.
- **Razón**: ADR-0003 y RNF-04.3.

## 7. Cómo probar el camino exitoso en navegador (actualizado)

- **Decisión**: con la `LoginPage` de HU-02 en `main`, el spec de Playwright inicia
  sesión con el usuario que crea `api/scripts/seed_test_user.py` (que ahora también crea
  su billetera, mientras no exista el registro de HU-01), recarga y verifica el resultado.
  El job E2E del CI ejecuta la semilla tras las migraciones.
- **Razón**: ya hay una forma legítima de iniciar sesión; `security.md` sigue prohibiendo
  atajos de autenticación.

## 8. Enrutamiento en la webapp

- **Decisión**: introducir `IonReactRouter` + `IonRouterOutlet` con rutas `/` (pantalla
  actual de estado) y `/recargar` (`RechargePage`). Navegación desde la pantalla principal
  con un `IonButton routerLink="/recargar"`: dos clics hasta confirmar (RNF-03.1).
- **Razón**: ADR-0007 fija react-router-dom 6 con Ionic; es la primera pantalla real.
- **Alternativas**: renderizar la recarga en la misma pantalla (sin ruta): rompe el patrón
  de páginas que usarán HU-05/09.

## 9. Rendimiento (CA-10)

- **Decisión**: la operación es una transacción con un `SELECT FOR UPDATE`, un `UPDATE` y
  dos `INSERT`; p95 esperado muy por debajo de 3 s. Se añade la tarea `POST
  /api/v1/wallet/recharges` al `locustfile.py` con autenticación simulada cuando HU-02
  exista; mientras tanto, la prueba de carga queda documentada y sin activar.
- **Razón**: RNF-02.3; el job nocturno ya verifica p95 por endpoint.
