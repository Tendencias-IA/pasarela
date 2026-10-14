# Tasks: PPA-12 / HU-12

- [X] T001 [US1] Probar formato, autorización y errores en `api/app/modules/accounts/tests/unit/test_profile.py`.
- [X] T002 [US1] Implementar schemas, repositorio y servicio en `api/app/modules/accounts/{schemas,repository,service}.py`.
- [X] T003 [US1] Añadir rutas propias en `api/app/modules/accounts/profile_routes.py` y contrato en `api/openapi.yaml`.
- [X] T004 [US1] Probar persistencia, login nuevo, teléfono libre y saldo intacto en `api/app/modules/accounts/tests/integration/test_update_phone.py`.
- [X] T005 [US1] Generar tipos y añadir perfil Ionic en `webapp/src/features/accounts/ProfilePage.tsx`, `api.ts` y `webapp/src/app/routes.tsx`.
- [X] T006 [US1] Verificar éxito, rechazo y cancelación en `webapp/e2e/hu-12-actualizar-telefono.spec.ts`.
- [X] T007 Ejecutar gates locales y documentar resultados en `specs/003-ppa-12-actualizar-telefono/quickstart.md`.

Orden: T001 → T002 → T003 → T004 → T005 → T006 → T007.
