# ============================================================
# AUREON SaaS Platform - Production Dockerfile
# Multi-stage build with security hardening
# Rhematek Production Shield
# ============================================================

# ============================================================
# Stage 1: Frontend Build (React/Vite)
# ============================================================
FROM node:20-alpine AS frontend-build

# Set working directory
WORKDIR /frontend

# Install dependencies first (better caching)
COPY frontend/package*.json ./

# Install dependencies (npm install for flexibility, generates lock file if missing)
RUN npm install --legacy-peer-deps --no-audit --no-fund

# Copy frontend source
COPY frontend/ .

# Build the React app for production
RUN npm run build

# ============================================================
# Stage 2: Python Dependencies Builder
# ============================================================
FROM python:3.11-slim AS python-builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    libpng-dev \
    libffi-dev \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install wheel
RUN pip install --no-cache-dir --upgrade pip wheel setuptools

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ============================================================
# Stage 3: Production Runtime
# ============================================================
FROM python:3.11-slim AS production

# Labels for container metadata
LABEL maintainer="Rhematek Solutions <dev@rhematek-solutions.com>"
LABEL version="2.2.0"
LABEL description="Aureon SaaS Platform - Production Image (Rhematek Production Shield)"

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=config.settings \
    PORT=8000 \
    PATH="/opt/venv/bin:$PATH"

# Create non-root user for security
RUN groupadd --gid 1000 aureon && \
    useradd --uid 1000 --gid aureon --shell /bin/bash --create-home aureon

# Install runtime dependencies only
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

# Set work directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=python-builder /opt/venv /opt/venv

# Copy application code
COPY --chown=aureon:aureon . .

# Copy React build from frontend stage
COPY --from=frontend-build --chown=aureon:aureon /frontend/dist /app/staticfiles/dashboard

# Create necessary directories with proper permissions
RUN mkdir -p /app/staticfiles /app/media /app/logs && \
    chown -R aureon:aureon /app

# Copy and set permissions for entrypoint
COPY --chown=aureon:aureon docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Remove unnecessary files for smaller attack surface
RUN rm -rf \
    /app/.git \
    /app/.github \
    /app/tests \
    /app/*.md \
    /app/Makefile \
    /app/.env.example \
    /app/docker \
    2>/dev/null || true

# Switch to non-root user
USER aureon

# Expose port
EXPOSE ${PORT}

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/health/ || exit 1

# Use tini as init system for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--", "/docker-entrypoint.sh"]

# Default command - Gunicorn with optimized settings
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--threads", "2", \
     "--worker-class", "gthread", \
     "--worker-connections", "1000", \
     "--max-requests", "10000", \
     "--max-requests-jitter", "1000", \
     "--timeout", "30", \
     "--keep-alive", "5", \
     "--graceful-timeout", "30", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--capture-output", \
     "--enable-stdio-inheritance"]

# ============================================================
# Stage 4: Development Runtime (optional build target)
# ============================================================
FROM production AS development

# Switch to root for development setup
USER root

# Install development dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Install development Python packages
RUN pip install --no-cache-dir \
    django-debug-toolbar \
    ipython \
    ipdb \
    watchdog

# Switch back to aureon user
USER aureon

# Development command with auto-reload
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
