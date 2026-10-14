# Implementation Plan: PPA-12

## Summary

Extender `accounts` y reemplazar la pantalla provisional `/perfil`. Reutilizar
sesión, cliente HTTP, unicidad de MySQL y componentes Ionic. Sin migraciones ni dependencias.

## Technical Context

Python 3.12, Flask, SQLAlchemy 2, Pydantic 2, MySQL 8; React 18, Ionic 9,
TanStack Query, React Hook Form, Vitest y Playwright.

## Constitution Check

| Principio | Resultado | Evidencia |
| --- | --- | --- |
| Spec antes de código y trazabilidad | PASS | CA-1 a CA-8 en spec y pruebas |
| Monolito modular | PASS | Solo accounts escribe users |
| Seguridad | PASS | Usuario desde sesión, campos extra rechazados, sin PII en logs |
| Dinero | PASS | No se escriben billeteras ni movimientos |
| Simplicidad | PASS | Sin migración, dependencias o capas nuevas |
| Calidad | PASS | Tests de formato, titularidad, duplicados y cambio de identificador |

## Design

- `GET /api/v1/profile`: devuelve nombre, teléfono, identificación y correo propios.
- `PATCH /api/v1/profile`: acepta solo `{phone}`; devuelve el perfil actualizado.
- Estados: 200 éxito, 401 sin sesión, 404 perfil ausente, 409 duplicado, 422 validación.
- Servicio usa `transaction()` para convivir con la lectura de sesión (autobegin).
- Repositorio bloquea el usuario con `FOR UPDATE`, comprueba unicidad excluyendo
  su id y actualiza solamente `phone`. El índice UNIQUE resuelve carreras entre cuentas.
- La respuesta se captura dentro de la transacción, evitando consultas tras el commit.
- Perfil nullable de los usuarios técnicos de login se conserva y se muestra como «Sin registrar».
- UI consulta TanStack Query, edita mediante React Hook Form, reemplaza caché tras éxito,
  cancela sin solicitud y muestra errores accesibles y confirmación Ionic.

## Verification

Pruebas unitarias del schema/servicio/rutas; integración MySQL: registro → login →
cambio → nuevo login, persistencia, teléfono anterior libre e invariantes de billetera.
Playwright: éxito, rechazo y cancelación en ambos tamaños con axe.
