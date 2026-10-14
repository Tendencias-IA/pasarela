# Research: Iniciar sesión (HU-02)

Sin tecnología por decidir: el stack está fijado por `AGENTS.md` y
`.claude/rules/api.md`. Las únicas decisiones son qué dependencias nuevas añadir y cómo
mapear las reglas de `.claude/rules/security.md` al código.

## Hash de contraseña

- **Decision**: `argon2-cffi`, `PasswordHasher()` con sus parámetros por defecto, para
  hashear al crear el usuario de prueba y para verificar en login.
- **Rationale**: Exigido explícitamente por RNF-01.2 y `.claude/rules/security.md`;
  `argon2-cffi` ya está en la lista de dependencias permitidas en `.claude/rules/api.md`.
- **Alternatives considered**: `hashlib` con PBKDF2/SHA — rechazado, la regla de
  seguridad lo prohíbe explícitamente ("Nunca `hashlib`").

## Mismo error para teléfono inexistente y contraseña incorrecta

- **Decision**: `auth.service.login` siempre ejecuta una verificación de hash, incluso
  cuando el teléfono no existe, contra un hash "señuelo" constante
  (`PasswordHasher().hash(" ")` calculado una vez al importar el módulo), y siempre
  lanza la misma excepción `InvalidCredentialsError` (código `invalid_credentials`,
  mensaje genérico) en ambos casos.
- **Rationale**: HU-02 CA-3 y RNF-01.5 exigen que el tiempo de respuesta y el mensaje no
  revelen cuál credencial falló; verificar siempre un hash evita el atajo de responder
  antes cuando el teléfono no existe.
- **Alternatives considered**: comparar solo si el usuario existe y devolver el mismo
  mensaje — rechazado porque el tiempo de respuesta sí revelaría la diferencia (sin
  hash real que verificar, la rama "no existe" sería mucho más rápida).

## Límite de intentos (rate limit)

- **Decision**: `flask-limiter` en `POST /auth/login`, 5 intentos por teléfono y 20 por
  IP cada 15 minutos, como ya especifica `.claude/rules/security.md`. Se añade
  `Limiter` a `app/extensions.py` e se inicializa en `create_app`, deshabilitado en
  `testing`/`e2e` (`RATELIMIT_ENABLED=False`, ya presente en `app/config.py`).
- **Rationale**: Mitiga fuerza bruta sobre contraseñas; ya está en la lista de
  dependencias permitidas.
- **Alternatives considered**: límite manual con una tabla propia — rechazado por
  simplicidad (Principio VII); `flask-limiter` ya resuelve esto sin estado adicional
  que mantener.

## Sesión del lado del servidor

- **Decision**: tabla `sessions` con un identificador aleatorio (`secrets.token_urlsafe
  (32)`) devuelto al cliente en una cookie `HttpOnly; SameSite=Lax; Secure` (sin
  `Secure` en `testing`/`e2e`, ver `app/config.py`), pero persistido en la tabla como su
  hash SHA-256; `current_user()` busca por el hash del valor de la cookie y compara con
  `hmac.compare_digest` para evitar timing attacks en la búsqueda.
- **Rationale**: RNF-01.3 exige sesión server-side, no JWT ni sesión solo en el
  cliente; "se guarda hasheado" y "comparar con `hmac.compare_digest`" están explícitos
  en `.claude/rules/security.md`.
- **Alternatives considered**: JWT firmado sin estado en servidor — rechazado porque no
  permite revocación real en logout (RNF-01.3, HU-04), que es un requisito explícito.

## Alcance de `users` en esta historia

- **Decision**: el modelo `User` de esta historia solo declara lo que HU-02 necesita
  leer: `id`, `phone` (único), `password_hash`, `created_at`, `updated_at`. Los campos
  de HU-01 (`full_name`, `national_id`, `email`) se añaden en la historia de registro
  con su propia migración que extiende la tabla.
- **Rationale**: Principio VII (simplicidad): no se adelantan columnas que ninguna
  prueba de esta historia ejercita. `architecture.md` ya reserva `users` para el módulo
  `accounts`, así que extenderla después no mueve de dueño a la tabla.
- **Alternatives considered**: crear ya la tabla completa de HU-01 — rechazado porque
  esta historia no puede probar esos campos y quedarían sin cobertura, violando el
  Principio III.
