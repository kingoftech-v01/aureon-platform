# Production Deployment Guide - Aureon SaaS Platform

Version: 2.0.0-FINAL
Last Updated: 2025-12-27

This guide provides comprehensive instructions for deploying the Aureon Finance Management SaaS platform to a production environment.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Server Requirements](#server-requirements)
3. [System Setup](#system-setup)
4. [Database Configuration](#database-configuration)
5. [Application Deployment](#application-deployment)
6. [Web Server Configuration](#web-server-configuration)
7. [Background Workers](#background-workers)
8. [Post-Deployment Tasks](#post-deployment-tasks)
9. [Monitoring & Maintenance](#monitoring--maintenance)
10. [Security Hardening](#security-hardening)
11. [Backup Strategy](#backup-strategy)
12. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Knowledge
- Linux server administration
- PostgreSQL database management
- Nginx web server configuration
- SSL/TLS certificate management
- Python virtual environments
- Git version control

### Required Accounts
- Server with SSH access (Ubuntu 20.04 LTS or 22.04 LTS recommended)
- Domain name with DNS management
- Stripe account (production API keys)
- Email service (AWS SES, SendGrid, or SMTP)
- SSL certificate (Let's Encrypt recommended)

---

## Server Requirements

### Minimum Specifications
- **CPU**: 2 cores
- **RAM**: 4 GB
- **Storage**: 50 GB SSD
- **OS**: Ubuntu 22.04 LTS
- **Network**: Static IP address

### Recommended Specifications (Production)
- **CPU**: 4 cores
- **RAM**: 8 GB
- **Storage**: 100 GB SSD (with backup storage)
- **OS**: Ubuntu 22.04 LTS
- **Network**: Static IP, firewall configured

### Software Stack
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Nginx 1.18+
- Node.js 18+ (for frontend build)
- Supervisor or systemd (for process management)

---

## System Setup

### 1. Update System

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential python3.11 python3.11-dev python3.11-venv \
    postgresql-15 postgresql-server-dev-15 redis-server nginx git curl \
    supervisor libpq-dev libjpeg-dev libpng-dev libmagic1
```

### 2. Create Application User

```bash
sudo useradd -m -s /bin/bash aureon
sudo usermod -aG sudo aureon
sudo su - aureon
```

### 3. Clone Repository

```bash
cd /home/aureon
git clone <repository-url> aureon-platform
cd aureon-platform
```

### 4. Create Virtual Environment

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

---

## Database Configuration

### 1. Configure PostgreSQL

```bash
sudo -u postgres psql
```

```sql
-- Create database and user
CREATE DATABASE finance_saas_prod;
CREATE USER finance_user WITH PASSWORD 'STRONG_PASSWORD_HERE';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE finance_saas_prod TO finance_user;
ALTER DATABASE finance_saas_prod OWNER TO finance_user;

-- Enable required extensions
\c finance_saas_prod
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

\q
```

### 2. Configure PostgreSQL for Production

Edit `/etc/postgresql/15/main/postgresql.conf`:

```ini
# Performance tuning
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 128MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB

# Connection settings
max_connections = 100
```

Restart PostgreSQL:

```bash
sudo systemctl restart postgresql
```

---

## Application Deployment

### 1. Environment Configuration

Create `.env` file:

```bash
cp .env.example .env
nano .env
```

**Production `.env` configuration:**

```ini
# Django Settings
SECRET_KEY=<generate-using-python-c-import-secrets-secrets-token-urlsafe-50>
DEBUG=False
ALLOWED_HOSTS=aureon.rhematek-solutions.com,www.aureon.rhematek-solutions.com

# Database
DATABASE_URL=postgresql://finance_user:STRONG_PASSWORD_HERE@localhost:5432/finance_saas_prod

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Stripe (Production Keys)
STRIPE_PUBLIC_KEY=pk_live_xxxxx
STRIPE_SECRET_KEY=sk_live_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
DJSTRIPE_WEBHOOK_SECRET=whsec_xxxxx

# Email (AWS SES Example)
EMAIL_BACKEND=django_ses.SESBackend
AWS_SES_REGION_NAME=us-east-1
AWS_ACCESS_KEY_ID=<your-aws-key>
AWS_SECRET_ACCESS_KEY=<your-aws-secret>
DEFAULT_FROM_EMAIL=noreply@aureon.rhematek-solutions.com

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SECURE_CONTENT_TYPE_NOSNIFF=True
SECURE_BROWSER_XSS_FILTER=True
X_FRAME_OPTIONS=DENY

# Monitoring
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
```

### 2. Run Database Migrations

```bash
source .venv/bin/activate
python manage.py migrate
```

### 3. Create Superuser

```bash
python manage.py createsuperuser
```

### 4. Seed Notification Templates

```bash
python manage.py create_notification_templates
```

### 5. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 6. Build Frontend (if applicable)

```bash
cd frontend
npm install
npm run build
cd ..
```

---

## Web Server Configuration

### 1. Configure Gunicorn

Create `/home/aureon/aureon-platform/gunicorn_config.py`:

```python
import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
errorlog = "/home/aureon/logs/gunicorn-error.log"
accesslog = "/home/aureon/logs/gunicorn-access.log"
loglevel = "info"
```

Create log directory:

```bash
mkdir -p /home/aureon/logs
```

### 2. Create Systemd Service for Gunicorn

Create `/etc/systemd/system/aureon-gunicorn.service`:

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
    --config /home/aureon/aureon-platform/gunicorn_config.py \
    config.wsgi:application
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable aureon-gunicorn
sudo systemctl start aureon-gunicorn
sudo systemctl status aureon-gunicorn
```

### 3. Configure Nginx

Create `/etc/nginx/sites-available/aureon`:

```nginx
upstream aureon_backend {
    server 127.0.0.1:8000;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name aureon.rhematek-solutions.com www.aureon.rhematek-solutions.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS Server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name aureon.rhematek-solutions.com www.aureon.rhematek-solutions.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/aureon.rhematek-solutions.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aureon.rhematek-solutions.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Client body size (for file uploads)
    client_max_body_size 50M;

    # Logging
    access_log /var/log/nginx/aureon-access.log;
    error_log /var/log/nginx/aureon-error.log;

    # Static files
    location /static/ {
        alias /home/aureon/aureon-platform/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /home/aureon/aureon-platform/media/;
        expires 30d;
        add_header Cache-Control "public";
    }

    # Proxy to Gunicorn
    location / {
        proxy_pass http://aureon_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

Enable site and restart Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/aureon /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 4. SSL Certificate (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d aureon.rhematek-solutions.com -d www.aureon.rhematek-solutions.com
```

---

## Background Workers

### 1. Configure Celery Worker

Create `/etc/systemd/system/aureon-celery.service`:

```ini
[Unit]
Description=Aureon Celery Worker
After=network.target redis.service postgresql.service

[Service]
Type=forking
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

### 2. Configure Celery Beat (Scheduler)

Create `/etc/systemd/system/aureon-celery-beat.service`:

```ini
[Unit]
Description=Aureon Celery Beat Scheduler
After=network.target redis.service postgresql.service

[Service]
Type=simple
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

### 3. Start Services

```bash
sudo systemctl daemon-reload
sudo systemctl enable aureon-celery aureon-celery-beat
sudo systemctl start aureon-celery aureon-celery-beat
sudo systemctl status aureon-celery aureon-celery-beat
```

---

## Post-Deployment Tasks

### 1. Verify Services

```bash
# Check all services
sudo systemctl status aureon-gunicorn aureon-celery aureon-celery-beat postgresql redis nginx

# Check logs
tail -f /home/aureon/logs/gunicorn-error.log
tail -f /home/aureon/logs/celery-worker.log
tail -f /var/log/nginx/aureon-error.log
```

### 2. Test Stripe Webhooks

```bash
# Use Stripe CLI to forward webhooks
stripe listen --forward-to https://aureon.rhematek-solutions.com/webhooks/stripe/

# Test webhook
stripe trigger payment_intent.succeeded
```

### 3. Verify Email Sending

```bash
python manage.py shell
```

```python
from django.core.mail import send_mail
send_mail(
    'Test Email',
    'This is a test from Aureon Platform.',
    'noreply@aureon.rhematek-solutions.com',
    ['admin@example.com'],
    fail_silently=False,
)
```

### 4. Run Analytics Recalculation

```bash
python manage.py shell
```

```python
from apps.analytics.services import RevenueMetricsCalculator, ClientMetricsCalculator
from datetime import datetime

# Calculate current month metrics
year = datetime.now().year
month = datetime.now().month
RevenueMetricsCalculator.calculate_month_metrics(year, month)

# Calculate all client metrics
from apps.clients.models import Client
for client in Client.objects.all():
    ClientMetricsCalculator.calculate_client_metrics(client)
```

---

## Monitoring & Maintenance

### 1. Setup Sentry for Error Tracking

Already configured via `SENTRY_DSN` in `.env`. Verify at https://sentry.io

### 2. Setup Prometheus Metrics (Optional)

Add to `config/urls.py`:

```python
urlpatterns += [
    path('', include('django_prometheus.urls')),
]
```

### 3. Database Backup Script

Create `/home/aureon/scripts/backup-database.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/home/aureon/backups/database"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/finance_saas_prod_$DATE.sql.gz"

mkdir -p $BACKUP_DIR

# Create backup
pg_dump -U finance_user finance_saas_prod | gzip > $BACKUP_FILE

# Keep only last 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE"
```

Make executable and add to cron:

```bash
chmod +x /home/aureon/scripts/backup-database.sh
crontab -e
```

Add:

```cron
# Daily database backup at 2 AM
0 2 * * * /home/aureon/scripts/backup-database.sh >> /home/aureon/logs/backup.log 2>&1
```

### 4. Log Rotation

Create `/etc/logrotate.d/aureon`:

```
/home/aureon/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0640 aureon aureon
    sharedscripts
    postrotate
        systemctl reload aureon-gunicorn
    endscript
}
```

---

## Security Hardening

### 1. Firewall Configuration

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

### 2. Fail2Ban for Brute Force Protection

```bash
sudo apt install fail2ban
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo nano /etc/fail2ban/jail.local
```

Add:

```ini
[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/*error.log

[nginx-limit-req]
enabled = true
port = http,https
logpath = /var/log/nginx/*error.log
```

Restart:

```bash
sudo systemctl restart fail2ban
```

### 3. Security Checklist

- [ ] Change default PostgreSQL password
- [ ] Restrict PostgreSQL to localhost only
- [ ] Enable UFW firewall
- [ ] Install Fail2Ban
- [ ] Configure SSL/TLS with strong ciphers
- [ ] Enable HSTS headers
- [ ] Set strong Django SECRET_KEY (50+ characters)
- [ ] Disable DEBUG mode (`DEBUG=False`)
- [ ] Set proper ALLOWED_HOSTS
- [ ] Use environment variables for secrets
- [ ] Enable Stripe webhook signature verification
- [ ] Configure CORS properly
- [ ] Regular security updates (`apt update && apt upgrade`)
- [ ] Monitor logs for suspicious activity

---

## Backup Strategy

### Daily Backups
- Database (automated via cron)
- Media files (`/home/aureon/aureon-platform/media`)
- Environment configuration (`/home/aureon/aureon-platform/.env`)

### Weekly Backups
- Full application code
- Nginx configuration
- Systemd service files
- SSL certificates

### Offsite Backup
Store backups on AWS S3 or similar:

```bash
# Install AWS CLI
sudo apt install awscli
aws configure

# Sync backups
aws s3 sync /home/aureon/backups s3://aureon-backups/$(date +%Y%m%d)/
```

---

## Troubleshooting

### Application Won't Start

```bash
# Check logs
sudo journalctl -u aureon-gunicorn -n 100
tail -f /home/aureon/logs/gunicorn-error.log

# Verify database connection
python manage.py dbshell

# Check migrations
python manage.py showmigrations
```

### Celery Tasks Not Running

```bash
# Check Redis
redis-cli ping

# Check Celery worker
sudo systemctl status aureon-celery
tail -f /home/aureon/logs/celery-worker.log

# Monitor tasks
python manage.py shell
from celery import current_app
current_app.control.inspect().active()
```

### Nginx 502 Bad Gateway

```bash
# Check Gunicorn is running
sudo systemctl status aureon-gunicorn

# Check Gunicorn bind address
ss -tlnp | grep 8000

# Verify Nginx config
sudo nginx -t
```

### Database Performance Issues

```sql
-- Check active connections
SELECT count(*) FROM pg_stat_activity;

-- Check slow queries
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active'
ORDER BY duration DESC;

-- Vacuum and analyze
VACUUM ANALYZE;
```

---

## Deployment Checklist

Before going live:

- [ ] All migrations applied
- [ ] Superuser created
- [ ] Notification templates seeded
- [ ] Static files collected
- [ ] Gunicorn service running
- [ ] Celery worker running
- [ ] Celery beat running
- [ ] Nginx configured and running
- [ ] SSL certificate installed
- [ ] Firewall configured
- [ ] Database backups configured
- [ ] Monitoring setup (Sentry)
- [ ] Email sending tested
- [ ] Stripe webhooks tested
- [ ] DNS configured correctly
- [ ] All services start on boot
- [ ] Log rotation configured

---

## Support & Maintenance

### Regular Tasks

**Daily:**
- Monitor error logs
- Check Sentry for exceptions
- Verify backups completed

**Weekly:**
- Review performance metrics
- Check disk space usage
- Review security logs

**Monthly:**
- Apply security updates
- Review and optimize database
- Test backup restoration
- Review and update dependencies

### Emergency Contacts

- Platform Admin: admin@rhematek-solutions.com
- Sentry: https://sentry.io/aureon-platform
- Stripe Dashboard: https://dashboard.stripe.com

---

## Conclusion

This deployment guide covers the complete production setup for the Aureon SaaS Platform. For questions or issues, refer to the troubleshooting section or contact support.

**Version**: 2.0.0-FINAL
**Last Updated**: 2025-12-27
**Documentation**: See README.md for full platform documentation
