# Decisiones PPA-3

- Decisión: actualizar únicamente revoked_at de la sesión activa con transacción.
  Motivo: sesiones ya persistidas y get_current_session ya rechaza revocadas.
  Alternativa descartada: borrar solo la cookie; permite reutilizar el token.
- Decisión: limpiar caché y desmontar rutas privadas, comprobando sesión al montarlas.
  Motivo: evita mostrar resultados de la cuenta anterior al volver atrás.
  Alternativa descartada: enlace directo al login; no revoca ni limpia datos.
- Decisión: fallo de cierre conserva la vista y muestra error reintentable.
  Motivo: no afirmar que se revocó una sesión cuando el servidor no lo confirmó.
