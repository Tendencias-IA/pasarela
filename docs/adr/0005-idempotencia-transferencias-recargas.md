# ADR-0005: Idempotencia por `Idempotency-Key` en transferencias y recargas

**Estado**: Aceptada
**Fecha**: 2026-10-13
**Ticket**: PPA-17

## Contexto

HU-07 CA-8, HU-08 CA-6 y RNF-04.4 exigen que "una misma solicitud" de transferencia o
recarga no se aplique más de una vez. Un doble clic en Confirmar, un reintento del
navegador tras un timeout o una recarga de página pueden reenviar el mismo `POST`.

## Decisión

- `POST /api/v1/transfers` y `POST /api/v1/wallet/recharges` exigen la cabecera
  `Idempotency-Key` con un UUID v4 generado por el cliente al mostrar el resumen de
  confirmación (no al hacer clic, para que el doble clic reutilice la misma clave).
  Sin cabecera: `400`.
- Tabla `idempotency_keys (user_id, key, request_hash, status_code, response_body,
  created_at)` con PK `(user_id, key)`. El `request_hash` es SHA-256 del cuerpo
  canonizado.
- Flujo en `app/common/idempotency.py` (decorador `@idempotent`): si existe la clave
  con el mismo hash, se devuelve la respuesta guardada con cabecera
  `Idempotent-Replayed: true`; si existe con otro hash, `422`; si no existe, se ejecuta la
  operación. En una operación exitosa la clave se guarda **en la misma transacción** que
  el movimiento de saldo, para que no pueda quedar la operación sin la clave ni la clave
  sin la operación.
- Las respuestas de rechazo de negocio (`422` por saldo insuficiente, etc.) también se
  guardan, para que el reintento reciba el mismo resultado. Como el rechazo hace rollback
  de la transacción principal, la clave y el movimiento `rechazada` se escriben juntos en
  una segunda transacción, después del rollback (ver `architecture.md`, "Operación
  atómica con bloqueo").
- Las claves caducan a las 24 horas; una limpieza perezosa borra las vencidas.

## Alternativas consideradas

- **Deduplicar por contenido** (mismo emisor, destinatario, monto en N segundos):
  rechazado porque dos transferencias legítimas iguales seguidas son válidas.
- **Token de un solo uso emitido en "preparar"**: funciona, pero acopla HU-06 y HU-07 y
  no cubre la recarga, que no tiene paso de preparación.

## Consecuencias

- La webapp debe generar y conservar la clave mientras dura el flujo de confirmación.
- Las pruebas de HU-07 y HU-08 incluyen obligatoriamente: reintento con misma clave
  (una sola aplicación), misma clave con cuerpo distinto (`422`), y dos claves distintas
  en paralelo (ambas aplican o una se rechaza por saldo).
