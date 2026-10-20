---
name: "sdd"
description: "Trabajo guiado de una historia (Jira PPA-n) con el ciclo SDD, deteniéndose en cada puerta para que la persona decida; recomienda el modelo por fase y deja una bitácora de decisiones."
argument-hint: "PPA-n [continuar]"
compatibility: "Requiere Spec Kit (.specify/) y las skills /speckit-*"
metadata:
  author: "equipo pasarela"
  source: "docs/sdd-guiado.md"
user-invocable: true
disable-model-invocation: true
---

# /sdd (adaptador para Claude Code)

Lee `docs/sdd-guiado.md` completo y síguelo al pie de la letra: es la única fuente de
verdad del procedimiento (fases, puertas, modelos, bitácora). Argumentos recibidos:

```text
$ARGUMENTS
```

Lo específico de Claude Code:

- **Puertas**: cada pregunta cerrada se hace con la herramienta `AskUserQuestion` (2 a 4
  opciones, una marcada "(Recommended)"). Si la persona elige "Other", su texto es la decisión.
- **Modelo**: no puedes cambiar el modelo de tu propia sesión; pide a la persona que lo haga
  en el menú de modelo de la app (`/model` en la terminal) y espera su confirmación. Nombres:
  Sonnet (`claude-sonnet-5-5`), Opus (`claude-opus-5-5`), Fable (`claude-fable-5-1`).
- **Comandos de Spec Kit**: `/speckit-specify`, `/speckit-clarify`, `/speckit-plan`,
  `/speckit-tasks`, `/speckit-implement`, invocados con la herramienta `Skill`.
- **Jira**: herramientas de Atlassian (`getJiraIssue`, `editJiraIssue`, `transitionJiraIssue`),
  solo cuando una puerta lo decidió.
- **Revisión de cierre**: `/code-review` sobre el diff de la rama.
