# Constitución de la Billetera Digital (Pasarela)

Documento raíz del proyecto. Spec Kit lo inyecta en `/speckit-specify`, `/speckit-plan` y
`/speckit-tasks`; todo plan debe pasar el **Constitution Check** contra estos principios.
Las reglas detalladas viven en `.claude/rules/`; esta constitución fija lo innegociable.

Fuente de negocio: `docs/referencia/requisitos-billetera-v1.0.md` (RF-01 a RF-07,
RNF-01 a RNF-06, HU-01 a HU-13). Cuando una regla cita un código `RF`, `RNF`, `CA` o `HU`,
se refiere a ese documento.

## Core Principles

### I. Especificación antes de código (NO NEGOCIABLE)

Ninguna historia se implementa sin `spec.md`, `plan.md` y `tasks.md` aprobados en
`specs/<NNN-ppa-n-slug>/`. La spec cita la HU y sus criterios de aceptación con su número;
el plan declara en qué módulo vive el cambio; las tareas referencian archivos concretos.
Un PR sin carpeta en `specs/` enlazada se rechaza. Razón: el equipo trabaja con
herramientas de IA, y la spec es el único contrato que la herramienta no puede inventar.

### II. Trazabilidad a requisitos

Cada regla de negocio en código y cada prueba referencian el criterio que las origina
(`HU-07 CA-4`, `RNF-04.1`). Un comportamiento que no está en la especificación v1.0 no
se implementa; si falta, se propone primero un cambio al documento de requisitos y al
ticket de Jira. Razón: evita que la IA "complete" funcionalidad que nadie pidió.

### III. Pruebas primero y cobertura mínima

Las pruebas de cada tarea se escriben antes de la implementación y deben fallar primero.
Backend: cobertura de líneas y ramas ≥ 90 % medida con `pytest-cov`, umbral bloqueante en
CI. Frontend: unitarias con Vitest para lógica y componentes, y un escenario Playwright
por historia de usuario que cubra el camino exitoso y el rechazado. Transferencias y
recargas tienen pruebas de concurrencia e idempotencia obligatorias (RNF-04). Razón:
el dinero, aunque ficticio, es el dominio donde un error silencioso cuesta más.

### IV. Monolito modular con vertical slicing

Un único despliegue de backend y uno de frontend. El código se organiza por capacidad de
negocio, no por capa técnica: `accounts`, `auth`, `wallet`, `transfers`, `movements`. Un
módulo solo toca sus propias tablas y expone servicios Python a los demás; nunca consulta
tablas ajenas ni importa repositorios de otro módulo. No se introducen puertos, adaptadores,
colas ni microservicios sin un ADR que justifique el problema concreto que resuelven.
Razón: 13 historias y un equipo pequeño; la complejidad accidental es el mayor riesgo.

### V. Integridad del dinero

Los montos se representan con `decimal.Decimal` en Python, `DECIMAL(15,2)` en MySQL y
cadenas en JSON; nunca `float` (RNF-04.3). Toda operación que mueve saldo ocurre en una
sola transacción de base de datos con bloqueo de las billeteras involucradas
(`SELECT ... FOR UPDATE` en orden ascendente de id), de modo que ambos saldos cambian o
ninguno (RNF-04.1, RNF-04.2). Transferencias y recargas aceptan `Idempotency-Key` y la
misma clave no se aplica dos veces (RNF-04.4). Una operación solo termina en estado
`exitosa` o `rechazada`; una rechazada no modifica saldos ni crea movimientos parciales.

### VI. Seguridad y privacidad por defecto

Autenticación, autorización, titularidad y límites de montos se validan en el servidor,
nunca solo en el cliente (RNF-01.4). Contraseñas con hash Argon2id (RNF-01.2). Sesión del
lado del servidor con expiración deslizante de cinco minutos e invalidación real al cerrar
(RNF-01.3, HU-03, HU-04). Ningún log, mensaje de error ni respuesta contiene contraseñas,
tokens, ni teléfonos completos de terceros (RNF-06). Los datos de otro participante
siempre se devuelven enmascarados.

### VII. Simplicidad y legibilidad

Se elige la solución más simple que cumpla la spec. Sin abstracciones "por si acaso",
sin configuración que nadie usa, sin dependencias nuevas sin ADR. Funciones que no se
pueden nombrar sin "y" se dividen. El código y los commits se escriben para quien lo lea
sin contexto en seis meses, incluida la herramienta de IA del siguiente ticket.

## Restricciones técnicas y de negocio

- Stack fijo: Python 3.12 + Flask 3 + SQLAlchemy 2 + Alembic + MySQL 8; React 18 + Vite +
  TypeScript estricto. Cambiarlo requiere ADR y aprobación del equipo.
- Reglas de negocio inmutables mientras no cambie la especificación v1.0: teléfono,
  identificación y correo únicos; la identificación es inmutable; transferencias entre
  $100 y $3.000.000 COP inclusive; recargas entre $5.000 y $5.000.000 COP inclusive; sin
  saldo máximo; historial de 20 por página con filtros de fecha y tipo; sesión de 5
  minutos; estados `exitosa` y `rechazada` únicamente.
- Fuera de alcance permanente del prototipo: pagos reales, códigos de verificación por
  SMS o correo, recuperación de contraseña, datos financieros reales.
- Rendimiento objetivo (RNF-02): p95 ≤ 2 s en consulta de saldo; p95 ≤ 3 s en historial,
  transferencias y recargas; 20 usuarios concurrentes sin inconsistencias de saldo.
- Accesibilidad y usabilidad (RNF-03): responsive escritorio y móvil; navegación por
  teclado; etiquetas en todos los controles; funciones principales a máximo tres clics.
- Ambientes: local y producción. `main` es la única rama larga y es desplegable siempre.

## Flujo de desarrollo y gates de calidad

1. Tomar el ticket PPA-n en Jira y crear la rama con `/speckit-specify` (ver
   `docs/sdd-workflow.md`).
2. `spec.md` → `/speckit-clarify` si hay dudas → `plan.md` con Constitution Check →
   `tasks.md` → `/speckit-implement`.
3. Un commit por tarea o grupo lógico, con formato `type(PPA-n): descripción`.
4. PR hacia `main` con la plantilla de `.github/PULL_REQUEST_TEMPLATE.md`, diff menor a
   400 líneas significativas, al menos una aprobación y CI verde.
5. Gates bloqueantes en CI: Ruff, mypy, ESLint, tsc, pytest con cobertura ≥ 90 %, Vitest,
   Playwright, quality gate de SonarQube (0 bugs, 0 vulnerabilidades, 0 hotspots sin
   revisar, duplicación < 3 %, cobertura ≥ 90 %).
6. Definición de terminado: criterios de la HU verificados por pruebas automáticas,
   definición transversal de terminado del documento de requisitos cumplida, ticket de
   Jira en estado final con enlace al PR.

## Governance

Esta constitución prevalece sobre cualquier otra guía del repositorio. Si una regla de
`.claude/rules/` la contradice, gana la constitución y se abre un PR para corregir la
regla. El código existente no es autoridad: si contradice la constitución, está mal.

Enmiendas: PR que modifica este archivo, con la justificación en el cuerpo del PR, una
aprobación de otra persona del equipo, y actualización de la versión según SemVer:
MAJOR al eliminar o redefinir un principio, MINOR al añadir principio o sección, PATCH
por aclaraciones. Todo PR de implementación verifica cumplimiento en el Constitution
Check del `plan.md` y en el checklist del PR. Las desviaciones se documentan en la tabla
"Complexity Tracking" del plan con la alternativa más simple rechazada y el motivo.

**Version**: 1.0.0 | **Ratified**: 2026-10-13 | **Last Amended**: 2026-10-13
