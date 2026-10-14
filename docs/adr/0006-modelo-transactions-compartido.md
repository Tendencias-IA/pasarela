# ADR-0006: El modelo `transactions` es compartido y vive en `app/common/models/`

**Estado**: Aceptada
**Fecha**: 2026-10-14
**Ticket**: PPA-17

## Contexto

La tabla `transactions` registra recargas (las escribe `wallet`, HU-08) y transferencias
(las escribe `transfers`, HU-07), y la lee `movements` (HU-09, HU-10). La regla de
vertical slicing prohíbe importar `models.py` de otro módulo, así que asignar el modelo a
un módulo obligaría a los otros dos a romper la regla o a duplicar el modelo sobre la
misma tabla.

## Decisión

El modelo SQLAlchemy `Transaction` vive en `app/common/models/transaction.py`, fuera de
los módulos. Es el único modelo compartido. Cada módulo lo usa desde su propio
`repository.py`: `wallet` y `transfers` insertan filas, `movements` solo consulta. Las
reglas de negocio sobre cuándo se inserta una fila y con qué estado siguen en
`architecture.md` ("Estados de una operación"). Las migraciones de la tabla se crean en
el módulo que introduce el cambio, con el ticket en el mensaje.

## Alternativas consideradas

- **Dueño `transfers` y servicio `record_recharge()` para `wallet`**: evita el modelo
  compartido, pero hace que una recarga dependa del módulo de transferencias, que no tiene
  nada que ver con ella.
- **Un modelo por módulo sobre la misma tabla**: SQLAlchemy lo permite, pero dos
  definiciones de la misma tabla divergen con el tiempo y Alembic genera migraciones
  contradictorias.
- **Tablas separadas `recharges` y `transfers`**: el historial (HU-09) tendría que unir
  dos tablas y ordenarlas por fecha en cada consulta; más complejo sin beneficio.

## Consecuencias

- `app/common/models/` queda reservado a modelos realmente compartidos; añadir otro
  requiere un ADR.
- Los tests unitarios de `wallet` y `transfers` siguen usando repositorios falsos; solo
  los de integración tocan la tabla real.
