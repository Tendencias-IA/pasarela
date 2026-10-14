# Quality gates

Todo lo listado aquí es bloqueante: si falla, el PR no se fusiona. Las reglas en prosa de
`.claude/rules/` son guía; estos gates son la verificación. Definidos en
`.github/workflows/checks.yml` (título y secretos, en todo PR), `.github/workflows/ci.yml`
(jobs de código, solo cuando cambian `api/` o `webapp/`) y
`sonar-project.properties`.

## Gates del PR (CI)

| Gate | Comando | Umbral |
| --- | --- | --- |
| Formato y lint de la API | `ruff format --check . && ruff check .` | 0 hallazgos |
| Tipos de la API | `mypy app` | 0 errores |
| Pruebas y cobertura de la API | `pytest` (con `--cov-fail-under=90`) | 100 % tests verdes, cobertura ≥ 90 % líneas y ramas |
| Contrato API | `pytest tests/contract` | 0 respuestas fuera de `openapi.yaml` |
| Lint de la webapp | `npm run lint` (ESLint + Prettier `--check`) | 0 hallazgos |
| Tipos de la webapp | `npm run typecheck` | 0 errores |
| Unitarias de la webapp | `npm run test -- --coverage` | 100 % verdes; `shared/money` y `shared/api/problem.ts` al 100 % |
| Build de la webapp | `npm run build` | sin errores ni warnings de tamaño |
| E2E | `npm run e2e` | 100 % verdes en los dos proyectos |
| SonarQube | `sonar-scanner` + espera del quality gate | gate `Pasarela` en verde |
| Secretos | `gitleaks git .` (CLI en contenedor) | 0 hallazgos; falsos positivos históricos en `.gitleaksignore` |
| Título del PR | `type(PPA-n): descripción` | regex en CI |

## Quality gate de SonarQube ("Pasarela")

Condiciones sobre **código nuevo** cuando hay historial y sobre **código global** en el
primer análisis:

| Métrica | Condición |
| --- | --- |
| Cobertura | ≥ 90 % |
| Bugs | 0 |
| Vulnerabilidades | 0 |
| Security hotspots revisados | 100 % |
| Code smells de severidad blocker o critical | 0 |
| Líneas duplicadas | < 3 % |
| Calificación de mantenibilidad | A |
| Calificación de fiabilidad y seguridad | A |

Exclusiones permitidas (ya declaradas en `sonar-project.properties`): migraciones
Alembic, archivos generados (`types.gen.ts`), configuración de herramientas y pruebas
(que se analizan como `sonar.tests`, no como fuente).

El servidor es SonarQube Community en contenedor dentro del job de CI (el repo es
privado y SonarCloud gratuito solo cubre públicos). Si el repositorio se hace público, se
migra a SonarCloud cambiando solo las variables `SONAR_HOST_URL` y `SONAR_TOKEN`.

## Gates de revisión humana

- Al menos una aprobación de alguien distinto del autor.
- Diff ≤ 400 líneas significativas (sin contar generados ni `openapi.yaml`); si es
  mayor, se divide.
- La plantilla de `.github/PULL_REQUEST_TEMPLATE.md` completa y veraz: resumen, ticket,
  cambios y cómo probar. Una sección vacía o falsa es motivo para rechazar el PR.
- La carpeta `specs/<NNN-ppa-n-slug>/` con `spec.md`, `plan.md` y `tasks.md` está en el
  PR o enlazada desde él.

## Gates nocturnos (no bloquean el PR, bloquean el release)

Definidos en `.github/workflows/nightly.yml` (cron diario a la 01:00 de Bogotá y
ejecución manual).

- Prueba de carga con Locust (`api/tests/load/locustfile.py`): p95 ≤ 2 s en
  `GET /api/v1/wallet`, p95 ≤ 3 s en `GET /api/v1/movements`, `POST /api/v1/transfers` y
  `POST /api/v1/wallet/recharges`, 20 usuarios concurrentes (RNF-02). El locustfile
  verifica al final que ningún saldo sea negativo.
- `pip-audit --strict` y `npm audit --audit-level=high`: 0 vulnerabilidades altas o
  críticas.

## Cómo bajar un umbral

No se baja. Si una tarea no puede alcanzar el 90 %, se divide o se mejora la
testabilidad; si una regla de Sonar es un falso positivo, se marca como tal en Sonar
con justificación, no se excluye el archivo. Cambiar un umbral requiere PR a este
archivo, a `ci.yml` y a la constitución, con aprobación del equipo.
