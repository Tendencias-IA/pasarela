# Arquitectura: monolito modular con vertical slicing

Aplica a todo el código de `api/` y `webapp/`. Complementa la constitución
(principios IV y V). Decisiones de fondo en `docs/adr/`.

## Módulos y su mapa a historias

Un módulo es una capacidad de negocio completa: sus rutas, validaciones, servicio,
repositorio, modelos y pruebas viven juntos. Nunca se organiza por capa técnica global
(`controllers/`, `services/`, `models/` en la raíz).

| Módulo | Responsabilidad | Historias | Tablas propias |
| --- | --- | --- | --- |
| `accounts` | Registro, consulta y edición de perfil | HU-01, HU-11, HU-12, HU-13 | `users` |
| `auth` | Inicio y cierre de sesión, expiración por inactividad | HU-02, HU-03, HU-04 | `sessions` |
| `wallet` | Saldo y recargas | HU-05, HU-08 | `wallets` |
| `transfers` | Preparar y confirmar transferencias | HU-06, HU-07 | `transactions` (escribe) |
| `movements` | Historial y filtros | HU-09, HU-10 | `transactions` (solo lee) |

`transactions` es la única tabla compartida: la escriben `wallet` (recargas) y
`transfers`; `movements` solo la lee a través de `movements.repository`. Cualquier otra
tabla pertenece a un solo módulo.

## Estructura de carpetas del backend

```text
api/
├── app/
│   ├── __init__.py            # create_app(config) y registro de blueprints
│   ├── config.py              # clases Config por ambiente, valores desde variables de entorno
│   ├── extensions.py          # db (SQLAlchemy), migrate (Alembic), limiter
│   ├── common/                # transversal, sin reglas de negocio de un módulo
│   │   ├── errors.py          # AppError, handlers RFC 9457
│   │   ├── money.py           # parse_amount, Decimal helpers, serialización
│   │   ├── masking.py         # mask_phone, mask_name
│   │   ├── idempotency.py     # decorador @idempotent y tabla idempotency_keys
│   │   ├── auth.py            # decorador @login_required, current_user
│   │   ├── pagination.py      # Page, paginate(query, page, size=20)
│   │   └── logging.py         # JSON logger y request_id
│   └── modules/
│       ├── accounts/
│       │   ├── routes.py      # Blueprint: solo parsea, llama al servicio, serializa
│       │   ├── schemas.py     # Pydantic: entrada y salida
│       │   ├── service.py     # reglas de negocio, transacciones
│       │   ├── repository.py  # consultas SQLAlchemy de ESTE módulo
│       │   ├── models.py      # tablas de ESTE módulo
│       │   └── tests/         # unit/ e integration/ del módulo
│       ├── auth/
│       ├── wallet/
│       ├── transfers/
│       └── movements/
├── migrations/                # Alembic, una migración por cambio de esquema
├── tests/
│   ├── conftest.py            # app de pruebas, sesión de BD, factories
│   ├── contract/              # respuestas vs. openapi.yaml
│   └── e2e_api/               # flujos completos por HTTP contra MySQL
├── openapi.yaml               # contrato de la API, fuente de verdad
└── pyproject.toml
```

Frontend espejo por feature en `webapp/src/features/<modulo>/` (ver `frontend.md`).

## Capas dentro de un módulo

Tres capas, dependencia solo hacia abajo: `routes → service → repository`.

- `routes.py` no contiene reglas de negocio. Valida la forma de la entrada con el schema,
  llama a una función del servicio y serializa la respuesta. Si una ruta tiene un `if`
  sobre saldo, límites o titularidad, está en la capa equivocada.
- `service.py` contiene las reglas de negocio y abre y cierra la transacción. Recibe y
  devuelve tipos de dominio o dataclasses, nunca objetos `request`/`Response` de Flask.
  Razón: así las pruebas unitarias cubren las reglas sin levantar Flask ni MySQL, que es
  lo que hace alcanzable el 90 % de cobertura.
- `repository.py` es el único lugar con consultas SQLAlchemy del módulo. Devuelve modelos
  o tuplas, nunca `Query` abiertos, para que el servicio no construya SQL.

## Comunicación entre módulos

- Un módulo llama a otro únicamente a través de funciones públicas de su `service.py`,
  importadas como `from app.modules.wallet import service as wallet_service`.
- Prohibido importar `repository.py` o `models.py` de otro módulo. Razón: si `transfers`
  consulta `wallets` directamente, la regla de bloqueo de filas queda duplicada y un
  cambio en `wallet` rompe `transfers` en silencio.
- Las operaciones que tocan dos módulos (una transferencia toca `wallet` y escribe
  `transactions`) se orquestan en el servicio del módulo dueño del caso de uso
  (`transfers.service.confirm_transfer`), dentro de una sola transacción de BD que ese
  servicio abre. Los servicios invocados reciben la sesión activa y no hacen `commit`.

## Patrones transversales obligatorios

### Dinero

`Decimal` con `quantize(Decimal("0.01"))` en Python, `DECIMAL(15,2)` en MySQL, cadena
`"150000.00"` en JSON. Nunca `float`, nunca `int` de centavos. La validación de rangos
usa `Decimal` y los límites se definen una sola vez en `app/common/money.py`:

```python
TRANSFER_MIN, TRANSFER_MAX = Decimal("100"), Decimal("3000000")
RECHARGE_MIN, RECHARGE_MAX = Decimal("5000"), Decimal("5000000")
```

### Operación atómica con bloqueo

Toda escritura de saldo sigue este orden, sin excepción:

```python
# Correcto
with db.session.begin():
    wallets = repository.lock_wallets([sender_id, receiver_id])  # SELECT ... FOR UPDATE ORDER BY id
    sender, receiver = wallets[sender_id], wallets[receiver_id]
    if sender.balance < amount:
        raise InsufficientBalance()          # rollback automático, nada persistido
    sender.balance -= amount
    receiver.balance += amount
    repository.add_transaction(...status="exitosa")
```

```python
# Incorrecto
sender = repository.get_wallet(sender_id)      # lectura sin bloqueo
if sender.balance >= amount:                   # otra petición puede pasar aquí a la vez
    sender.balance -= amount
    db.session.commit()
```

Diferencia: el bloqueo en orden ascendente de id evita deadlocks y garantiza que dos
transferencias simultáneas no gasten el mismo saldo (RNF-04.2, HU-07 CA-9).

### Idempotencia

`POST /transfers` y `POST /wallet/recharges` exigen cabecera `Idempotency-Key` (UUID v4
generado por el cliente). Se persiste en `idempotency_keys(user_id, key, request_hash,
status_code, response_body)` dentro de la misma transacción que la operación. Reintento
con la misma clave y el mismo cuerpo devuelve la respuesta guardada sin ejecutar nada;
misma clave con cuerpo distinto responde `422`. Razón: un doble clic o un reintento de
red no puede acreditar dos veces (RNF-04.4).

### Estados de una operación

Una `transaction` nace y muere en la misma transacción de BD con `status` en
`{"exitosa", "rechazada"}`. No existen estados `pendiente` ni `en_proceso`: "preparar
transferencia" (HU-06) es una consulta pura que no escribe nada. Una operación
`rechazada` se registra solo si llegó a validaciones de negocio con sesión válida; los
errores de formato no crean registros.

### Enmascaramiento

Los datos de un tercero (destinatario, emisor) salen del servidor ya enmascarados vía
`app/common/masking.py`: nombre con iniciales (`"Mar** G****"`) y teléfono con últimos
cuatro dígitos (`"***4567"`). El frontend nunca recibe el dato completo para ocultarlo
él. Razón: RNF-06 y HU-06 CA-7, y porque lo que llega al navegador es público.

## Modelo de datos de referencia

| Tabla | Columnas clave | Notas |
| --- | --- | --- |
| `users` | `id`, `full_name`, `phone` UNIQUE, `national_id` UNIQUE, `email` UNIQUE, `password_hash`, `created_at`, `updated_at` | `national_id` no tiene endpoint de edición |
| `wallets` | `id`, `user_id` UNIQUE FK, `balance DECIMAL(15,2)` CHECK ≥ 0, `updated_at` | Una por usuario, creada en el registro |
| `sessions` | `id` (token aleatorio hasheado), `user_id` FK, `created_at`, `last_activity_at`, `expires_at`, `revoked_at` | Expiración deslizante de 5 min |
| `transactions` | `id`, `type` ENUM(`transferencia`,`recarga`), `status` ENUM(`exitosa`,`rechazada`), `amount DECIMAL(15,2)`, `sender_wallet_id` FK NULL, `receiver_wallet_id` FK, `rejection_reason`, `created_at` | Índices por `(sender_wallet_id, created_at)` y `(receiver_wallet_id, created_at)` |
| `idempotency_keys` | `user_id`, `key`, `request_hash`, `status_code`, `response_body`, `created_at` | PK compuesta `(user_id, key)` |

El historial (HU-09) deriva "enviada" o "recibida" según si la billetera del usuario es
`sender` o `receiver`; no se duplican filas por participante.

## Qué no hacer

- No crear `core/`, `domain/`, `ports/`, `adapters/` ni interfaces abstractas de
  repositorio. ADR-0001 explica por qué se rechazó hexagonal.
- No añadir colas, eventos, caché ni servicios externos. No hay PSP real (alcance).
- No compartir modelos SQLAlchemy entre módulos: `transactions` se expone a `movements`
  mediante consultas de solo lectura en `movements/repository.py`, no importando el modelo
  de `transfers`. Si hace falta el mismo modelo en dos módulos, va en `app/common/models/`
  con un ADR.
- No poner reglas de negocio en el frontend como única validación: el frontend valida para
  dar feedback inmediato, el backend valida para decidir (RNF-01.4).
