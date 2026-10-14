# Data Model: Historial de movimientos (HU-09)

Sin migración nueva: esta historia **lee** `transactions` (ADR-0006, creada en la migración
`0002_wallet_tables` de HU-08) y consulta `wallets` y `users` solo a través de los servicios
de sus módulos.

## `transactions` (compartida, `app/common/models/transaction.py`): columnas usadas

| Columna | Uso en HU-09 |
| --- | --- |
| `id` | Identificador del movimiento; desempate del orden |
| `type` | `recarga` o `transferencia` |
| `status` | `exitosa` o `rechazada`, se expone tal cual |
| `amount` | DECIMAL(15,2), se expone como cadena |
| `sender_wallet_id` | NULL en recargas; billetera del usuario → "enviada" |
| `receiver_wallet_id` | billetera del usuario → "recibida" (o la recargada) |
| `rejection_reason` | Se expone cuando `status = rechazada` |
| `created_at` | Orden `DESC`; se expone en UTC ISO 8601 |

Condición de titularidad: `sender_wallet_id = :wallet OR (receiver_wallet_id = :wallet AND
(type = 'recarga' OR status = 'exitosa'))`: quien envía ve su transferencia aunque fuera
rechazada; quien recibe solo la ve si fue exitosa; una recarga rechazada sí es del titular.
Índices existentes `(receiver_wallet_id, created_at)` y `(sender_wallet_id, created_at)`
cubren la consulta.

## Entidades de dominio (Python, `movements/service.py`)

- `Direction` (StrEnum): `recarga`, `enviada`, `recibida`.
- `Counterparty(name_masked: str | None, phone_masked: str)`: solo en transferencias;
  construida con `app/common/masking.py`.
- `Movement(id, direction, status, amount: Decimal, created_at, rejection_reason,
  counterparty)`: proyección de una fila desde la billetera del usuario.
- `MovementsPage(items: list[Movement], page: int, page_size: int = 20, total: int)`.

Reglas:

- `direction` se deriva de la fila y de la billetera del usuario (research §6).
- Si el usuario no tiene billetera: `MovementsPage([], page, 20, 0)` y log `WARNING`
  `movements.wallet_missing` (dato inconsistente; no se crea billetera).
- `page >= 1`; `offset = (page - 1) * 20`; `items` vacío si `offset >= total`.

## Contratos entre módulos (nuevos, solo `service.py`)

- `wallet_service.get_wallet_owners(wallet_ids: Iterable[int]) -> dict[int, WalletOwner]`
  con `WalletOwner(wallet_id, user_id, phone, full_name: str | None)`. Internamente usa
  `accounts_service.get_users_by_ids`.
- `accounts_service.get_users_by_ids(user_ids: Iterable[int]) -> dict[int, UserSummary]`
  con `UserSummary(id, phone, full_name: str | None)`; `full_name` queda `None` hasta que
  HU-01 añada la columna.

## Validación de entrada (`movements/schemas.py`)

- `MovementsQuery.page`: entero `>= 1`, por defecto 1, leído de la query string como
  cadena y convertido; `"0"`, `"-1"`, `"abc"`, `"1.5"` → `422 validation` con
  `errors: [{field: "page", message: "La página debe ser un entero desde 1."}]`.
  Parámetros desconocidos (`from`, `to`, `type` llegarán con HU-10) se ignoran hoy.

## Salida (`movements/schemas.py`)

- `MovementOut`: `id`, `direction`, `type`, `status`, `amount` (cadena), `created_at`
  (ISO 8601 `Z`), `rejection_reason` (nullable), `counterparty` (nullable:
  `{name_masked, phone_masked}`).
- `MovementsPageOut`: `items: MovementOut[]`, `page`, `page_size`, `total`.

## Tablas de prueba (`tests/factories.py`)

- `make_transaction(*, type_, status, amount, receiver_wallet_id, sender_wallet_id=None,
  rejection_reason=None, created_at=None)` inserta filas con `created_at` controlado para
  probar orden y paginación de forma determinista.
