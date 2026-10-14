# PPA-13: cómo probar

1. Con API, MySQL y frontend activos, registrar dos cuentas ficticias.
2. Iniciar sesión y abrir `/perfil`; pulsar Editar correo, guardar un correo libre.
3. Recargar: verificar el nuevo correo y que teléfono e identificación se mantienen.
4. Intentar formato inválido o correo de la otra cuenta: rechazar sin cambiar el actual.
5. Cancelar una edición: no enviar PATCH y conservar el valor guardado.
6. Confirmar que no se envía un código ni se alteran saldo o movimientos.

Validación: Ruff, mypy, pytest; lint, typecheck, Vitest, build y
`npx playwright test e2e/hu-13-actualizar-correo.spec.ts`.

## Evidencia local — 2026-10-14

- Ruff y mypy: sin errores.
- Suite completa de pytest: exit 0, cobertura 94.97% (umbral 90%).
  Se omiten 21 casos existentes de HU-08 que requieren DATABASE_URL MySQL;
  las integraciones de cuentas, incluido el cambio de correo, usan MySQL en Docker.
- Generación OpenAPI, typecheck y lint: sin errores.
- Vitest del hook de perfil: 4 pruebas aprobadas.
- Build del frontend y Playwright de HU-12/HU-13: 8 pruebas aprobadas
  en escritorio y móvil, con comprobación de accesibilidad.
- Las pruebas de navegador usan API simulada. La persistencia y unicidad reales
  se comprueban por separado en la integración del backend con MySQL.

La rama parte de PPA-12 y el PR debe apuntar a esa rama mientras el PR #6
siga abierto. Integrar primero PPA-12 y luego cambiar la base de PPA-13 a main.
