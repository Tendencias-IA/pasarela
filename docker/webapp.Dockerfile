# Imagen de la webapp: build con Vite y servido por nginx, que hace proxy de /api a la API
# para mantener un solo origen. Contexto de build: raíz del repo. Reglas: .claude/rules/docker.md

FROM node:22-alpine AS build
WORKDIR /build
COPY webapp/package.json webapp/package-lock.json ./
RUN npm ci
COPY webapp/ ./
RUN npm run build

FROM nginx:1.27-alpine
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /build/dist /usr/share/nginx/html
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=3s --retries=3 \
    CMD ["wget", "-qO-", "http://127.0.0.1:8080/"]
