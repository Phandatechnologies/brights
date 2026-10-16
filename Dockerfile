# Brights production image: one container serving the Django API and the built React app.
# Build:  docker build -t brights .
# Run:    docker run -p 8000:8000 --env-file backend/.env.production brights

# --- Stage 1: build the React frontend --------------------------------------------------
FROM node:22-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# --- Stage 2: the Python application ----------------------------------------------------
FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    STATIC_MANIFEST=true \
    FRONTEND_DIST=/app/frontend/dist

WORKDIR /app/backend
COPY backend/requirements.txt ./
RUN pip install -r requirements.txt

COPY backend/ ./
COPY --from=frontend /app/frontend/dist /app/frontend/dist

# Collect admin/static files at build time. The dummy values are only for this step;
# real secrets are given to the container at runtime, never baked into the image.
RUN DJANGO_SECRET_KEY=build-only DB_NAME=build DB_USER=build DB_PASSWORD=build \
    python manage.py collectstatic --noinput

# Run as an unprivileged user, not root.
RUN useradd --create-home --uid 10001 brights && chown -R brights /app
USER brights

EXPOSE 8000
CMD ["sh", "start.sh"]
