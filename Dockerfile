# ============================================================
# AUREON SaaS Platform - Production Dockerfile
# Multi-stage build with security hardening
# ============================================================

# ============================================================
# Stage 1: Dashboard Frontend Build (React/Vite)
# ============================================================
FROM node:20-alpine AS dashboard-build

WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm install --legacy-peer-deps --no-audit --no-fund

COPY frontend/ .
RUN npm run build

# ============================================================
# Stage 2: Python Dependencies Builder
# ============================================================
FROM python:3.11-slim AS python-builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    libpng-dev \
    libffi-dev \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip wheel setuptools

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ============================================================
# Stage 3: Production Runtime
# ============================================================
FROM python:3.11-slim AS production

LABEL maintainer="Rhematek Solutions <dev@rhematek-solutions.com>"
LABEL version="3.0.0"
LABEL description="Aureon SaaS Platform - Production Image"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=config.settings \
    PORT=8000 \
    PATH="/opt/venv/bin:$PATH"

RUN groupadd --gid 1000 aureon && \
    useradd --uid 1000 --gid aureon --shell /bin/bash --create-home aureon

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libjpeg62-turbo \
    libpng16-16 \
    libmagic1 \
    postgresql-client \
    redis-tools \
    curl \
    netcat-openbsd \
    ca-certificates \
    tini \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /app

# Copy virtual environment from builder
COPY --from=python-builder /opt/venv /opt/venv

# Copy backend code
COPY --chown=aureon:aureon backend/ .

# Copy .env from project root
COPY --chown=aureon:aureon .env .env

# Copy React dashboard build to static/dashboard
COPY --from=dashboard-build --chown=aureon:aureon /frontend/dist /app/static/dashboard

# Create necessary directories
RUN mkdir -p /app/staticfiles /app/mediafiles /app/logs && \
    chown -R aureon:aureon /app

# Copy and set permissions for entrypoint
COPY --chown=aureon:aureon docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Remove unnecessary files
RUN rm -rf /app/.git /app/tests /app/*.md 2>/dev/null || true

USER aureon

EXPOSE ${PORT}

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/health/ || exit 1

ENTRYPOINT ["tini", "--", "/docker-entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]
