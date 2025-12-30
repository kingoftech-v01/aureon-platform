#!/bin/bash
# ============================================================
# AUREON SaaS Platform - Docker Entrypoint
# Rhematek Production Shield + Scale8
# ONE COMMAND DEPLOYMENT - Everything is automatic
# ============================================================

set -e

echo "=============================================="
echo "  AUREON PLATFORM STARTUP"
echo "  Rhematek Production Shield"
echo "=============================================="
echo "Environment: ${DJANGO_SETTINGS_MODULE:-config.settings}"
echo "Port: ${PORT:-8000}"

# Function to wait for a service
wait_for_service() {
    local host="$1"
    local port="$2"
    local service="$3"
    local max_retries="${4:-30}"
    local retry=0

    echo "Waiting for $service ($host:$port)..."

    while [ $retry -lt $max_retries ]; do
        if nc -z "$host" "$port" 2>/dev/null; then
            echo "$service is ready!"
            return 0
        fi
        retry=$((retry + 1))
        echo "$service is unavailable - sleeping (attempt $retry/$max_retries)"
        sleep 2
    done

    echo "WARNING: $service did not become available after $max_retries attempts"
    return 1
}

# Extract host and port from DATABASE_URL if set
if [ -n "$DATABASE_URL" ]; then
    # Parse DATABASE_URL: postgresql://user:pass@host:port/db
    DB_HOST=$(echo "$DATABASE_URL" | sed -n 's|.*@\([^:/]*\).*|\1|p')
    DB_PORT=$(echo "$DATABASE_URL" | sed -n 's|.*:\([0-9]*\)/.*|\1|p')
fi

# Set defaults
DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
REDIS_HOST="${REDIS_HOST:-redis}"
REDIS_PORT="${REDIS_PORT:-6379}"

# Wait for PostgreSQL
if [ -n "$DB_HOST" ]; then
    wait_for_service "$DB_HOST" "$DB_PORT" "PostgreSQL" 60 || {
        echo "Continuing without PostgreSQL check..."
    }
fi

# Wait for Redis (if configured)
if [ -n "$REDIS_URL" ] || [ -n "$REDIS_HOST" ]; then
    # Extract Redis host from REDIS_URL if set
    if [ -n "$REDIS_URL" ]; then
        REDIS_HOST=$(echo "$REDIS_URL" | sed -n 's|.*@\([^:/]*\).*|\1|p')
        REDIS_PORT=$(echo "$REDIS_URL" | sed -n 's|.*:\([0-9]*\)/.*|\1|p')
        REDIS_HOST="${REDIS_HOST:-redis}"
        REDIS_PORT="${REDIS_PORT:-6379}"
    fi

    wait_for_service "$REDIS_HOST" "$REDIS_PORT" "Redis" 30 || {
        echo "Continuing without Redis check..."
    }
fi

# Run database migrations
echo ""
echo "Running database migrations..."
python manage.py migrate --noinput || {
    echo "WARNING: Migration failed, continuing..."
}

# Collect static files (always in production)
echo ""
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear 2>/dev/null || {
    echo "WARNING: Static file collection failed, continuing..."
}

# Create notification templates
echo ""
echo "Creating notification templates..."
python manage.py create_notification_templates 2>/dev/null || {
    echo "Templates already exist or command not available"
}

# Create superuser if credentials provided
if [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo ""
    echo "Creating superuser..."
    python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
email = '$DJANGO_SUPERUSER_EMAIL'
password = '$DJANGO_SUPERUSER_PASSWORD'
if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(email=email, password=password)
    print(f'Superuser {email} created')
else:
    print(f'Superuser {email} already exists')
" 2>/dev/null || echo "Superuser creation skipped"
fi

# Seed demo data if SEED_DEMO_DATA is set
if [ "$SEED_DEMO_DATA" = "true" ] || [ "$SEED_DEMO_DATA" = "1" ]; then
    echo ""
    echo "Seeding demo data..."
    python manage.py seed_demo_data 2>/dev/null || echo "Demo data seeding skipped"
fi

echo ""
echo "=============================================="
echo "  APPLICATION READY"
echo "  Starting: $@"
echo "=============================================="

exec "$@"
