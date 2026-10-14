## Ticket y especificación

- Jira: PPA-
- Spec Kit: `specs/<NNN-ppa-n-slug>/` (spec.md, plan.md, tasks.md incluidos o enlazados)
- Historia(s) y criterios cubiertos: HU-__ CA-__, CA-__

## Qué cambia y por qué

<!-- Qué hace este PR, qué alternativa se descartó y por qué. Este texto se convierte en el
     mensaje del commit en main al hacer squash. -->

## Cómo se verificó

<!-- Comandos ejecutados, cobertura resultante, capturas si hay UI, salida relevante. -->

- Cobertura backend: __ %
- Playwright: desktop ☐ móvil ☐

## Checklist (marcar solo lo que es verdad)

- [ ] El Constitution Check de `plan.md` pasa sin desviaciones, o están justificadas en Complexity Tracking.
- [ ] Cada criterio de aceptación cubierto tiene un test que lo cita por su código.
- [ ] Los tests nuevos fallaron antes del cambio y pasan después.
- [ ] `ruff`, `mypy`, `eslint`, `tsc` sin hallazgos en local.
- [ ] Montos con `Decimal`/cadena; sin `float`.
- [ ] Operaciones de saldo en una sola transacción con bloqueo; idempotencia donde aplica.
- [ ] Checklist de seguridad de `.claude/rules/security.md` revisado.
- [ ] Sin secretos, datos reales ni archivos ajenos a la tarea.
- [ ] `openapi.yaml` actualizado si cambió un endpoint; migración incluida si cambió el esquema.
- [ ] Diff ≤ 400 líneas significativas, o se explica por qué no se dividió.
- [ ] Reglas o ADRs actualizados si este cambio altera una convención.
