# Observabilidad

Aplica a `api/`. Objetivo: poder verificar RNF-02 (rendimiento) y diagnosticar un
rechazo o un error sin acceder a datos personales (RNF-06).

## Logs estructurados

- Un solo logger configurado en `app/common/logging.py` con `python-json-logger`. Nunca
  `print`. Nivel por `LOG_LEVEL` (`INFO` en producción, `DEBUG` en local).
- Cada línea es un JSON con, como mínimo: `timestamp`, `level`, `logger`, `message`,
  `request_id`, `method`, `path`, `status`, `duration_ms`, `user_id` (si hay sesión) y
  `module` (nombre del módulo de negocio).
- `request_id`: se toma de la cabecera `X-Request-Id` si viene, si no se genera
  (`uuid4().hex[:12]`), se devuelve en la respuesta y se incluye en los errores RFC 9457.
  Razón: un usuario reporta "me rechazó la transferencia" con el id y se encuentra la
  línea exacta.
- Eventos de negocio con nombre fijo y `extra` estructurado, no texto libre:

```python
# Correcto
log.info("transfer.rejected", extra={"reason": "insufficient_balance", "amount": str(amount),
                                     "recipient_phone": mask_phone(phone)})
```

```python
# Incorrecto
print(f"Transferencia de {user.phone} a {phone} por {amount} rechazada: saldo {wallet.balance}")
```

Diferencia: la segunda expone dos teléfonos completos y el saldo, y no se puede filtrar
por campo.

- Eventos obligatorios: `account.registered`, `auth.login_ok`, `auth.login_failed`
  (sin decir por qué), `auth.session_expired`, `auth.logout`, `recharge.applied`,
  `transfer.applied`, `transfer.rejected`, `idempotency.replayed`, `profile.updated`
  (campo cambiado, no valor).
- Prohibido en logs: contraseñas y hashes, cookie de sesión, `national_id`, teléfonos
  completos de terceros, cuerpos completos de petición o respuesta (RNF-06.2, RNF-06.4).

## Métricas de latencia (RNF-02)

- Middleware en `create_app` mide `duration_ms` por petición y lo escribe en el log de
  acceso. Es la fuente para calcular p95 por endpoint con una consulta sobre los logs o
  con el reporte de Locust.
- Umbrales a verificar en el job nocturno de carga: p95 ≤ 2000 ms en `GET /api/v1/wallet`;
  p95 ≤ 3000 ms en `GET /api/v1/movements`, `POST /api/v1/transfers` y
  `POST /api/v1/wallet/recharges`, con 20 usuarios concurrentes.
- Si una petición supera 3000 ms se loguea en `WARNING` con evento `request.slow`.

## Health check

- `GET /health` público, sin sesión, responde `200 {"status": "ok", "db": "ok"}` si
  `SELECT 1` funciona y `503` si no. No expone versiones ni configuración.

## Errores

- `500` inesperados: el manejador global registra `ERROR` con stack trace y
  `request_id`, y responde un `problem` genérico. Nunca se traga una excepción con
  `except Exception: pass`.
- Errores de negocio (`AppError`) se registran en `INFO` con su `code`; no son errores
  del sistema.

## Local

- `docker compose --profile app up` levanta MySQL, la API y la webapp; los logs JSON se
  ven con `docker compose logs -f api | jq` (ver `docker.md`). No se añade stack de observabilidad (Prometheus, Grafana) al
  prototipo; los logs estructurados son suficientes para el alcance.
