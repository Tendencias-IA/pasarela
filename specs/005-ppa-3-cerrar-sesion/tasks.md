# Tasks: PPA-3

## Setup

- [x] T001 Documentar requisitos y diseño en specs/005-ppa-3-cerrar-sesion/spec.md y plan.md.

## US1 — cierre seguro (MVP)

- [x] T002 [US1] Escribir y ejecutar pruebas rojas en api/app/modules/auth/tests/integration/test_logout.py y webapp/src/features/auth/__tests__/useLogout.test.tsx.
- [x] T003 [US1] Revocar sesión y borrar cookie en api/app/modules/auth/{repository,service,routes}.py.
- [x] T004 [US1] Añadir contratos y pruebas en api/openapi.yaml y api/tests/contract/test_logout_contract.py.
- [x] T005 [US1] Implementar logout, limpieza y guard en webapp/src/features/auth/useLogout.ts y webapp/src/app/{AppShell,RequireSession,routes}.tsx.
- [x] T006 [US1] Verificar cierre, rechazo y navegación atrás en webapp/e2e/hu-03-cerrar-sesion.spec.ts.

## Cierre

- [x] T007 Ejecutar gates y registrar evidencia en specs/005-ppa-3-cerrar-sesion/quickstart.md.

Dependencias: T001 → T002 → T003/T004 → T005 → T006 → T007.
Backend y pruebas frontend pueden validarse independientemente; no se requieren agentes.
