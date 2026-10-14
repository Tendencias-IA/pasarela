# Data Model: Iniciar sesión (HU-02)

## User (`users`, módulo `accounts`)

Alcance de esta historia: solo los campos que `auth` necesita leer para verificar
credenciales. HU-01 extenderá esta tabla con el resto de columnas del registro.

| Columna | Tipo | Regla |
| --- | --- | --- |
| `id` | `BIGINT` PK autoincremental | |
| `phone` | `VARCHAR(10)` UNIQUE, NOT NULL | formato colombiano, 10 dígitos; la unicidad la valida HU-01 al crear, aquí solo se lee |
| `password_hash` | `VARCHAR(255)` NOT NULL | salida de Argon2id (`PasswordHasher().hash(...)`), nunca la contraseña en claro |
| `created_at` | `DATETIME` `server_default=func.now()` | |
| `updated_at` | `DATETIME` `server_default=func.now()`, `onupdate=func.now()` | |

No hay transición de estado: un `User` existe o no existe para un teléfono dado.

## Session (`sessions`, módulo `auth`)

| Columna | Tipo | Regla |
| --- | --- | --- |
| `id` | `BIGINT` PK autoincremental | |
| `user_id` | `BIGINT` FK → `users.id`, NOT NULL, índice | |
| `token_hash` | `VARCHAR(64)` UNIQUE, NOT NULL | SHA-256 hex del token aleatorio devuelto en la cookie; el token en claro nunca se persiste |
| `created_at` | `DATETIME` `server_default=func.now()` | |
| `last_activity_at` | `DATETIME` `server_default=func.now()`, `onupdate=func.now()` | base para la expiración deslizante de HU-03; esta historia la escribe pero no la vence activamente |
| `expires_at` | `DATETIME` NOT NULL | calculada como `last_activity_at + SESSION_IDLE` (5 min); HU-03 implementa el rechazo automático al vencer, aquí el campo existe para que `auth.service.get_current_user` pueda ya comparar contra `utcnow()` |
| `revoked_at` | `DATETIME` NULL | se fija en logout (HU-04); mientras sea `NULL` la sesión es potencialmente válida |

**Estados de una sesión** (derivados, no una columna de estado):

- *Activa*: `revoked_at IS NULL` y `expires_at > utcnow()`.
- *Revocada*: `revoked_at IS NOT NULL` (logout explícito).
- *Expirada*: `revoked_at IS NULL` pero `expires_at <= utcnow()`.

`current_user()` solo acepta una sesión *activa*; revocada o expirada son
indistinguibles para quien llama (FR-005): en ambos casos se rechaza igual.

## Relación

Un `User` tiene cero o muchas `Session` (inicios de sesión concurrentes permitidos; no
hay regla en la spec v1.0 que limite a una sesión por usuario). `Session.user_id` es la
única forma en que `auth` conoce al usuario: nunca importa `accounts.repository` ni
`accounts.models` (regla de `architecture.md`), solo usa
`accounts.service.get_user_by_phone` para buscar por teléfono.
