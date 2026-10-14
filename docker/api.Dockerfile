# Imagen de la API (Flask + gunicorn). Contexto de build: raíz del repo.
# Reglas: .claude/rules/docker.md

FROM python:3.12-slim AS build
WORKDIR /build
COPY api/pyproject.toml ./
COPY api/app ./app
COPY api/migrations ./migrations
RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app
RUN groupadd --system --gid 10001 app && useradd --system --uid 10001 --gid app --home /srv/app app
WORKDIR /srv/app
COPY --from=build /install /usr/local
COPY --chown=app:app api/app ./app
COPY --chown=app:app api/migrations ./migrations
USER 10001:10001
EXPOSE 5000
# Sin curl en la imagen: el healthcheck usa la biblioteca estándar de Python.
HEALTHCHECK --interval=15s --timeout=3s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=3).status == 200 else 1)"]
# Aplica migraciones pendientes y arranca. APP_CONFIG decide la configuración (ver api.md).
CMD ["sh", "-c", "flask db upgrade && exec gunicorn -b 0.0.0.0:5000 -w 2 --access-logfile - 'app:create_app()'"]
