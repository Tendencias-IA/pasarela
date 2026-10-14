# Git, commits y pull requests

Aplica a todo el repositorio. `main` es la única rama larga, siempre desplegable, y de
ella sale producción. Ambientes: local y producción.

## Ramas

- Formato `<type>/PPA-<n>-<descripcion-corta>`: `feat/PPA-6-preparar-transferencia`,
  `fix/PPA-7-saldo-negativo-concurrencia`, `docs/PPA-14-reglas-sdd`. Mismo `type` que
  el commit (`feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `build`, `ci`).
- Una rama por ticket, creada desde `main` actualizado. Vida máxima: días. Se sincroniza
  con `main` a diario mediante `git rebase main` mientras es privada; con `git merge
  main` si alguien más la tiene.
- Se borra tras el merge.
- Nadie hace push directo a `main`; está protegida (PR obligatorio, 1 aprobación, CI
  verde, historia lineal).

## Commits

- Formato de una línea: `type(PPA-n): descripción en minúscula e imperativo`, máximo
  72 caracteres. Varios tickets: `fix(PPA-6, PPA-7): ...`. Cambio incompatible:
  `feat(PPA-n)!: ...`.
- Un cambio por commit. Pruebas junto con lo que prueban; refactor separado del cambio
  de comportamiento; dependencias (`pyproject.toml`, `package-lock.json`) en commit
  propio `build(PPA-n): ...`; migraciones en commit propio junto con su modelo.
- Cada commit deja el árbol verde (`pytest`, `npm run test`). Razón: `git bisect` y
  `git revert` solo sirven si cada commit es consistente.
- Cuerpo solo si aporta lo que el diff no dice (una restricción, un despliegue previo
  necesario). Sin trailers de herramientas ni pies "generado por": el autor del commit es
  responsable del código, lo haya escrito una IA o no.

| Incorrecto | Correcto |
| --- | --- |
| `fix: cambios` | `fix(PPA-7): bloquear billeteras en orden ascendente para evitar deadlock` |
| `feat: add transfer` | `feat(PPA-6): validar destinatario y rango de monto al preparar transferencia` |
| `update tests` | `test(PPA-8): cubrir reintento con misma idempotency-key` |

## Antes de hacer push

1. `ruff format . && ruff check . && mypy app && pytest` en `api/`;
   `npm run lint && npm run typecheck && npm run test` en `webapp/`.
2. Leer el diff completo (`git diff main...HEAD`): sin `print`, sin `.only`, sin
   `TODO` sin ticket, sin secretos, sin archivos ajenos a la tarea.
3. `git log --oneline main..HEAD`: cada línea cumple el formato y es un solo cambio.
4. `git push -u origin <rama>`. Para reescribir una rama propia ya publicada:
   `git push --force-with-lease`, nunca `--force`.

## Pull request

- Título igual que un commit: `type(PPA-n): descripción`. El CI lo valida.
- Se usa la plantilla de `.github/PULL_REQUEST_TEMPLATE.md` completa. El cuerpo lleva el
  razonamiento: qué cambia, por qué, qué se descartó, cómo se verificó, enlace a Jira y
  a `specs/<NNN-ppa-n-slug>/`.
- Tamaño: ≤ 400 líneas significativas. Una HU grande se divide en PRs por tarea de
  `tasks.md` (por ejemplo, migración y modelo primero, servicio y pruebas después,
  UI al final), cada uno útil por sí mismo.
- Revisión: al menos una aprobación de alguien distinto del autor; responder en un día
  hábil; comentarios con severidad (`blocking`, `consider`, `nit`, `question`); se
  critica el código, no a la persona.
- El autor verifica cada comentario contra el código antes de aceptarlo o rebatirlo, y
  responde con el commit que lo resuelve. Durante la revisión se añaden commits, no se
  reescribe la rama.
- Merge con **squash** desde GitHub. La descripción del PR se convierte en el mensaje del
  commit en `main`, así que se escribe con ese cuidado. Tras el merge, el ticket de Jira
  pasa a su estado final con el enlace al PR.

## Qué no hacer

- No mezclar en un PR cambios de reglas (`.claude/rules`, constitución) con
  implementación de una HU: las reglas tienen su propio PR y revisión.
- No subir `.env`, dumps de base de datos, capturas con datos ni `node_modules`.
- No cerrar un PR con "arreglado después": el PR se fusiona cuando está terminado.
