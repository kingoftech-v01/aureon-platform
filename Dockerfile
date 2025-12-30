# Multi-stage Dockerfile for Aureon SaaS Platform
# Rhematek Production Shield

# Stage 1: Build React Frontend
FROM node:20-alpine as frontend-build

WORKDIR /frontend

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci --legacy-peer-deps

# Copy frontend source
COPY frontend/ .

# Build the React app
RUN npm run build

# Stage 2: Build stage for Python dependencies
FROM python:3.11-slim as python-build

WORKDIR /app

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    libpng-dev \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 3: Runtime stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings \
    PORT=8000

# Create app user
RUN groupadd -r aureon && useradd -r -g aureon aureon

# Install runtime dependencies (including redis-tools for healthcheck)
RUN apt-get update && apt-get install -y \
    libpq5 \
    libjpeg62-turbo \
    libpng16-16 \
    libmagic1 \
    postgresql-client \
    redis-tools \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy Python dependencies from build stage
COPY --from=python-build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=python-build /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Copy React build from frontend stage to staticfiles/dashboard
COPY --from=frontend-build /frontend/dist /app/staticfiles/dashboard

# Create necessary directories
RUN mkdir -p /app/staticfiles /app/media /app/logs && \
    chown -R aureon:aureon /app

# Copy entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Switch to app user
USER aureon

# Expose port (configurable via env)
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/api/health/ || exit 1

# Entrypoint
ENTRYPOINT ["/docker-entrypoint.sh"]

# Default command
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "2", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-"]
