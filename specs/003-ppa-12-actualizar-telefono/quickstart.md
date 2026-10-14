# PPA-12: cómo probar

1. Aplicar migraciones existentes y registrar dos cuentas ficticias.
2. Iniciar sesión y abrir `/perfil`; editar el teléfono y guardar un número libre.
3. Recargar la página: debe conservar el teléfono nuevo.
4. Iniciar sesión con el nuevo teléfono; el anterior ya no debe identificar la cuenta.
5. Intentar un teléfono inválido o de la segunda cuenta: rechazar y conservar el actual.
6. Cancelar una edición: conservar el valor guardado sin enviar PATCH.
7. Verificar que identificación y saldo no cambian y que no se solicita SMS.

Comandos: `ruff check .`, `mypy app`, `pytest` en api; `npm run lint`,
`npm run typecheck`, `npm run test`, `npm run build` y
`npx playwright test e2e/hu-12-actualizar-telefono.spec.ts` en webapp.

## Evidencia local (2026-10-14)

- Las pruebas nuevas fallaron antes de implementar `UpdatePhoneIn`.
- Ruff y mypy aprobados; backend con cobertura 94,82 %.
- Integración MySQL de HU-12: cambio persistido, login nuevo, teléfono anterior
  liberado y rechazo de duplicados aprobados.
- Los 21 casos anteriores de HU-08 que requieren `DATABASE_URL` MySQL externo
  se omiten por sus marcadores existentes; los tests nuevos usan testcontainers.
- TypeScript, lint y build aprobados; dos pruebas del hook de perfil aprobadas.
- Playwright: cuatro escenarios aprobados en escritorio y móvil; axe sin
  violaciones serious/critical en la comprobación del perfil tras guardar.
- Las pruebas Playwright de HU-12 simulan las respuestas de perfil; el login y
  la persistencia reales se verifican en los tests MySQL del backend.
