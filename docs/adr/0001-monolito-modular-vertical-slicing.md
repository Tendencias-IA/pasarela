# ADR-0001: Monolito modular con vertical slicing en lugar de arquitectura hexagonal

**Estado**: Aceptada
**Fecha**: 2026-10-13
**Ticket**: PPA-17

## Contexto

La billetera tiene 13 historias de usuario, un equipo pequeño que trabaja con
herramientas de IA, un solo despliegue y ninguna integración externa (no hay pasarela
de pagos real, bancos ni notificaciones). Se evaluó una arquitectura hexagonal
(puertos y adaptadores) porque es común en sistemas de pagos.

## Decisión

Un monolito modular organizado por capacidad de negocio (vertical slicing): un módulo
por capacidad (`accounts`, `auth`, `wallet`, `transfers`, `movements`), cada uno con
sus rutas, schemas, servicio, repositorio, modelos y pruebas. Dentro del módulo hay tres
capas mínimas (`routes → service → repository`) solo para poder probar las reglas de
negocio sin base de datos. Estructura detallada en `.claude/rules/architecture.md`.

## Alternativas consideradas

- **Hexagonal / clean architecture**: puertos e interfaces para repositorios y servicios
  externos. Rechazada porque no hay ningún adaptador que intercambiar: una sola base de
  datos y cero servicios externos. Las interfaces añadirían archivos y capas que la IA
  tendría que mantener en cada historia sin ganancia de testabilidad, ya que los servicios
  ya se prueban con repositorios falsos.
- **Monolito por capas técnicas** (`controllers/`, `services/`, `models/` globales).
  Rechazada porque una historia tocaría cuatro carpetas, los PR se cruzarían entre
  compañeros y la IA tendría que cargar todo el proyecto en contexto para cada cambio.
- **Microservicios**: rechazada por obvia sobre-ingeniería para el alcance.

## Consecuencias

- Una HU se implementa en una carpeta; dos personas pueden trabajar en módulos distintos
  sin conflictos.
- El riesgo es el acoplamiento silencioso entre módulos. Se mitiga con la regla "solo se
  importa `service.py` de otro módulo" y con la revisión del PR.
- Si en el futuro aparece un servicio externo real (por ejemplo, un PSP), se introduce un
  adaptador solo para ese servicio, en el módulo que lo usa, con un ADR nuevo.
