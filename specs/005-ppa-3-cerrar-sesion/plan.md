# Implementation Plan: PPA-3

**Branch**: `feat/PPA-3-cerrar-sesion` | **Date**: 2026-10-14 | **Spec**: [spec.md](spec.md)

## Summary

Revocar la sesión en auth, eliminar la cookie y sustituir el enlace ficticio
de logout por una acción Ionic. Vaciar QueryClient y desmontar las vistas privadas.
Una consulta mínima GET /auth/session permite al router verificar sesión antes
de montar pantallas privadas y al volver atrás. No implementa HU-04 completa.

## Technical Context

Python 3.12, Flask 3, SQLAlchemy 2, MySQL 8; React 18, TypeScript 5, Ionic 9,
TanStack Query. pytest/MySQL, Vitest/MSW y Playwright/axe. Sin dependencias nuevas.

## Constitution Check

- I/II: spec previa, CA-1..4 y ticket PPA-3 trazables.
- III: pruebas nuevas antes del código, cobertura API >=90% sin exclusiones nuevas.
- IV: auth solo escribe sessions; router orquesta componentes desde app.
- V: no operación financiera ni cambio de esquema.
- VI: cookie HttpOnly, token hasheado, CSRF existente, revocación persistente.
- VII: funciones simples y modelo existente; sin nuevas capas ni servicios externos.

## Project Structure

- API: `api/app/modules/auth/{routes,service,repository}.py`, `api/openapi.yaml`.
- UI: `webapp/src/features/auth/{api,useLogout}.ts`, `webapp/src/app/{AppShell,routes,RequireSession}.tsx`.
- Pruebas: auth/integration/test_logout.py, tests/contract/test_logout_contract.py,
  auth/__tests__/useLogout.test.tsx y e2e/hu-03-cerrar-sesion.spec.ts.

## Complexity Tracking

Consulta mínima de sesión necesaria para CA-2/CA-3: eliminar solo la cookie o
redirigir sin consultar al servidor deja abiertas vistas privadas. El endpoint
ya figura en el contrato de arquitectura; no incorpora renovación deslizante,
temporizador ni aviso por inactividad de HU-04.
