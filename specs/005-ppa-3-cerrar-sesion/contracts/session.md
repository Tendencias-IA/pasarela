# Contrato PPA-3

Fuente ejecutable: `api/openapi.yaml`.

- POST /api/v1/auth/logout: cookie válida y X-Requested-With: fetch; sin cuerpo.
  204 sin contenido, cookie borrada. 401 invalid_session; 403 missing_requested_with.
- GET /api/v1/auth/session: cookie válida; 200 {expires_at: fecha ISO UTC}.
  401 invalid_session. Consulta de acceso, sin renovación ni cambios de saldo.
- Respuestas auth y privadas con cookie: Cache-Control: no-store.
- Tras 204, el cliente cancela consultas, vacía caché y reemplaza la ruta por /login.
- Un 5xx/fallo de red no limpia la sesión local como si hubiera sido un éxito.
