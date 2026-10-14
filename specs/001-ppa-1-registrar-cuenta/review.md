# PPA-1 / HU-01 — Registro de cuenta

## Integración

Base: `main` en `9059f61`, que incluye login HU-02 y recarga HU-08. Se conserva el módulo
de autenticación, su interfaz y el scaffold oficial. El formulario se expone en
`/registro` y enlaza a `/login`; el registro no inicia sesión.

La migración `0003_users_registration` se aplica después de
`0002_wallet_tables`. Reutiliza la billetera de HU-08 y añade los datos de perfil, con
saldo `DECIMAL(15,2)` inicial `0.00`. Los datos de perfil son obligatorios para
registrarse, pero anulables en almacenamiento para conservar los usuarios
preexistentes del login.

## Evidencia local

- API después de integrar HU-08: pruebas ejecutadas aprobadas y cobertura 94,94 %.
  Los tests de HU-01 y login usan MySQL Docker; 21 casos de HU-08 marcados por
  main para MySQL externo se omiten sin `DATABASE_URL` MySQL al iniciar pytest.
- Ruff y mypy aprobados.
- TypeScript, lint y build del frontend aprobados.
- Vitest antes de integrar HU-08: 20 pruebas aprobadas. Después del merge,
  el panel inicial presentó un timeout de hidratación; se amplió la espera
  explícita a cinco segundos conservando las aserciones y se vuelve a comprobar.
- Playwright de HU-01: alta exitosa y rechazo en escritorio y móvil; las
  respuestas HTTP se simulan para comprobar interfaz y accesibilidad.

## Verificación antes del merge

- Revisar los resultados de CI y SonarQube del PR.
- Demostrar el flujo completo con frontend, API y MySQL en Docker Compose.
- Completar la auditoría de secretos y trazabilidad final.
- Las tareas T019–T021 contienen casos más amplios que los tests actuales:
  falta ampliar el rollback de billetera y la validación de cada respuesta
  HTTP contra el contrato. No se marcan completas por tener solo parte cubierta.

Este documento registra la implementación entregada y sus límites; los pendientes
siguen visibles en `tasks.md` y no se reducen los umbrales de calidad.
