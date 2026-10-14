# ADR-0002: Flask 3 + SQLAlchemy 2 + Alembic sobre MySQL 8

**Estado**: Aceptada
**Fecha**: 2026-10-13
**Ticket**: PPA-17

## Contexto

El equipo pidió un backend en Python con un framework sencillo y MySQL como base de
datos. Se necesitan transacciones con bloqueo de filas (RNF-04.1, RNF-04.2), migraciones
versionadas (RNF-05) y una API HTTP consumida por un frontend React.

## Decisión

- **Flask 3** con patrón app factory (`create_app`) y un Blueprint por módulo.
- **SQLAlchemy 2** (estilo declarativo con `Mapped[]`) para modelos y consultas, y
  **Alembic** vía Flask-Migrate para migraciones. Una migración por cambio de esquema,
  nunca `create_all()` fuera de pruebas.
- **MySQL 8 / InnoDB**, `DECIMAL(15,2)` para dinero, `utf8mb4`, zona horaria UTC en
  servidor y conversión en el cliente.
- **Pydantic 2** para validar entrada y serializar salida en `schemas.py`; el contrato
  público se mantiene a mano en `backend/openapi.yaml` y se verifica con pruebas de
  contrato.
- Dependencias de apoyo: `argon2-cffi` (hash de contraseñas), `Flask-Limiter` (rate
  limit en login), `python-json-logger`.

## Alternativas consideradas

- **FastAPI**: validación y OpenAPI automáticos, pero el equipo prefirió Flask por
  familiaridad y simplicidad del modelo síncrono. La pérdida del OpenAPI automático se
  compensa con `openapi.yaml` y pruebas de contrato.
- **Django**: ORM y admin integrados, pero impone su estructura por app y más superficie
  de la necesaria para 13 historias.
- **SQL crudo con `mysql-connector`**: rechazado porque las migraciones y el bloqueo de
  filas quedarían a mano y sin tipos.

## Consecuencias

- Las pruebas de integración necesitan MySQL real (contenedor) porque `SELECT ... FOR
  UPDATE` no se puede simular fielmente con SQLite.
- El contrato `openapi.yaml` puede desincronizarse del código; la prueba de contrato en CI
  es el mecanismo que lo evita.
