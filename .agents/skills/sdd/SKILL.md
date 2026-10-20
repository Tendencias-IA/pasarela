---
name: sdd
description: Trabajo guiado de una historia (Jira PPA-n) con el ciclo SDD, deteniéndose en cada puerta para que la persona decida; recomienda el modelo por fase y deja una bitácora de decisiones.
---

# /sdd (adaptador para Codex y otros agentes)

Lee `docs/sdd-guiado.md` completo y síguelo al pie de la letra: es la única fuente de
verdad del procedimiento (fases, puertas, modelos, bitácora).

Lo específico de esta herramienta:

- **Puertas**: cada decisión se presenta como una pregunta cerrada en el chat, con 2 a 4
  opciones numeradas y una marcada como recomendada; no continúes hasta que la persona
  responda.
- **Modelo**: anuncia el recomendado por fase y pide a la persona que lo cambie en su
  herramienta (`/model` en Codex) y lo confirme; anota en la bitácora el que se usó.
- **Comandos de Spec Kit**: las skills hermanas de `.agents/skills/`: `$speckit-specify`,
  `$speckit-clarify`, `$speckit-plan`, `$speckit-tasks`, `$speckit-implement`.
- **Jira**: léelo con la integración disponible o pide a la persona que pegue el ticket; no
  cambies su estado sin una decisión en puerta.
