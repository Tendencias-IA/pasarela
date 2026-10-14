# Guía SDD: de un ticket de Jira a un PR

Para cualquier persona del equipo, con Claude Code abierto en la raíz del repo. El
ciclo completo para una historia toma una sesión; cada paso produce un archivo que el
siguiente paso consume. Si un paso no produce su archivo, no se avanza.

## Antes de empezar (una sola vez)

1. Instala Claude Code y, opcionalmente, la CLI de Spec Kit (`uv tool install
   specify-cli --from git+https://github.com/github/spec-kit.git`). No hace falta
   ejecutar `specify init`: el repo ya está inicializado.
2. Clona el repo y abre Claude Code en la raíz. Verifica que al escribir `/speckit`
   aparecen los comandos `speckit-specify`, `speckit-plan`, `speckit-tasks`,
   `speckit-implement`.
3. Lee `AGENTS.md`. Son cinco minutos y evita el 80 % de los retrabajos.

## Paso 0. Tomar el ticket

- Asígnate el ticket `PPA-n` en Jira y pásalo a "En progreso".
- Copia la historia completa con sus criterios de aceptación: la vas a pegar en el
  siguiente paso. La versión canónica está en
  `docs/referencia/requisitos-billetera-v1.0.md`.
- Crea la rama desde `main` actualizado:

```bash
git checkout main && git pull
git checkout -b feat/PPA-6-preparar-transferencia
```

## Paso 1. Especificar: `/speckit-specify`

Pega la HU con sus criterios y pide el nombre corto `ppa-<n>-<slug>` para la carpeta.

```text
/speckit-specify HU-06 Preparar una transferencia. Nombre corto: ppa-6-preparar-transferencia.
Como usuario autenticado, quiero ingresar el teléfono del destinatario y el monto, para
revisar una transferencia antes de confirmarla.
Criterios de aceptación:
1. El sistema permite ingresar el teléfono del destinatario y un monto en COP.
2. El monto permitido se encuentra entre $100 y $3.000.000 COP, inclusive.
3. ... (todos los CA tal cual están en Jira)
Dependencias: HU-02 y HU-05. Fuera de alcance: ejecutar la transferencia (HU-07).
```

Resultado: `specs/006-ppa-6-preparar-transferencia/spec.md`. Revísalo y exige que:

- cada criterio de aceptación aparezca como escenario Given/When/Then con su código
  `CA-n`;
- las reglas de negocio citen el documento de requisitos (límites, enmascaramiento);
- no invente nada que no esté en la HU; si falta información, debe quedar como
  `[NEEDS CLARIFICATION]`, no resuelto por la IA.

## Paso 2. Aclarar: `/speckit-clarify` (si hay `NEEDS CLARIFICATION`)

Responde las preguntas con el documento de requisitos a mano. Si la respuesta no está en
el documento, pregunta al equipo y registra la decisión en el ticket de Jira antes de
seguir. No dejes que la IA "asuma".

## Paso 3. Planificar: `/speckit-plan`

```text
/speckit-plan Implementar en el módulo transfers (`api/`) y la feature transfers (`webapp/`)
siguiendo .claude/rules/architecture.md. Preparar no escribe nada en BD. Reutilizar
wallet.service para leer saldo y accounts.service para buscar destinatario por teléfono.
```

Resultado: `plan.md`, `research.md`, `data-model.md`, `contracts/` y `quickstart.md`.
Revisa el **Constitution Check**: debe listar cada principio y decir cómo se cumple. Si
hay una desviación, debe estar en "Complexity Tracking" con la alternativa más simple
rechazada. Un plan que crea carpetas fuera de `api/app/modules/transfers/` o
`webapp/src/features/transfers/` sin justificación está mal.

Opcional pero recomendado: `/speckit-checklist` genera una lista de verificación de
calidad de la spec.

## Paso 4. Tareas: `/speckit-tasks`

Resultado: `tasks.md`. Exige que:

- las pruebas de cada criterio aparezcan **antes** de la implementación que cubren;
- cada tarea nombre el archivo exacto (`api/app/modules/transfers/service.py`);
- exista una tarea para `openapi.yaml`, una para el spec Playwright
  `webapp/e2e/hu-06-preparar-transferencia.spec.ts` y, si hay esquema nuevo, una
  migración.

Opcional: `/speckit-analyze` cruza spec, plan y tasks y reporta inconsistencias.

## Paso 5. Implementar: `/speckit-implement`

La IA ejecuta las tareas en orden. Tu trabajo es revisar, no mirar:

- Después de cada grupo de tareas, corre los comandos de `AGENTS.md` y lee el diff.
- Haz un commit por tarea o grupo lógico: `feat(PPA-6): validar rango de monto al
  preparar transferencia`. Tú haces el commit, no la IA, y solo después de leerlo.
- Si la IA se sale de las reglas (un `float`, SQL en una ruta, un `except Exception:
  pass`), no lo corrijas a mano en silencio: díselo citando la regla, para que corrija el
  patrón y no solo la línea.

## Paso 6. Verificar y abrir el PR

```bash
cd api && ruff format . && ruff check . && mypy app && pytest
cd ../webapp && npm run lint && npm run typecheck && npm run test && npm run e2e
git log --oneline main..HEAD
```

- Cobertura ≥ 90 %, cada CA con un test que lo cita, Playwright verde en escritorio y
  móvil.
- `git push -u origin feat/PPA-6-preparar-transferencia` y abre el PR con el título
  `feat(PPA-6): preparar transferencia con validación y resumen enmascarado`. Completa la
  plantilla con honestidad: resumen, ticket y spec, cambios y cómo probar.
- Pide revisión. Responde cada comentario con el commit que lo resuelve. Tras el merge
  (squash), borra la rama y pasa el ticket a "Listo" con el enlace al PR.

## Si algo sale mal

| Síntoma | Qué hacer |
| --- | --- |
| `/speckit-specify` no encuentra la constitución | Estás fuera de la raíz del repo o falta `.specify/`. Vuelve a clonar. |
| El plan propone hexagonal, colas o un microservicio | Rechaza el plan y cita ADR-0001; vuelve a correr `/speckit-plan` con la restricción explícita. |
| La cobertura queda en 85 % | No excluyas archivos. Pide a la IA tests unitarios de servicio para las ramas sin cubrir (`pytest --cov-report=term-missing` las lista). |
| Sonar reporta un hotspot | Revísalo en Sonar y márcalo como seguro solo si puedes explicar por qué en el PR. |
| El spec de Playwright es inestable | Suele ser un selector por texto cambiante o una espera implícita. Usa roles y `expect(...).toBeVisible()`. |
| La IA "completó" funcionalidad que no está en la HU | Bórrala. Si crees que hace falta, propón el cambio en el documento de requisitos y en Jira. |

## Ejemplo resumido completo (HU-06)

1. `git checkout -b feat/PPA-6-preparar-transferencia`
2. `/speckit-specify` con la HU-06 → `specs/006-ppa-6-preparar-transferencia/spec.md`
3. `/speckit-plan` → módulo `transfers`, endpoint `POST /api/v1/transfers/preview`, sin
   escritura en BD, enmascaramiento en servidor.
4. `/speckit-tasks` → tests unitarios de `preview_transfer` (CA-2..CA-6), test de
   contrato, `openapi.yaml`, `TransferForm` + `TransferSummary`, spec Playwright.
5. `/speckit-implement` → commits por tarea, revisados por ti.
6. PR `feat(PPA-6): ...`, CI verde, una aprobación, squash, ticket a "Listo".
