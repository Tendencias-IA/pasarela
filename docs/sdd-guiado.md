# Trabajo guiado con `/sdd`: puertas de decisión y bitácora

Procedimiento para trabajar una historia de Jira (PPA-n) **en conjunto** entre una persona y
un agente de IA, cualquiera que sea (Claude Code, Codex u otro). El agente prepara y propone;
la persona decide en cada **puerta**; cada decisión queda en una **bitácora** que es la
evidencia del trabajo controlado. Envuelve el ciclo SDD de `docs/sdd-workflow.md`.

Este documento es la única fuente de verdad. Los adaptadores por agente
(`.claude/skills/sdd/SKILL.md`, `.agents/skills/sdd/SKILL.md`) solo lo cargan y añaden lo
específico de su herramienta.

## Entrada

```text
/sdd PPA-n            # empieza desde el ticket
/sdd PPA-n continuar  # retoma donde dice la bitácora
```

Si falta el ticket, el agente pregunta cuál antes de hacer nada.

## Reglas que no se negocian

1. **Ninguna puerta se pasa sin respuesta explícita de la persona.** El agente presenta la
   decisión como una pregunta cerrada con 2 a 4 opciones concretas (una marcada como
   recomendada) y espera. Una respuesta libre de la persona vale como decisión.
2. **Una fase por turno.** El agente termina la fase, abre la puerta y para. No encadena la
   siguiente fase en el mismo turno aunque "sea obvia".
3. **Modelo por fase.** Al entrar en cada fase el agente anuncia el modelo recomendado
   (tabla de abajo) y por qué, pide a la persona que lo cambie en su herramienta (o que diga
   "sigo con este") y espera la confirmación antes de trabajar. El modelo con el que se hizo
   la fase se anota en la bitácora. El agente no cambia su propio modelo.
4. **Bitácora obligatoria** en `specs/NNN-ppa-n-slug/decisiones.md` (plantilla en
   `.specify/templates/decisiones-template.md`). La entrada se escribe **en el mismo turno**
   en que la persona decide, nunca después.
5. **Git y Jira solo por decisión en puerta**: sin `git add`, `commit`, `push`, PR ni cambios
   de ticket que la persona no haya elegido en una puerta (`.claude/rules/git-workflow.md`).
6. Todo lo demás es lo que ya dicen `AGENTS.md`, la constitución y `.claude/rules/`.

## Modelo recomendado por fase

| Fase | Modelo | Razón |
| --- | --- | --- |
| 0 Ticket, 1 Especificar, 2 Aclarar, 4 Tareas, 6 Cierre | el más económico de la familia (Sonnet en Claude) | Lectura, redacción y listas: no exige el modelo más caro |
| 3 Planificar | el intermedio (Opus en Claude) | Hay alternativas de diseño que comparar |
| 5 Implementar | el intermedio; **el más potente** (Fable en Claude) si la historia mueve dinero, bloquea filas o hay concurrencia | El coste de un error silencioso en dinero es el mayor del proyecto (constitución V) |

En Codex u otra herramienta se aplica la misma escala con sus modelos. La persona puede
elegir otro; se respeta y se anota.

## Fases y puertas

### Fase 0. Ticket

1. Leer el ticket en Jira y la sección de la HU en
   `docs/referencia/requisitos-billetera-v1.0.md`. Resumir en ≤ 10 líneas: objetivo,
   criterios de aceptación numerados, dependencias (¿están en `main`?), módulo.
2. Revisar en `specs/` y en el código si ya existe trabajo previo de la HU y decirlo.
3. **Puerta 0**: ¿tomamos el ticket? Opciones: tomarlo (asignar y pasar a In Progress),
   tomarlo sin tocar Jira, esperar a una dependencia, no tomarlo.
4. Crear la bitácora con la entrada de la puerta 0 y el nombre de la rama propuesta
   (`feat/PPA-n-<slug>`); la rama se crea solo si la persona lo decidió.

### Fase 1. Especificar

1. Anunciar el modelo y esperar confirmación.
2. Ejecutar el comando de especificar de Spec Kit (`/speckit-specify` en Claude,
   `$speckit-specify` en Codex) con la carpeta `specs/NNN-ppa-n-slug`
   (NNN = siguiente número libre; decirlo explícitamente).
3. **Puerta 1**: presentar las historias de usuario priorizadas, las suposiciones y lo que
   quedó fuera de alcance. Opciones: aprobar, cambiar prioridades, añadir o quitar alcance,
   pasar por aclarar.

### Fase 2. Aclarar (solo si la puerta 1 lo pidió o hay `NEEDS CLARIFICATION`)

Ejecutar el comando de aclarar de Spec Kit; cada respuesta de la persona es una entrada de
bitácora.

### Fase 3. Planificar

1. Anunciar el modelo y esperar confirmación.
2. Ejecutar el comando de planificar de Spec Kit. Antes de escribir `research.md`, listar las
   decisiones técnicas abiertas (máximo 5) con sus alternativas.
3. **Puerta 3**: una pregunta por decisión abierta. Las respuestas se escriben en
   `research.md` como "Decisión" y en la bitácora.

### Fase 4. Tareas

1. Anunciar el modelo y esperar confirmación.
2. Ejecutar el comando de tareas de Spec Kit.
3. **Puerta 4**: mostrar el conteo por fase y el MVP propuesto. Opciones: aprobar, recortar a
   MVP, reordenar, añadir tareas.

### Fase 5. Implementar

1. Anunciar el modelo y esperar confirmación.
2. Ejecutar el comando de implementar de Spec Kit **una fase de `tasks.md` por turno**
   (Setup, Foundational, cada historia, Polish). Pruebas antes de cada implementación, como
   exige la constitución.
3. **Puerta 5.x** al cerrar cada fase: resumen de lo hecho, validadores ejecutados y su
   resultado, y dudas. Opciones: continuar con la siguiente fase, ajustar algo antes, parar
   aquí. Si la fase tocó archivos ajenos a la historia, decirlo en la puerta.

### Fase 6. Cierre

1. Anunciar el modelo y esperar confirmación.
2. Correr los validadores completos (`api`: ruff, mypy, pytest; `webapp`: lint, typecheck,
   test, build; `e2e` si hubo cambios de pantalla) y una revisión de código del diff.
3. **Puerta 6**: resultados y hallazgos. Opciones: corregir hallazgos, commit por tarea,
   commit único, push y PR, dejar sin confirmar. Solo se ejecuta lo elegido.
4. Cerrar la bitácora con el resumen: fases, modelos usados, decisiones, qué quedó fuera.

## Retomar (`continuar`)

Leer `decisiones.md`, decir en qué puerta quedó y continuar desde la fase siguiente,
repitiendo el anuncio de modelo.

## Qué no hacer

- No decidir por la persona "para avanzar": si no responde, no se avanza.
- No resumir varias puertas en una sola pregunta.
- No borrar ni reescribir entradas de la bitácora; si una decisión cambia, se añade una
  entrada nueva que lo dice.

## Instalación por agente

- **Claude Code**: `.claude/skills/sdd/SKILL.md` ya está en el repo; se invoca con `/sdd PPA-n`.
  Los comandos `/speckit-*` están en `.claude/skills/`.
- **Codex**: `.agents/skills/sdd/SKILL.md` ya está en el repo, junto con los comandos de Spec
  Kit como skills (`.agents/skills/speckit-*/`, generados con
  `specify init --here --integration codex --integration-options="--skills"`); se invocan
  con `$sdd PPA-n` y `$speckit-specify`, `$speckit-plan`, etc.
- **Otro agente**: dale este documento como instrucción y usa los comandos de Spec Kit de tu
  herramienta (`specify init --here --ai <agente>`).
