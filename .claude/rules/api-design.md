---
paths:
  - "api/app/modules/**/routes.py"
  - "api/app/modules/**/schemas.py"
  - "api/openapi.yaml"
  - "webapp/src/shared/api/**"
---

# Diseño de la API HTTP

El contrato es `api/openapi.yaml`. Se edita a mano en la misma tarea que el endpoint
y se verifica con pruebas de contrato (ver `testing.md`). El frontend genera sus tipos
desde ese archivo con `openapi-typescript`; nunca escribe tipos de respuesta a mano.

## Convenciones generales

- Base `/api/v1`. Un cambio incompatible crea `/api/v2`; no se rompe `v1` en silencio.
- JSON en entrada y salida, `Content-Type: application/json`. Errores con
  `application/problem+json`.
- Nombres de campos en `snake_case` en JSON (espejo de Python). El frontend adapta en
  su capa `shared/api`.
- Montos como cadena decimal con dos decimales (`"150000.00"`), ver ADR-0003. Fechas en
  ISO 8601 UTC (`2026-10-13T21:40:00Z`).
- Toda mutación (`POST`, `PATCH`, `DELETE`) exige la cabecera `X-Requested-With: fetch`
  como defensa CSRF complementaria a `SameSite=Lax` (ADR-0004).
- `POST /transfers` y `POST /wallet/recharges` exigen `Idempotency-Key` (ADR-0005).
- Autenticación por cookie de sesión `HttpOnly`. Sin sesión válida: `401` con
  `type: ".../unauthenticated"`. Nunca `403` para distinguir "no existe" de "no es tuyo"
  en recursos de otro usuario: se responde `404` para no filtrar existencia (RNF-06.1).

## Endpoints de la v1

| Método y ruta | Historia | Éxito | Errores de negocio |
| --- | --- | --- | --- |
| `POST /api/v1/accounts` | HU-01 | `201` cuenta creada, sin sesión | `422 validation`, `409 duplicate_identity` |
| `POST /api/v1/auth/login` | HU-02 | `204` + cookie | `401 invalid_credentials`, `429 too_many_attempts` |
| `POST /api/v1/auth/logout` | HU-03 | `204` + cookie borrada | `401` |
| `GET /api/v1/auth/session` | HU-04 | `200 {expires_at}` | `401 session_expired` |
| `GET /api/v1/wallet` | HU-05 | `200 {balance}` | `401`, `404 wallet_not_found` |
| `POST /api/v1/wallet/recharges` | HU-08 | `201 {transaction}` | `422 amount_out_of_range`, `400 missing_idempotency_key` |
| `POST /api/v1/transfers/preview` | HU-06 | `200 {amount, recipient_masked}` | `422 amount_out_of_range`, `404 recipient_not_found`, `422 self_transfer`, `422 insufficient_balance` |
| `POST /api/v1/transfers` | HU-07 | `201 {transaction}` | igual que preview + `422 idempotency_key_mismatch` |
| `GET /api/v1/movements?page=&from=&to=&type=` | HU-09, HU-10 | `200 {items, page, page_size: 20, total}` | `422 invalid_date_range` |
| `GET /api/v1/profile` | HU-11 | `200 {full_name, phone, national_id, email}` | `401` |
| `PATCH /api/v1/profile` | HU-12, HU-13 | `200` perfil actualizado | `422 validation`, `409 duplicate_identity` |

`type` en `movements`: `all` (por defecto), `sent`, `received`, `recharge`. Orden fijo:
`created_at DESC`. `page` empieza en 1; `page_size` es fijo en 20 (RF-05).

## Formato de error (RFC 9457)

```json
{
  "type": "https://pasarela.local/problems/insufficient_balance",
  "title": "Saldo insuficiente",
  "status": 422,
  "detail": "El saldo disponible es menor que el monto solicitado.",
  "instance": "/api/v1/transfers",
  "code": "insufficient_balance",
  "request_id": "7f1c9b2e",
  "errors": [{ "field": "amount", "message": "Debe estar entre 100.00 y 3000000.00" }]
}
```

- `code` es estable y en `snake_case`; el frontend decide mensajes y comportamiento por
  `code`, nunca por `detail`.
- `errors` solo aparece en `422 validation` y lista todos los campos inválidos a la vez
  (RNF-03.2), no solo el primero.
- `detail` nunca contiene valores enviados por el usuario ni datos de otra cuenta.

## Ejemplo completo: confirmar transferencia

Solicitud:

```http
POST /api/v1/transfers HTTP/1.1
Content-Type: application/json
X-Requested-With: fetch
Idempotency-Key: 6f1a2c3e-8b4d-4e5f-9a6b-7c8d9e0f1a2b
Cookie: session=...

{ "recipient_phone": "3001234567", "amount": "150000.00" }
```

Respuesta `201`:

```json
{
  "id": 8812,
  "type": "transferencia",
  "status": "exitosa",
  "amount": "150000.00",
  "recipient": { "name_masked": "Mar** G****", "phone_masked": "***4567" },
  "balance_after": "350000.00",
  "created_at": "2026-10-13T21:40:00Z"
}
```

Reintento con la misma clave y el mismo cuerpo: misma respuesta `201` más cabecera
`Idempotent-Replayed: true`, sin segundo débito.

## Qué no hacer

- No devolver `200` con `{"ok": false}`; el estado HTTP es el resultado.
- No exponer ids de billetera ajenos ni teléfonos completos de terceros en ninguna
  respuesta.
- No aceptar montos numéricos (`150000`) aunque Pydantic pueda convertirlos: el schema
  rechaza `float`/`int` para forzar la cadena y evitar pérdida de precisión en el cliente.
- No paginar con `offset` libre ni permitir `page_size` por query: los requisitos fijan 20.
