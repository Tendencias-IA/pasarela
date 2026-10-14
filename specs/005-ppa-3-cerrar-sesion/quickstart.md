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

## Evidencia local — 2026-10-14

- Rojo inicial: logout inexistente devuelve 404; el hook aún no existe.
- Ruff, mypy y pytest completo: aprobados; cobertura API 95.13% (umbral 90%).
- MySQL real en Docker: revoca una de dos sesiones, elimina cookie, rechaza
  la cookie anterior con solicitudes válidas y conserva cuenta, saldo y movimientos.
- OpenAPI regenerado, typecheck, lint y build: aprobados.
- Vitest completo: 55 pruebas aprobadas, incluidas las del cierre y del panel.
- Playwright HU-03 y regresión HU-01: 8 pruebas aprobadas en móvil y escritorio,
  incluida revisión de accesibilidad sin hallazgos serious/critical.
- Navegador con API simulada; revocación real verificada aparte en MySQL.
- Se omiten 21 casos existentes de HU-08 por DATABASE_URL no MySQL;
  las pruebas de auth sí usan MySQL de testcontainers. CI pendiente.
- Gitleaks no está disponible en el PATH local; revisión del diff sin secretos
  nuevos y comprobación automática pendiente en CI.

## Entrega por PR

Backend: PR #8, `feat/PPA-3-cerrar-sesion-api` hacia main.
Frontend: `feat/PPA-3-cerrar-sesion` sobre la rama backend. Integrar #8 primero
y cambiar después la base del PR de frontend a main. No depende de PPA-12/PPA-13.
