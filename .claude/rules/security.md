# Seguridad y privacidad

Aplica a todo el repositorio. Cubre RNF-01 (seguridad) y RNF-06 (privacidad). Cada regla
cita su origen; si una regla no tiene origen en la especificación, es una práctica OWASP
que el equipo adoptó. Decisiones de sesión en ADR-0004.

## Autenticación y sesión

- Contraseñas con Argon2id vía `argon2-cffi` (`PasswordHasher()` por defecto). Nunca
  `hashlib`, nunca texto plano, nunca en logs ni en respuestas (HU-01 CA-6, RNF-01.2).
- Política de contraseña: mínimo 8 caracteres, al menos una letra y un dígito (HU-01
  CA-5). Se valida en `schemas.py` y, por consistencia, en el formulario.
- Login por teléfono y contraseña. Ante fallo, siempre el mismo mensaje y el mismo código
  `invalid_credentials`, y el mismo tiempo de respuesta aproximado (se ejecuta el hash
  aunque el teléfono no exista) para no revelar qué credencial falló (HU-02 CA-3,
  RNF-01.5).
- Rate limit en `POST /auth/login`: 5 intentos por teléfono y 20 por IP cada 15 minutos
  con `Flask-Limiter`; exceso responde `429`.
- Sesión del lado del servidor, cookie `HttpOnly; SameSite=Lax; Secure` (en producción),
  expiración deslizante de 5 minutos, revocación real en logout (RNF-01.3, HU-03, HU-04).
  El identificador se guarda hasheado; comparar con `hmac.compare_digest`.
- Toda mutación exige `X-Requested-With: fetch` (defensa CSRF complementaria).

## Autorización y titularidad

- Todo endpoint privado usa `@login_required`; la lista de rutas públicas es exactamente
  `POST /accounts`, `POST /auth/login` y `GET /health` (RNF-01.1, HU-02 CA-5). `/health`
  no expone datos ni configuración.
- El id del usuario sale siempre de la sesión, nunca del cuerpo ni de la URL. No existen
  rutas `/users/{id}/wallet`: son `/wallet`, `/profile`, `/movements` del usuario
  autenticado (HU-05 CA-4, RNF-06.1).
- El servidor revalida en cada operación: sesión, destinatario, monto, límites,
  titularidad y saldo, aunque el cliente ya lo haya validado (HU-07 CA-2, RNF-01.4).

## Validación de entrada

- Toda entrada pasa por un schema Pydantic antes de tocar el servicio. Sin
  `request.get_json()` suelto en servicios.
- SQL solo a través de SQLAlchemy con parámetros; prohibido `text()` con f-strings. Para
  columnas dinámicas (orden del historial) se usa una lista blanca fija.
- Tamaño máximo de cuerpo 16 KB (`MAX_CONTENT_LENGTH`); el prototipo no sube archivos.

## Privacidad y datos personales (RNF-06)

- Los datos de terceros salen enmascarados desde el servidor con `app/common/masking.py`
  (HU-06 CA-7, HU-09 CA-3). La webapp nunca recibe el dato completo.
- Logs: nunca `password`, `password_hash`, cookie de sesión, `Idempotency-Key` completa
  ni teléfonos completos. `mask_phone` es obligatorio al loguear un teléfono; `national_id`
  no se loguea nunca (RNF-06.2, RNF-06.4).
- Mensajes de error sin datos de otra cuenta y sin valores enviados por el usuario.
- Datos de prueba y de demostración ficticios: generados por factories, nunca copiados
  de personas reales (RNF-06.3).

## Secretos y configuración

- Secretos solo en variables de entorno (`SECRET_KEY`, `DATABASE_URL`). En el repo
  únicamente `api/.env.example` con valores de ejemplo inválidos. `.env` está en
  `.gitignore`; antes de cada push se corre `gitleaks git .` en local.
- Si un secreto llega a un commit: rotarlo primero, limpiar la historia después, avisar
  al equipo. Borrar el commit no lo des-filtra.
- `DEBUG=False` y `TESTING=False` en producción; el manejador `500` nunca devuelve stack
  traces.

## Cabeceras y transporte

- Producción detrás de HTTPS. Cabeceras fijas en `create_app`: `Content-Security-Policy:
  default-src 'self'`, `X-Content-Type-Options: nosniff`, `Referrer-Policy:
  strict-origin-when-cross-origin`, `X-Frame-Options: DENY`.
- CORS: deshabilitado. Webapp y API se sirven desde el mismo origen (Vite proxy en
  local, mismo proxy en producción). Si alguna vez hiciera falta, lista blanca de origen
  exacto, nunca `*` con credenciales.

## Qué revisa el revisor en un PR que toca seguridad

- Rutas nuevas con `@login_required` salvo las dos públicas.
- El id de usuario sale de la sesión, no de la petición.
- Entrada validada por schema; sin SQL concatenado.
- Respuestas y logs sin contraseñas, cookies, cédulas ni teléfonos completos ajenos.
- Datos de terceros enmascarados en servidor.
- Ningún secreto nuevo en el repo; `.env.example` actualizado si hay variable nueva.
- Mutaciones exigen `X-Requested-With`; transferencias y recargas exigen
  `Idempotency-Key`.
