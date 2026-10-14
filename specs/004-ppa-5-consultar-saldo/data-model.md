# Data Model: Consultar el saldo (HU-05)

Sin migración nueva: esta historia **lee** `wallets` (creada en `0002_wallet_tables` por
HU-08) a través del repositorio del módulo `wallet`.

## `wallets` (módulo `wallet`, `app/modules/wallet/models.py`): columnas usadas

| Columna | Tipo | Uso en HU-05 |
| --- | --- | --- |
| `id` | BIGINT | No se expone (api-design.md: no se devuelven ids de billetera) |
| `user_id` | BIGINT UNIQUE FK `users.id` | Condición de titularidad: `WHERE user_id = :session_user` |
| `balance` | DECIMAL(15,2) CHECK ≥ 0 | Se lee como `Decimal` y se expone como cadena `"150000.00"` |
| `updated_at` | DATETIME | No se expone |

## Relaciones

- Una cuenta tiene cero o una billetera. Cero es posible (dato inconsistente) y es el
  flujo alternativo de CA-5: `404 wallet_not_found` + `WARNING wallet.missing`.
- HU-05 es de solo lectura; HU-07 y HU-08 actualizan `balance` bajo bloqueo
  `FOR UPDATE` en sus propias transacciones. La lectura de HU-05 no toma bloqueos.

## Entidades de dominio y contrato

- Servicio: `get_balance(user_id: int, repo=default_repository) -> Decimal`. Sin
  dataclass intermedia: un solo valor.
- Salida: `WalletOut(balance: str)` construida con `WalletOut.from_balance(Decimal)` →
  `{"balance": to_json(balance)}`.
- Webapp: `WalletOut` generado en `types.gen.ts`; `useWallet()` expone
  `data.balance` (cadena) que `formatCOP` convierte en `$ 150.000,00`.

## Clave de caché en la webapp

`["wallet"]` (`WALLET_QUERY_KEY`). La invalidan `useRecharge` (HU-08) y, cuando exista,
la confirmación de transferencia (HU-07).
