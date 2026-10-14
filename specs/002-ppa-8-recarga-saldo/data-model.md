# Data Model: Recarga simulada de saldo (HU-08)

Tres tablas nuevas, en una sola migración Alembic `0002_wallets_transactions_idempotency`
(encadenada a `0001_create_users_and_sessions` de HU-02).
Tipos MySQL 8 / InnoDB, `utf8mb4`. Fechas en UTC (`DATETIME(6)`, `server_default now()`).

## `wallets` (módulo `wallet`, modelo `app/modules/wallet/models.py`)

| Columna | Tipo | Restricciones | Notas |
| --- | --- | --- | --- |
| `id` | BIGINT | PK, autoincrement | |
| `user_id` | BIGINT | NOT NULL, UNIQUE, FK → users.id | `users` la creó HU-02 (migración 0001) |
| `balance` | DECIMAL(15,2) | NOT NULL, DEFAULT 0.00, CHECK `balance >= 0` | Sin tope (FR-008) |
| `created_at` | DATETIME(6) | NOT NULL, default now | |
| `updated_at` | DATETIME(6) | NOT NULL, default now, on update now | |

Invariantes: una billetera por usuario; el saldo solo cambia dentro de una transacción
que bloquea la fila (`SELECT ... FOR UPDATE`); nunca negativo.

## `transactions` (compartida, modelo `app/common/models/transaction.py`, ADR-0006)

| Columna | Tipo | Restricciones | Notas |
| --- | --- | --- | --- |
| `id` | BIGINT | PK, autoincrement | |
| `type` | ENUM('transferencia','recarga') | NOT NULL | HU-08 solo inserta `recarga` |
| `status` | ENUM('exitosa','rechazada') | NOT NULL | Inmutable tras insertar |
| `amount` | DECIMAL(15,2) | NOT NULL, CHECK `amount > 0` | |
| `sender_wallet_id` | BIGINT | NULL, FK → wallets.id | NULL en recargas |
| `receiver_wallet_id` | BIGINT | NOT NULL, FK → wallets.id | Billetera recargada |
| `rejection_reason` | VARCHAR(64) | NULL | `code` del error cuando `status = rechazada` |
| `created_at` | DATETIME(6) | NOT NULL, default now | |

Índices: `(receiver_wallet_id, created_at)`, `(sender_wallet_id, created_at)` (para HU-09).

Estados: la fila nace con su estado final. `exitosa` se inserta en la misma transacción
que actualiza `wallets.balance`; `rechazada` se inserta en una transacción posterior al
rollback, solo para rechazos de negocio con billetera existente (`amount_out_of_range`;
`wallet_not_found` no puede registrarse porque no hay billetera a la que asociarlo).

## `idempotency_keys` (compartida, modelo `app/common/models/idempotency_key.py`, ADR-0005)

| Columna | Tipo | Restricciones | Notas |
| --- | --- | --- | --- |
| `user_id` | BIGINT | PK (parte 1) | Usuario de la sesión |
| `key` | CHAR(36) | PK (parte 2) | UUID v4 enviado por el cliente |
| `request_hash` | CHAR(64) | NOT NULL | SHA-256 de método + ruta + cuerpo canónico |
| `status_code` | SMALLINT | NOT NULL | 201 o 422 |
| `response_body` | JSON | NOT NULL | Cuerpo exacto a reproducir |
| `created_at` | DATETIME(6) | NOT NULL, default now | Caducidad lógica: 24 h |

Reglas: misma `(user_id, key)` + mismo `request_hash` → replay con `Idempotent-Replayed:
true`; mismo par con distinto hash → 422 `idempotency_key_mismatch`; inserción dentro de
la misma transacción que la operación (éxito) o que el registro `rechazada` (rechazo).

## Entidades de dominio (Python, `wallet/service.py`)

- `RechargeResult(transaction_id, amount: Decimal, balance_after: Decimal, created_at)`:
  lo que devuelve `recharge(user_id, amount, idempotency)`; la ruta lo serializa con
  `RechargeOut`.
- `IdempotencyContext(key: str, request_hash: str)`: lo construye `@idempotent` y lo
  consume el repositorio al insertar la clave.
- Errores de negocio (`AppError`, con sufijo `Error`): `AmountOutOfRangeError` (422,
  `amount_out_of_range`), `WalletNotFoundError` (404, `wallet_not_found`),
  `UnauthenticatedError` (401, `unauthenticated`), `MissingIdempotencyKeyError` (400,
  `missing_idempotency_key`), `IdempotencyKeyMismatchError` (422,
  `idempotency_key_mismatch`).

## Validación de entrada (`wallet/schemas.py`)

- `RechargeIn.amount`: cadena decimal estricta, `> 0`, máximo 15 dígitos y 2 decimales.
  Rechaza números JSON, vacío, negativo, `NaN`, más de dos decimales → `422 validation`
  con `errors: [{field: "amount", message: "..."}]`.
- Rango `[5000.00, 5000000.00]` inclusive: lo valida el servicio con las constantes de
  `app/common/money.py` (es regla de negocio, se registra como `rechazada`).

## Flujo de la recarga (servicio)

1. `current_user_id()` → `user_id`.
2. `with db.session.begin()`: `lock_wallet_for_user(user_id)` (404 si no existe) →
   validar rango → `balance += amount` → `add_transaction(recarga, exitosa)` →
   `add_idempotency_key(201, body)`.
3. Si un `AppError` de negocio interrumpe el paso 2: rollback automático; segunda
   transacción con `add_transaction(recarga, rechazada, reason)` y
   `add_idempotency_key(422, problem)`; se relanza el error.
4. Respuesta `201` con `RechargeOut` (ver contrato).
