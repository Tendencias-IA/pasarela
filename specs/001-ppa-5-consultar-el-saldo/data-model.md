# Data Model: Consultar el saldo

## Wallet

Representa la billetera digital de una cuenta. Es propiedad exclusiva del módulo `wallet`
y ya existe desde HU-08, mediante la migración `0002_wallet_tables`.

| Campo | Tipo persistido | Reglas |
| --- | --- | --- |
| `id` | entero grande | Identificador primario. |
| `user_id` | entero grande | Clave foránea a `users.id`, obligatoria y única: una billetera por usuario. |
| `balance` | `DECIMAL(15,2)` | Obligatorio, saldo inicial `0.00`, nunca negativo. Se maneja como `Decimal` y se expone como cadena decimal. |
| `created_at` | fecha/hora UTC | Obligatorio; creado junto con la billetera. |
| `updated_at` | fecha/hora UTC | Obligatorio; cambia al modificar el saldo en historias posteriores. |

## Relationships

- Una cuenta (`users`) tiene cero o una billetera (`wallets`). Cero es un estado posible
  para soportar HU-05 CA-5.
- Una billetera pertenece a exactamente una cuenta y no es compartida.
- HU-05 es de solo lectura. HU-07 y HU-08 actualizarán `balance` bajo sus propias reglas
  de transacción y bloqueo.

## Validation and lifecycle

- El usuario autenticado nunca selecciona una billetera mediante un valor enviado por el
  cliente; se obtiene por su `user_id` de sesión.
- Una billetera ausente produce `wallet_not_found`, sin crear ni modificar datos.
- `wallet.service.create_wallet(user_id)` ya prepara la creación con `0.00` para HU-01;
  esta historia no altera ese flujo ni convierte una consulta en creación automática.

