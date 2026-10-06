# Contexto de build: la raíz del repo (ver docker-compose.yml), porque esta
# etapa necesita también frontend/. En local no cambia nada: docker-compose
# monta ./backend:/app como volumen, así que esto queda tapado en tiempo de
# ejecución igual que antes; esta imagen autosuficiente solo es necesaria
# para desplegar donde no hay ese bind mount (p. ej. Render).
FROM node:20-alpine AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY --from=frontend-build /backend/app/static ./app/static

COPY backend/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
