# PPA-1 / HU-01 — Registro de cuenta

## Integración

Base: `main` en `a6d32fa`, que incluye el login de HU-02. Se conserva el módulo
de autenticación, su interfaz y el scaffold oficial. El formulario se expone en
`/registro` y enlaza a `/login`; el registro no inicia sesión.

La migración `0002_users_wallets` se aplica después de
`0001_create_users_and_sessions`. Añade los datos de perfil y la billetera, con
saldo `DECIMAL(15,2)` inicial `0.00`. Los datos de perfil son obligatorios para
registrarse, pero anulables en almacenamiento para conservar los usuarios
preexistentes del login.

## Evidencia local

- Suite completa de API aprobada contra MySQL Docker; cobertura 97,48 %.
- Ruff y mypy aprobados.
- TypeScript, lint y build del frontend aprobados.
- Vitest: 20 pruebas aprobadas, incluyendo registro, login y cliente HTTP.
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
