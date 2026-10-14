---
paths:
  - "docker/**"
  - "docker-compose.yml"
  - ".dockerignore"
  - "**/Dockerfile"
---

# Contenedores: imágenes y compose

Aplica a `docker/`, `docker-compose.yml` y cualquier `Dockerfile`. Las mismas imágenes
sirven para desarrollo local, E2E y producción; solo cambia `APP_CONFIG` y las variables
de entorno. Ticket de origen: PPA-24.

## Uso

```bash
cp .env.example .env                      # una vez; .env nunca se versiona
docker compose up -d mysql                # desarrollo con la API y la webapp fuera de Docker
docker compose --profile app up --build   # todo en contenedores: http://127.0.0.1:8080
docker compose logs -f api | jq           # logs JSON de la API
```

## Imágenes

- Base fijada por versión mayor y variante: `python:3.12-slim`, `node:22-alpine`,
  `nginx:1.27-alpine`. Nunca `latest`. Razón: una base que cambia sola rompe builds
  reproducibles y el CI deja de ser comparable entre ejecuciones.
- Multi-stage obligatorio: la etapa final no contiene compiladores, `npm`, código de
  pruebas ni archivos de desarrollo. El contexto de build es la raíz del repo y
  `.dockerignore` deja entrar solo `api/`, `webapp/` y `docker/`.
- La etapa final corre con usuario sin privilegios (`USER app` en la API; nginx ya
  degrada privilegios). Nunca `USER root` en la etapa final.
- `HEALTHCHECK` en toda imagen de servicio, contra `/health`. Sin instalar `curl` ni
  paquetes `apt` en la imagen de la API: el healthcheck usa la biblioteca estándar de
  Python. Si hiciera falta un paquete del sistema, se fija versión y se limpia
  `/var/lib/apt/lists` en la misma capa.
- Sin secretos en la imagen ni en `Dockerfile`: `SECRET_KEY`, `DATABASE_URL` y
  contraseñas llegan por variables de entorno en tiempo de ejecución. `COPY . .` está
  prohibido sin `.dockerignore` que excluya `.env`.
- Logs a `stdout`/`stderr` en JSON (ver `observability.md`); gunicorn con
  `--access-logfile -`. Nada se escribe en archivos dentro del contenedor.
- La API aplica `flask db upgrade` al arrancar y luego arranca gunicorn con `exec`, para
  que reciba las señales de parada. Razón: la base de datos siempre está al día con el
  código desplegado y no hay un paso manual de migración.
- Un solo origen: nginx sirve la webapp y reenvía `/api/` y `/health` a `api:5000`. Así
  la cookie de sesión `SameSite=Lax` funciona sin CORS (ver `security.md`). No se abre
  CORS para "probar rápido".
- Los Dockerfiles pasan `hadolint` sin errores (`hadolint docker/*.Dockerfile`).

## Compose

- `docker-compose.yml` es solo para desarrollo local y E2E; producción despliega las
  mismas imágenes con las variables de su entorno, no este archivo.
- Puertos publicados solo en `127.0.0.1` y configurables por `.env` (`MYSQL_PORT`, `API_PORT`,
  `WEBAPP_PORT`) para convivir con otros proyectos; MySQL nunca se expone fuera de la máquina.
- Variables obligatorias con `${VAR:?mensaje}` para que compose falle con un mensaje
  claro si falta `.env`, en lugar de arrancar con una contraseña vacía.
- `api` espera a `mysql` con `condition: service_healthy`; no se usan `sleep` ni
  reintentos a mano.
- Los servicios de aplicación van bajo el perfil `app` para que `docker compose up -d
  mysql` siga siendo el camino rápido de desarrollo.

## Contrato con `api/` y `webapp/`

- `api/pyproject.toml` permite `pip install .` sin extras de desarrollo (los extras
  `[dev]` no entran en la imagen).
- `webapp/package.json` tiene `build` que escribe en `dist/`.
- Ninguna de las dos carpetas tiene `Dockerfile` propio: las imágenes viven en `docker/`
  y toman el contexto desde la raíz.
