# Probar PPA-3

Prerrequisitos: MySQL/Docker y API con variables de api/.env.example configuradas;
`uv sync` en api y `npm ci` en webapp. Migraciones aplicadas. Datos ficticios.

1. Iniciar sesión con una cuenta registrada y abrir /recargar.
2. Cerrar sesión desde el menú (en móvil, abrir menú primero): vuelve al login.
3. Volver atrás, recargar o entrar directamente a /recargar: exige login.
4. Repetir una petición privada con la cookie anterior: 401 invalid_session.
5. Iniciar sesión nuevamente: cuenta, saldo y movimientos intactos.
6. Simular fallo del endpoint de logout: muestra error y permite reintentar.

Validación: Ruff, mypy, pytest; npm run lint, npm run typecheck, npm run test;
`npx playwright test e2e/hu-03-cerrar-sesion.spec.ts` en ambos proyectos.
