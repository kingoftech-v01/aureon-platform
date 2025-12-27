#!/bin/bash
# Docker entrypoint script for Aureon SaaS Platform

set -e

echo "===== Aureon Platform Startup ====="
echo "Environment: ${DJANGO_SETTINGS_MODULE:-config.settings}"

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
while ! pg_isready -h "${DB_HOST:-db}" -p "${DB_PORT:-5432}" -U "${DB_USER:-finance_user}" > /dev/null 2>&1; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done
echo "PostgreSQL is ready!"

# Wait for Redis to be ready
echo "Waiting for Redis..."
until redis-cli -h "${REDIS_HOST:-redis}" -p "${REDIS_PORT:-6379}" ping > /dev/null 2>&1; do
  echo "Redis is unavailable - sleeping"
  sleep 1
done
echo "Redis is ready!"

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Create default notification templates
echo "Creating notification templates..."
python manage.py create_notification_templates || echo "Templates already exist or error occurred"

# Collect static files
if [ "$COLLECT_STATIC" = "true" ]; then
  echo "Collecting static files..."
  python manage.py collectstatic --noinput
fi

# Create superuser if credentials provided
if [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  echo "Creating superuser..."
  python manage.py createsuperuser \
    --noinput \
    --email "$DJANGO_SUPERUSER_EMAIL" \
    || echo "Superuser already exists"
fi

echo "===== Starting Application ====="
exec "$@"
