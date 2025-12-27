# Aureon SaaS Platform - Quick Start Guide

## Setup Instructions

### Prerequisites
- Python 3.10 or higher
- PostgreSQL 14 or higher
- Redis 7 or higher
- Git

### 1. Clone and Setup Virtual Environment

```bash
cd "Finance Management"
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Django
SECRET_KEY=django-insecure-CHANGE-THIS-IN-PRODUCTION
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,*.localhost

# Database
DB_NAME=aureon_db
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1

# Stripe (Test Mode)
STRIPE_PUBLIC_KEY=pk_test_your_key_here
STRIPE_SECRET_KEY=sk_test_your_key_here
DJSTRIPE_WEBHOOK_SECRET=whsec_your_secret_here

# Email (Console Backend for Development)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=noreply@aureon.local

# Site
SITE_URL=http://localhost:8000
```

### 4. Create PostgreSQL Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE aureon_db;

# Grant permissions
GRANT ALL PRIVILEGES ON DATABASE aureon_db TO postgres;

# Exit
\q
```

### 5. Run Migrations

```bash
# Use the custom settings file
export DJANGO_SETTINGS_MODULE=config.settings_aureon  # Linux/Mac
set DJANGO_SETTINGS_MODULE=config.settings_aureon  # Windows

# Create migrations for shared apps (public schema)
python manage.py makemigrations tenants
python manage.py makemigrations accounts

# Migrate public schema
python manage.py migrate_schemas --shared

# Create migrations for tenant apps
python manage.py makemigrations clients
# python manage.py makemigrations contracts  # TODO: Implement
# python manage.py makemigrations invoicing  # TODO: Implement
# python manage.py makemigrations payments   # TODO: Implement

# Migrate all tenant schemas
python manage.py migrate_schemas
```

### 6. Create Superuser

```bash
python manage.py createsuperuser
# Enter email: admin@aureon.local
# Enter password: (your secure password)
```

### 7. Create a Test Tenant

```bash
python manage.py shell
```

```python
from apps.tenants.models import Tenant, Domain
from datetime import timedelta
from django.utils import timezone

# Create tenant
tenant = Tenant.objects.create(
    name="Demo Agency",
    slug="demo-agency",
    schema_name="demo_agency",
    tenant_type=Tenant.AGENCY,
    contact_email="demo@example.com",
    plan=Tenant.FREE,
    is_trial=True,
    trial_ends_at=timezone.now() + timedelta(days=14)
)

# Create domain
Domain.objects.create(
    tenant=tenant,
    domain="demo-agency.localhost",  # For local development
    is_primary=True,
)

print(f"Tenant created: {tenant.name}")
print(f"Domain: demo-agency.localhost")
exit()
```

### 8. Create a Test User for the Tenant

```bash
python manage.py shell
```

```python
from apps.accounts.models import User
from apps.tenants.models import Tenant

# Get the tenant
tenant = Tenant.objects.get(slug="demo-agency")

# Create admin user for this tenant
user = User.objects.create_user(
    email="admin@demo-agency.com",
    password="SecurePass123!",
    first_name="John",
    last_name="Doe",
    tenant=tenant,
    role=User.ADMIN,
    is_active=True,
    is_verified=True
)

print(f"User created: {user.email}")
print(f"Tenant: {tenant.name}")
exit()
```

### 9. Start Development Server

```bash
python manage.py runserver
```

Access at:
- Admin (Public): http://localhost:8000/admin/
- API Docs: http://localhost:8000/api/docs/
- Tenant Admin: http://demo-agency.localhost:8000/admin/ (requires hosts file)

### 10. Configure Local Hosts (Optional)

For proper subdomain testing, add to your hosts file:

**Windows**: `C:\Windows\System32\drivers\etc\hosts`
**Linux/Mac**: `/etc/hosts`

```
127.0.0.1   localhost
127.0.0.1   demo-agency.localhost
127.0.0.1   test-tenant.localhost
```

### 11. Start Celery (Separate Terminal)

```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows

# Start Celery worker
celery -A config worker -l info

# In another terminal, start Celery beat
celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

---

## Testing the API

### 1. Get JWT Token

```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@demo-agency.com",
    "password": "SecurePass123!"
  }'
```

Response:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### 2. Use Token for Authenticated Requests

```bash
curl -X GET http://demo-agency.localhost:8000/api/users/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 3. Create a Client

```bash
curl -X POST http://demo-agency.localhost:8000/api/clients/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "client_type": "company",
    "company_name": "Acme Corporation",
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane@acme.com",
    "phone": "+1234567890",
    "lifecycle_stage": "prospect"
  }'
```

---

## Project Structure

```
Finance Management/
├── apps/
│   ├── tenants/          ✅ Complete (models, admin, serializers, views, URLs)
│   ├── accounts/         ✅ Complete (models, admin, serializers, views, URLs)
│   ├── clients/          ✅ Models + Admin (pending: serializers, views)
│   ├── contracts/        ⏳ Pending
│   ├── invoicing/        ⏳ Pending
│   ├── payments/         ⏳ Pending
│   ├── notifications/    ⏳ Pending
│   ├── analytics/        ⏳ Pending
│   ├── documents/        ⏳ Pending
│   ├── webhooks/         ⏳ Pending
│   ├── integrations/     ⏳ Pending
│   └── website/          ✅ Existing (marketing site)
│
├── config/
│   ├── __init__.py
│   ├── settings_aureon.py      ✅ Complete
│   ├── urls_tenants.py          ✅ Complete
│   ├── urls_public.py           ✅ Complete
│   ├── celery.py                ✅ Complete
│   └── wsgi.py                  ✅ Complete
│
├── requirements.txt             ✅ Complete
├── manage.py                    ✅ Complete
├── .env.example                 ✅ Complete
│
├── CLAUDE.md                    ✅ Project instructions
├── Project Plan.md              ✅ Business plan
├── IMPLEMENTATION_STATUS.md     ✅ Status tracking
├── COMPLETE_MODELS_BLUEPRINT.md ✅ All model definitions
├── BACKEND_IMPLEMENTATION_REPORT.md ✅ Comprehensive report
└── QUICKSTART.md               ✅ This file
```

---

## Common Commands

### Django Management

```bash
# Create migrations
python manage.py makemigrations

# Run migrations (shared schema)
python manage.py migrate_schemas --shared

# Run migrations (all tenant schemas)
python manage.py migrate_schemas

# Create superuser
python manage.py createsuperuser

# Django shell
python manage.py shell

# Django shell with tenant context
python manage.py tenant_command shell --schema=demo_agency
```

### Database

```bash
# Access PostgreSQL
psql -U postgres -d aureon_db

# List schemas
\dn

# List tables in public schema
\dt

# List tables in tenant schema
SET search_path TO demo_agency;
\dt

# Reset database (DANGER!)
DROP DATABASE aureon_db;
CREATE DATABASE aureon_db;
```

### Celery

```bash
# Start worker
celery -A config worker -l info

# Start beat scheduler
celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler

# Purge all tasks
celery -A config purge

# Flower (web-based monitoring)
celery -A config flower
# Access at http://localhost:5555
```

### Code Quality

```bash
# Run tests
pytest

# Check test coverage
pytest --cov=apps

# Lint code
flake8 apps/

# Format code (if using black)
black apps/
```

---

## Troubleshooting

### Issue: Cannot connect to PostgreSQL

**Solution**: Verify PostgreSQL is running
```bash
# Windows
sc query postgresql

# Linux/Mac
sudo systemctl status postgresql
```

### Issue: Redis connection failed

**Solution**: Start Redis server
```bash
# Windows (using WSL or Redis for Windows)
redis-server

# Linux
sudo systemctl start redis

# Mac
brew services start redis
```

### Issue: Migrations fail

**Solution**: Check database connection and run migrations in order
```bash
python manage.py migrate_schemas --shared  # Public schema first
python manage.py migrate_schemas           # Then tenant schemas
```

### Issue: Cannot access tenant subdomain

**Solution**:
1. Add to hosts file (see step 10)
2. Ensure domain is created in database
3. Use `localhost:8000` with `X-Tenant` header for testing

### Issue: Static files not loading

**Solution**: Collect static files
```bash
python manage.py collectstatic --noinput
```

---

## Next Steps

1. ✅ Complete setup
2. ⏳ Implement remaining models (contracts, invoicing, payments)
3. ⏳ Create serializers and views for clients app
4. ⏳ Integrate Stripe payment processing
5. ⏳ Build frontend dashboard
6. ⏳ Write comprehensive tests
7. ⏳ Deploy to staging environment

---

## Documentation

- **API Documentation**: http://localhost:8000/api/docs/
- **Admin Panel**: http://localhost:8000/admin/
- **Full Implementation Report**: See `BACKEND_IMPLEMENTATION_REPORT.md`
- **Model Blueprints**: See `COMPLETE_MODELS_BLUEPRINT.md`

---

## Support

For questions or issues:
- **Email**: stephane@rhematek-solutions.com
- **Company**: Rhematek Solutions
- **Platform**: Aureon by Rhematek Solutions

---

**Last Updated**: December 27, 2025
**Version**: 1.0
