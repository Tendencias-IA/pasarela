# Pasarela · Billetera Digital

Prototipo académico de billetera digital (materia Tendencias de IA, Universidad El Bosque).
Permite registrar una cuenta, iniciar sesión, consultar saldo, transferir dinero ficticio
entre usuarios, recargar saldo simulado, consultar el historial y gestionar el perfil.

El proyecto se desarrolla con **Spec-Driven Development (SDD)** usando
[Spec Kit](https://github.com/github/spec-kit) y herramientas de IA. Toda historia de
usuario pasa por `spec → plan → tasks → implement` antes de escribir código.

## Mapa del repositorio

| Ruta | Qué contiene |
| --- | --- |
| `AGENTS.md` / `CLAUDE.md` | Punto de entrada para cualquier herramienta de IA. Léelo primero. |
| `.specify/memory/constitution.md` | Constitución del proyecto: principios y gates innegociables. |
| `.claude/rules/` | Reglas por tema: arquitectura, diseño de API, api, webapp, testing, seguridad, observabilidad, Git, quality gates, docker. |
| `.claude/skills/speckit-*` | Comandos de Spec Kit (`/speckit-specify`, `/speckit-plan`, `/speckit-tasks`, `/speckit-implement`). |
| `docs/sdd-workflow.md` | Guía paso a paso para tomar un ticket de Jira y ejecutar el ciclo SDD. |
| `docs/adr/` | Decisiones de arquitectura (ADR). |
| `docs/referencia/` | Especificación de requisitos e historias de usuario (fuente de verdad del negocio). |
| `specs/` | Una carpeta por historia implementada: `spec.md`, `plan.md`, `tasks.md`. |
| `api/` | API en Python + Flask: app factory, configuraciones, errores RFC 9457, logging JSON, `/health`, migraciones y pruebas. |
| `webapp/` | Webapp en React + Vite + TypeScript con Ionic: panel inicial, `/recargar` (HU-08), cliente HTTP, Vitest, Playwright. |
| `.github/` | Plantilla de PR, CODEOWNERS y pipeline de CI. |
| `docker-compose.yml`, `docker/` | MySQL local e imágenes de `api` y `webapp` (ver `.claude/rules/docker.md`). |

## Stack

- `api/`: Python 3.12, Flask 3, SQLAlchemy 2, Alembic, MySQL 8.
- `webapp/`: React 18, Vite, TypeScript, Vitest, Playwright.
- Calidad: pytest con cobertura ≥ 90 %, Ruff, mypy, ESLint, Prettier, SonarQube.

## Ejecutar con Docker

```bash
cp .env.example .env                      # una vez; ajusta los puertos si alguno está ocupado
docker compose --profile app up --build   # MySQL + API + webapp en http://127.0.0.1:8080
docker compose up -d mysql                # solo la base de datos, para desarrollar fuera de Docker
```

Detalles en `.claude/rules/docker.md`.

## Gestión

- Backlog: [Jira PPA](https://wmss.atlassian.net/jira/software/projects/PPA/boards/68/backlog).
- Historias HU-01 a HU-13 = tickets PPA-1 a PPA-13.
- Reglas y SDD: épica PPA-14.

## Cómo empezar

1. Clona el repositorio y abre Claude Code en la raíz. Requisitos: Python 3.12 (`uv venv --python 3.12`), Node 22 (`nvm use`), Docker.
2. Lee `AGENTS.md` y `docs/sdd-workflow.md`.
3. Toma un ticket PPA-n y sigue la guía.
