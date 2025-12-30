# Deployment Guide - Aureon SaaS Platform

**Version**: 2.2.0
**Last Updated**: December 2025
**Platform**: Aureon by Rhematek Solutions
**Security**: Rhematek Production Shield

---

## Dockploy Deployment (One Command)

Deploy Aureon with a **single command**. The entrypoint script handles everything automatically.

### Step 1: Configure Environment Variables in Dockploy

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Django secret key (generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`) |
| `DEBUG` | Yes | Set to `False` for production |
| `ALLOWED_HOSTS` | Yes | Your domain (e.g., `aureon.yourdomain.com`) |
| `DATABASE_URL` | Yes | PostgreSQL URL: `postgresql://user:pass@host:5432/dbname` |
| `REDIS_URL` | Yes | Redis URL: `redis://:password@host:6379/0` |
| `CELERY_BROKER_URL` | Yes | Redis URL for Celery: `redis://:password@host:6379/1` |
| `STRIPE_PUBLIC_KEY` | Yes | Stripe publishable key |
| `STRIPE_SECRET_KEY` | Yes | Stripe secret key |
| `DJSTRIPE_WEBHOOK_SECRET` | Yes | Stripe webhook signing secret |
| `EMAIL_HOST_USER` | No | SMTP username |
| `EMAIL_HOST_PASSWORD` | No | SMTP password |
| `DJANGO_SUPERUSER_EMAIL` | No | Auto-create admin (set email) |
| `DJANGO_SUPERUSER_PASSWORD` | No | Auto-create admin (set password) |
| `SEED_DEMO_DATA` | No | Set to `true` to seed demo data on first run |

### Step 2: Deploy

```bash
docker compose -f docker-compose.prod.yml up -d
```

**That's it!** The container automatically:
1. Waits for PostgreSQL and Redis to be ready
2. Runs database migrations
3. Collects static files
4. Creates notification templates
5. Creates superuser (if `DJANGO_SUPERUSER_EMAIL` and `DJANGO_SUPERUSER_PASSWORD` are set)
6. Seeds demo data (if `SEED_DEMO_DATA=true`)
7. Starts Gunicorn with optimized settings

### Step 3: Verify Deployment

```bash
# Check health endpoint
curl https://your-domain.com/api/health/

# View logs
docker compose -f docker-compose.prod.yml logs -f web
```

### What Gets Deployed

| Service | Description |
|---------|-------------|
| `web` | Django + Gunicorn (4 workers, 2 threads) |
| `celery-high` | High priority task worker |
| `celery-medium` | Medium priority task worker |
| `celery-low` | Low priority + batch tasks |
| `celery-beat` | Task scheduler |
| `db-master` | PostgreSQL 16 primary |
| `db-replica` | PostgreSQL read replica |
| `redis-cache` | Redis for caching |
| `redis-queue` | Redis for Celery broker |
| `pgbouncer` | Connection pooling |
| `nginx` | Reverse proxy with SSL |
| `prometheus` | Metrics collection |
| `grafana` | Monitoring dashboard |

---

## Table of Contents

1. [Dockploy Deployment](#dockploy-deployment-one-command)
2. [Server Requirements](#server-requirements)
3. [Prerequisites](#prerequisites)
4. [Docker Deployment](#docker-deployment)
5. [Manual Deployment](#manual-deployment)
6. [Nginx Configuration](#nginx-configuration)
7. [SSL/TLS Setup](#ssltls-setup)
8. [Database Configuration](#database-configuration)
9. [Redis Configuration](#redis-configuration)
10. [Celery Workers](#celery-workers)
11. [Monitoring Setup](#monitoring-setup)
12. [Backup Procedures](#backup-procedures)
13. [Troubleshooting](#troubleshooting)
14. [Deployment Checklist](#deployment-checklist)

---

## Server Requirements

### Minimum Specifications

| Resource | Requirement | Notes |
|----------|-------------|-------|
| CPU | 2 cores | Intel/AMD x64 |
| RAM | 4 GB | 8 GB recommended |
| Storage | 50 GB SSD | NVMe preferred |
| OS | Ubuntu 22.04 LTS | Or 20.04 LTS |
| Network | Static IP | Required for production |
| Bandwidth | 1 Gbps | Minimum |

### Recommended Specifications (Production)

| Resource | Requirement | Notes |
|----------|-------------|-------|
| CPU | 4+ cores | More for high traffic |
| RAM | 8-16 GB | Scale with users |
| Storage | 100+ GB SSD | NVMe recommended |
| OS | Ubuntu 22.04 LTS | Latest LTS |
| Network | Static IP + Firewall | Cloud provider firewall |
| Bandwidth | 1 Gbps+ | CDN recommended |

### Software Requirements

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.11+ | Application runtime |
| PostgreSQL | 15+ | Primary database |
| Redis | 7+ | Cache and message broker |
| Nginx | 1.18+ | Reverse proxy |
| Docker | 24+ | Containerization |
| Docker Compose | 2.0+ | Container orchestration |
| Node.js | 18+ | Frontend build |
| Git | 2.30+ | Version control |
| Certbot | Latest | SSL certificates |

---

## Prerequisites

### Required Accounts

Before deployment, ensure you have:

1. **Server Access**: SSH access to Ubuntu server
2. **Domain Name**: DNS configured to point to server IP
3. **Stripe Account**: Production API keys from [Stripe Dashboard](https://dashboard.stripe.com)
4. **Email Provider**: SMTP credentials (AWS SES, SendGrid, or Gmail)
5. **SSL Certificate**: Let's Encrypt (free) or commercial certificate

### Initial Server Setup

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y \
    build-essential \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    postgresql-15 \
    postgresql-server-dev-15 \
    redis-server \
    nginx \
    git \
    curl \
    supervisor \
    libpq-dev \
    libjpeg-dev \
    libpng-dev \
    libmagic1 \
    certbot \
    python3-certbot-nginx

# Enable and start services
sudo systemctl enable postgresql redis-server nginx
sudo systemctl start postgresql redis-server nginx
```

---

## Docker Deployment

### Quick Start with Docker

This is the recommended deployment method for production. The entrypoint script handles all initialization automatically.

#### Step 1: Clone Repository

```bash
# Create application directory
sudo mkdir -p /opt/aureon
cd /opt/aureon

# Clone repository
git clone https://github.com/rhematek-solutions/aureon.git .
```

#### Step 2: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit environment variables
nano .env
```

**Essential Environment Variables**:

```ini
# Django Core
SECRET_KEY=your-very-long-secret-key-min-50-characters-here
DEBUG=False
ALLOWED_HOSTS=aureon.yourdomain.com

# Database
DATABASE_URL=postgresql://aureon_user:your-password@db-master:5432/aureon_db

# Redis
REDIS_URL=redis://:your-redis-password@redis-cache:6379/0
CELERY_BROKER_URL=redis://:your-redis-password@redis-queue:6379/1

# Stripe
STRIPE_PUBLIC_KEY=pk_live_xxx
STRIPE_SECRET_KEY=sk_live_xxx
DJSTRIPE_WEBHOOK_SECRET=whsec_xxx

# Auto-create Admin (optional)
DJANGO_SUPERUSER_EMAIL=admin@yourdomain.com
DJANGO_SUPERUSER_PASSWORD=your-admin-password

# Seed Demo Data (optional)
SEED_DEMO_DATA=true
```

#### Step 3: Deploy (Single Command)

```bash
docker compose -f docker-compose.prod.yml up -d
```

**Everything is automatic!** The entrypoint script:
- Waits for PostgreSQL and Redis
- Runs migrations
- Collects static files
- Creates notification templates
- Creates superuser (if env vars set)
- Seeds demo data (if enabled)

#### Step 4: Verify Deployment

```bash
# Check health endpoint
curl http://localhost:8001/api/health/

# View logs
docker compose -f docker-compose.prod.yml logs -f web
```

### Docker Compose Configuration

**docker-compose.yml** (Development):

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: aureon-db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=${DB_NAME:-finance_saas}
      - POSTGRES_USER=${DB_USER:-finance_user}
      - POSTGRES_PASSWORD=${DB_PASSWORD:-change_me_in_production}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-finance_user}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - aureon-network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: aureon-redis
    command: redis-server --appendonly yes --maxmemory 256mb
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - aureon-network
    restart: unless-stopped

  web:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: aureon-web
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 --threads 2 --timeout 120
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
      - logs_volume:/app/logs
    ports:
      - "8001:8000"
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - aureon-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health/"]
      interval: 30s
      timeout: 10s
      retries: 3

  celery_worker:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: aureon-celery-worker
    command: celery -A config worker -l info --concurrency=4
    volumes:
      - media_volume:/app/media
      - logs_volume:/app/logs
    env_file:
      - .env
    depends_on:
      - db
      - redis
    networks:
      - aureon-network
    restart: unless-stopped

  celery_beat:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: aureon-celery-beat
    command: celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    volumes:
      - logs_volume:/app/logs
    env_file:
      - .env
    depends_on:
      - db
      - redis
    networks:
      - aureon-network
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  static_volume:
  media_volume:
  logs_volume:

networks:
  aureon-network:
    driver: bridge
```

---

## Manual Deployment

For environments where Docker is not available.

### Step 1: Create Application User

```bash
# Create dedicated user
sudo useradd -m -s /bin/bash aureon
sudo usermod -aG sudo aureon

# Switch to aureon user
sudo su - aureon
```

### Step 2: Clone and Setup

```bash
# Clone repository
cd /home/aureon
git clone https://github.com/rhematek-solutions/aureon.git aureon-platform
cd aureon-platform

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### Step 3: Configure Environment

```bash
# Create environment file
cp .env.example .env
nano .env

# Create logs directory
mkdir -p logs
```

### Step 4: Database Setup

```bash
# Configure PostgreSQL
sudo -u postgres psql

-- Create database and user
CREATE DATABASE finance_saas_prod;
CREATE USER finance_user WITH PASSWORD 'your-secure-password';
GRANT ALL PRIVILEGES ON DATABASE finance_saas_prod TO finance_user;
ALTER DATABASE finance_saas_prod OWNER TO finance_user;
\c finance_saas_prod
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
\q
```

### Step 5: Initialize Application

```bash
# Activate virtual environment
source .venv/bin/activate

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Seed notification templates
python manage.py create_notification_templates

# Collect static files
python manage.py collectstatic --noinput
```

### Step 6: Create Systemd Services

**Gunicorn Service** (`/etc/systemd/system/aureon-gunicorn.service`):

```ini
[Unit]
Description=Aureon Gunicorn Daemon
After=network.target postgresql.service redis.service

[Service]
User=aureon
Group=aureon
WorkingDirectory=/home/aureon/aureon-platform
Environment="PATH=/home/aureon/aureon-platform/.venv/bin"
EnvironmentFile=/home/aureon/aureon-platform/.env
ExecStart=/home/aureon/aureon-platform/.venv/bin/gunicorn \
    --bind 127.0.0.1:8000 \
    --workers 4 \
    --threads 2 \
    --timeout 120 \
    --access-logfile /home/aureon/logs/gunicorn-access.log \
    --error-logfile /home/aureon/logs/gunicorn-error.log \
    config.wsgi:application
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Celery Worker Service** (`/etc/systemd/system/aureon-celery.service`):

```ini
[Unit]
Description=Aureon Celery Worker
After=network.target redis.service postgresql.service

[Service]
User=aureon
Group=aureon
WorkingDirectory=/home/aureon/aureon-platform
Environment="PATH=/home/aureon/aureon-platform/.venv/bin"
EnvironmentFile=/home/aureon/aureon-platform/.env
ExecStart=/home/aureon/aureon-platform/.venv/bin/celery -A config worker \
    --loglevel=info \
    --logfile=/home/aureon/logs/celery-worker.log \
    --concurrency=4 \
    --max-tasks-per-child=1000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Celery Beat Service** (`/etc/systemd/system/aureon-celery-beat.service`):

```ini
[Unit]
Description=Aureon Celery Beat Scheduler
After=network.target redis.service postgresql.service

[Service]
User=aureon
Group=aureon
WorkingDirectory=/home/aureon/aureon-platform
Environment="PATH=/home/aureon/aureon-platform/.venv/bin"
EnvironmentFile=/home/aureon/aureon-platform/.env
ExecStart=/home/aureon/aureon-platform/.venv/bin/celery -A config beat \
    --loglevel=info \
    --logfile=/home/aureon/logs/celery-beat.log \
    --pidfile=/home/aureon/logs/celery-beat.pid
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Step 7: Enable and Start Services

```bash
sudo systemctl daemon-reload
sudo systemctl enable aureon-gunicorn aureon-celery aureon-celery-beat
sudo systemctl start aureon-gunicorn aureon-celery aureon-celery-beat

# Verify status
sudo systemctl status aureon-gunicorn
sudo systemctl status aureon-celery
sudo systemctl status aureon-celery-beat
```

---

## Nginx Configuration

### Production Nginx Config

Create `/etc/nginx/sites-available/aureon`:

```nginx
# Upstream configuration
upstream aureon_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name aureon.yourdomain.com www.aureon.yourdomain.com;

    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Redirect all other requests to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS Server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name aureon.yourdomain.com www.aureon.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/aureon.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aureon.yourdomain.com/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;

    # Modern TLS configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Client configuration
    client_max_body_size 50M;
    client_body_buffer_size 10M;

    # Logging
    access_log /var/log/nginx/aureon-access.log;
    error_log /var/log/nginx/aureon-error.log;

    # Static files
    location /static/ {
        alias /home/aureon/aureon-platform/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Media files
    location /media/ {
        alias /home/aureon/aureon-platform/media/;
        expires 30d;
        add_header Cache-Control "public";
    }

    # Health check endpoint (no caching)
    location /api/health/ {
        proxy_pass http://aureon_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        add_header Cache-Control "no-store, no-cache, must-revalidate";
    }

    # Proxy to Django application
    location / {
        proxy_pass http://aureon_backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";
        proxy_redirect off;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # Buffering
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }

    # WebSocket support (if needed)
    location /ws/ {
        proxy_pass http://aureon_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Enable Site

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/aureon /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

---

## SSL/TLS Setup

### Let's Encrypt with Certbot

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain certificate
sudo certbot --nginx -d aureon.yourdomain.com -d www.aureon.yourdomain.com

# Verify auto-renewal
sudo certbot renew --dry-run
```

### Certificate Renewal Cron

```bash
# Add to crontab
sudo crontab -e

# Add this line (runs twice daily)
0 0,12 * * * /usr/bin/certbot renew --quiet --post-hook "systemctl reload nginx"
```

### SSL Test

Verify your SSL configuration at: https://www.ssllabs.com/ssltest/

Expected grade: **A+**

---

## Database Configuration

### PostgreSQL Optimization

Edit `/etc/postgresql/15/main/postgresql.conf`:

```ini
# Connection Settings
max_connections = 100
superuser_reserved_connections = 3

# Memory Settings
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 128MB
work_mem = 4MB

# Checkpoint Settings
checkpoint_completion_target = 0.9
wal_buffers = 16MB
min_wal_size = 1GB
max_wal_size = 4GB

# Query Planning
random_page_cost = 1.1
effective_io_concurrency = 200
default_statistics_target = 100

# Logging
log_destination = 'stderr'
logging_collector = on
log_directory = 'pg_log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_rotation_age = 1d
log_rotation_size = 100MB
log_min_duration_statement = 1000
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on
```

### Restart PostgreSQL

```bash
sudo systemctl restart postgresql
```

---

## Redis Configuration

### Redis Optimization

Edit `/etc/redis/redis.conf`:

```ini
# Memory
maxmemory 256mb
maxmemory-policy allkeys-lru

# Persistence
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec

# Security
requirepass your-redis-password

# Connections
maxclients 10000
timeout 300

# Logging
loglevel notice
logfile /var/log/redis/redis-server.log
```

### Restart Redis

```bash
sudo systemctl restart redis-server
```

---

## Celery Workers

### Scaling Celery Workers

For high-traffic environments, scale Celery workers:

```bash
# Multiple worker instances
celery -A config worker -l info --concurrency=4 -Q default -n worker1@%h
celery -A config worker -l info --concurrency=4 -Q email -n worker2@%h
celery -A config worker -l info --concurrency=2 -Q analytics -n worker3@%h
```

### Flower Monitoring

```bash
# Install Flower
pip install flower

# Run Flower
celery -A config flower --port=5555

# Access at: http://localhost:5555
```

---

## Monitoring Setup

### Prometheus Configuration

Install Prometheus:

```bash
# Download Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xvfz prometheus-*.tar.gz
sudo mv prometheus-*/ /opt/prometheus
```

Create `/opt/prometheus/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'aureon'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'

  - job_name: 'nginx'
    static_configs:
      - targets: ['localhost:9113']

  - job_name: 'postgresql'
    static_configs:
      - targets: ['localhost:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']
```

### Sentry Error Tracking

```bash
# Set SENTRY_DSN in .env
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
```

Django automatically sends errors to Sentry when configured.

### Health Check Endpoints

| Endpoint | Purpose | Expected Response |
|----------|---------|-------------------|
| `/api/health/` | Application health | `{"status": "healthy"}` |
| `/api/health/db/` | Database connectivity | `{"status": "connected"}` |
| `/api/health/redis/` | Redis connectivity | `{"status": "connected"}` |

---

## Backup Procedures

### Automated Database Backup

Create `/home/aureon/scripts/backup-database.sh`:

```bash
#!/bin/bash

# Configuration
BACKUP_DIR="/home/aureon/backups/database"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/finance_saas_$DATE.sql.gz"
RETENTION_DAYS=30

# Create backup directory
mkdir -p $BACKUP_DIR

# Create backup
PGPASSWORD="your-db-password" pg_dump -h localhost -U finance_user finance_saas_prod | gzip > $BACKUP_FILE

# Verify backup
if [ -f "$BACKUP_FILE" ] && [ -s "$BACKUP_FILE" ]; then
    echo "$(date): Backup successful - $BACKUP_FILE" >> /home/aureon/logs/backup.log
else
    echo "$(date): Backup FAILED" >> /home/aureon/logs/backup.log
    exit 1
fi

# Delete old backups
find $BACKUP_DIR -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $BACKUP_FILE"
```

### Media Files Backup

Create `/home/aureon/scripts/backup-media.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/home/aureon/backups/media"
DATE=$(date +%Y%m%d)
BACKUP_FILE="$BACKUP_DIR/media_$DATE.tar.gz"

mkdir -p $BACKUP_DIR

tar -czf $BACKUP_FILE -C /home/aureon/aureon-platform media/

# Keep 7 days of media backups
find $BACKUP_DIR -name "media_*.tar.gz" -mtime +7 -delete

echo "Media backup completed: $BACKUP_FILE"
```

### Cron Schedule

```bash
# Edit crontab
crontab -e

# Add these lines
# Database backup at 2 AM daily
0 2 * * * /home/aureon/scripts/backup-database.sh >> /home/aureon/logs/backup.log 2>&1

# Media backup at 3 AM weekly (Sunday)
0 3 * * 0 /home/aureon/scripts/backup-media.sh >> /home/aureon/logs/backup.log 2>&1
```

### Offsite Backup (AWS S3)

```bash
# Install AWS CLI
pip install awscli

# Configure AWS
aws configure

# Sync to S3
aws s3 sync /home/aureon/backups s3://your-backup-bucket/aureon/ --storage-class STANDARD_IA
```

### Backup Restoration

```bash
# Restore database
gunzip < /home/aureon/backups/database/finance_saas_20251229.sql.gz | psql -U finance_user finance_saas_prod

# Restore media files
tar -xzf /home/aureon/backups/media/media_20251229.tar.gz -C /home/aureon/aureon-platform/
```

---

## Troubleshooting

### Common Issues

#### Application Not Starting

```bash
# Check Gunicorn logs
sudo journalctl -u aureon-gunicorn -n 100
tail -f /home/aureon/logs/gunicorn-error.log

# Check for syntax errors
cd /home/aureon/aureon-platform
source .venv/bin/activate
python manage.py check

# Verify database connection
python manage.py dbshell
```

#### 502 Bad Gateway

```bash
# Check if Gunicorn is running
sudo systemctl status aureon-gunicorn

# Check Gunicorn socket
ss -tlnp | grep 8000

# Restart services
sudo systemctl restart aureon-gunicorn nginx
```

#### Celery Tasks Not Running

```bash
# Check Redis
redis-cli ping

# Check Celery worker
sudo systemctl status aureon-celery
tail -f /home/aureon/logs/celery-worker.log

# Test Celery connection
celery -A config inspect ping
```

#### Database Connection Issues

```bash
# Test PostgreSQL connection
psql -h localhost -U finance_user -d finance_saas_prod

# Check PostgreSQL status
sudo systemctl status postgresql

# View PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-15-main.log
```

#### Static Files Not Loading

```bash
# Recollect static files
python manage.py collectstatic --noinput

# Check Nginx static configuration
ls -la /home/aureon/aureon-platform/staticfiles/

# Verify permissions
sudo chown -R aureon:www-data /home/aureon/aureon-platform/staticfiles/
```

---

## Deployment Checklist

### Dockploy Quick Checklist

- [ ] Configure environment variables in Dockploy UI
- [ ] Run `docker compose -f docker-compose.prod.yml up -d`
- [ ] Verify health endpoint returns 200
- [ ] Access admin panel at `/admin/`

### Pre-Deployment (Manual)

- [ ] Server meets minimum requirements (4 CPU, 8GB RAM)
- [ ] Domain DNS configured to server IP
- [ ] Stripe production keys ready
- [ ] Environment variables prepared

### Post-Deployment Verification

- [ ] Health endpoint: `curl https://yourdomain.com/api/health/`
- [ ] Admin panel works at `/admin/`
- [ ] API docs accessible at `/api/docs/`
- [ ] Stripe webhook configured in Stripe Dashboard
- [ ] Celery tasks running: `docker compose logs celery-high`

### Security Verification

- [ ] `DEBUG=False` in environment
- [ ] `SECRET_KEY` is 50+ characters
- [ ] HTTPS enabled with valid certificate
- [ ] Security headers present (check with `curl -I`)
- [ ] Rate limiting active

---

## Support

For deployment assistance:

- **Email**: support@rhematek-solutions.com
- **Documentation**: https://docs.aureon.rhematek-solutions.com
- **Issues**: https://github.com/rhematek-solutions/aureon/issues

---

**Aureon** - Automated Financial Management Platform
Copyright 2025 Rhematek Solutions
*From Signature to Cash, Everything Runs Automatically.*
