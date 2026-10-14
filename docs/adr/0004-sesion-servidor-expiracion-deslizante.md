# ADR-0004: Sesión del lado del servidor con expiración deslizante de cinco minutos

**Estado**: Aceptada
**Fecha**: 2026-10-13
**Ticket**: PPA-17

## Contexto

RNF-01.3 y HU-04 exigen que la sesión expire tras cinco minutos sin actividad y que la
actividad válida reinicie el contador. HU-03 CA-3 exige que una sesión cerrada no pueda
reutilizarse "mediante navegación hacia atrás, recarga de página o repetición de una
solicitud anterior". Un JWT sin estado no puede cumplir esto: sigue siendo válido hasta
su `exp` aunque el usuario haya cerrado sesión.

## Decisión

- Tabla `sessions` con un identificador aleatorio de 256 bits generado con
  `secrets.token_urlsafe(32)`; en la base de datos se guarda su hash SHA-256, nunca el
  valor en claro.
- El identificador viaja en una cookie `session` con `HttpOnly`, `SameSite=Lax`,
  `Secure` en producción y sin `Max-Age` (cookie de sesión del navegador).
- Cada petición autenticada verifica `revoked_at IS NULL` y `last_activity_at + 5 min >
  now()`, y actualiza `last_activity_at`. Si expiró, responde `401` y marca la sesión
  como revocada.
- `POST /auth/logout` marca `revoked_at` y borra la cookie. Repetir una petición antigua
  con la misma cookie responde `401`.
- La webapp mantiene un temporizador de inactividad solo para avisar y redirigir al
  login; la decisión siempre es del servidor.
- Como la webapp se sirve desde el mismo origen que la API (o detrás del mismo proxy),
  `SameSite=Lax` mitiga CSRF; además, todas las mutaciones requieren cabecera
  `X-Requested-With: fetch`, que un formulario cross-site no puede enviar.

## Alternativas consideradas

- **JWT en `Authorization: Bearer`**: sin estado y popular, pero no permite invalidación
  real ni expiración deslizante sin una lista de revocación, que es exactamente la tabla
  que estamos creando.
- **Flask-Login con cookie firmada**: cumple el cierre voluntario pero no la expiración
  deslizante verificable en servidor ni la revocación tras repetir una solicitud antigua.

## Consecuencias

- Una consulta adicional por petición autenticada; aceptable para 20 usuarios
  concurrentes. Índice en `sessions(id)`.
- Un job o la propia verificación limpia sesiones expiradas; no hace falta cron en el
  prototipo.
