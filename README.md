# Aureon by Rhematek Solutions

**From Signature to Cash, Everything Runs Automatically.**

Aureon is a comprehensive SaaS platform that automates end-to-end client financial workflows: lead-to-contract, contract generation and e-signature, auto-invoicing, payment collection via Stripe, receipt delivery, and real-time dashboards.

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE.md)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/django-5.1.4-green.svg)](https://www.djangoproject.com/)
[![React](https://img.shields.io/badge/react-18.3.1-blue.svg)](https://reactjs.org/)
[![PostgreSQL](https://img.shields.io/badge/postgresql-16-blue.svg)](https://www.postgresql.org/)

---

## One-Command Deployment (Dockploy)

Deploy Aureon with a single command. Everything is automatic.

```bash
docker compose -f docker-compose.prod.yml up -d
```

**That's it!** The container automatically handles:
- Database migrations
- Static file collection
- Notification templates creation
- Superuser creation (if `DJANGO_SUPERUSER_EMAIL` and `DJANGO_SUPERUSER_PASSWORD` are set)
- Demo data seeding (if `SEED_DEMO_DATA=true`)

For Dockploy, simply add this as your start command and configure environment variables in the UI.

---

## Table of Contents

- [One-Command Deployment](#one-command-deployment-dockploy)
- [Overview](#overview)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Quick Start](#quick-start)
- [Production Deployment](#production-deployment)
- [Environment Variables](#environment-variables)
- [Architecture](#architecture)
- [API Documentation](#api-documentation)
- [Contributing](#contributing)
- [License](#license)
- [Support](#support)

---

## Overview

### Mission

Eliminate the complexity of financial administration for modern businesses. Empower agencies, freelancers, and startups to automate their contracts, billing, and payments through an intelligent, secure, and transparent platform.

### Target Markets

- **Digital Agencies**: Managing recurring client contracts and multiple revenue streams
- **Freelancers and Coaches**: Professional solo operators managing multiple clients
- **SaaS Startups**: Subscription-based businesses requiring tight financial integration

### Value Propositions

- **End-to-end automation**: From proposal to payment with minimal manual intervention
- **Faster cash flow**: Automatic invoice creation and Stripe-based collection
- **Transparent client experience**: Branded contracts, e-signatures, and receipting in a single portal
- **Compliance and auditability**: Immutable activity logs, digital signatures, and versioned contracts
- **Scalable pricing and billing**: Time-based, milestone-based, and subscription models

---

## Key Features

### Client Onboarding and CRM
- Contact management with roles, tags, and lifecycle stages
- Lead capture via embeddable forms and integrations
- Customizable client portals with branded UI

### Contracts and E-Signatures
- Contract templates with dynamic fields and placeholders
- Automated proposal-to-contract conversion with version control
- E-signature workflows (eIDAS/ESIGN/UETA compliant)
- Milestone and conditional clauses

### Automated Invoicing
- Invoice generation tied to contract milestones or recurring billing
- Stripe integration for payments, installments, and automated retries
- Proration, credits, refunds, and tax handling (VAT/GST)

### Receipts and Notifications
- Instant receipts sent by email or within the client portal
- Real-time payment status and invoice aging reminders
- Audit logs and exportable reports for accounting

### Payments and Treasury Automation
- Stripe webhooks for status updates and automations
- Multi-currency and multi-region tax configurations
- Reconciliation tools for QuickBooks and Xero

### Document Management
- Central document vault for contracts, receipts, and attachments
- Role-based access control (RBAC) and granular permissions
- Encryption at rest and in transit

### Analytics and Reporting
- Cash flow dashboards and aging reports
- Conversion funnels: lead to proposal to contract to payment
- Revenue recognition reports for GAAP/IFRS compliance

### Security and Compliance
- SOC 2-type controls and secure development lifecycle
- GDPR/CCPA data handling and data subject access requests
- Digital signatures with tamper-evident records
- Two-Factor Authentication (2FA) with TOTP

---

## Technology Stack

### Backend
- **Framework**: Django 5.1.4 with Django REST Framework 3.14
- **Database**: PostgreSQL 16
- **Caching**: Redis 7.4 with django-redis
- **Task Queue**: Celery 5.4.0 with priority queues (high/medium/low/batch)
- **Authentication**: Django Allauth + JWT (SimpleJWT) + 2FA (pyotp)
- **Payments**: Stripe + dj-stripe

### Frontend
- **Framework**: React 18.3.1 with TypeScript
- **UI Library**: Tailwind CSS 3.4.1 + Bootstrap 5
- **State Management**: React Context + React Query
- **Charts**: Chart.js / Recharts
- **Forms**: React Hook Form

### Infrastructure
- **Containerization**: Docker multi-stage builds
- **Web Server**: Nginx with SSL/TLS (Let's Encrypt)
- **Monitoring**: Prometheus + Grafana
- **Error Tracking**: Sentry
- **Deployment**: Dockploy / Docker Compose

### Security (Rhematek Production Shield)
- Argon2 password hashing
- JWT token authentication with refresh tokens
- Two-Factor Authentication (2FA/TOTP)
- Content Security Policy (CSP)
- CORS protection
- Rate limiting (django-ratelimit)
- Brute force protection (django-axes)
- XSS sanitization middleware
- Honeypot protection

---

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Node.js 18+ (for frontend)
- Docker and Docker Compose (optional)

### Local Development Setup

#### Option 1: Using Docker (Recommended)

1. **Clone the repository**
```bash
git clone https://github.com/rhematek-solutions/aureon.git
cd aureon
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Build and run with Docker Compose**
```bash
docker-compose up --build
```

4. **Access the application**
- **Main Site**: http://localhost:8001
- **Admin Panel**: http://localhost:8001/admin
- **API Documentation**: http://localhost:8001/api/docs

#### Option 2: Manual Setup

1. **Clone and create virtual environment**
```bash
git clone https://github.com/rhematek-solutions/aureon.git
cd aureon
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your database and Redis URLs
```

4. **Run database migrations**
```bash
python manage.py migrate
```

5. **Create a superuser**
```bash
python manage.py createsuperuser
```

6. **Seed notification templates**
```bash
python manage.py create_notification_templates
```

7. **Collect static files**
```bash
python manage.py collectstatic --noinput
```

8. **Start the development server**
```bash
python manage.py runserver
```

9. **Start Celery workers (in separate terminals)**
```bash
# Celery worker
celery -A config worker -l info

# Celery beat (scheduler)
celery -A config beat -l info
```

---

## Production Deployment

### Dockploy Deployment (Recommended)

**Single command - everything is automatic:**

```bash
docker compose -f docker-compose.prod.yml up -d
```

Configure these environment variables in Dockploy:

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Django secret key (50+ chars) |
| `DATABASE_URL` | Yes | PostgreSQL connection URL |
| `REDIS_URL` | Yes | Redis connection URL |
| `STRIPE_SECRET_KEY` | Yes | Stripe API secret key |
| `DJANGO_SUPERUSER_EMAIL` | No | Auto-create admin user |
| `DJANGO_SUPERUSER_PASSWORD` | No | Admin user password |
| `SEED_DEMO_DATA` | No | Set to `true` to seed demo data |

The entrypoint script automatically runs:
1. Wait for PostgreSQL and Redis
2. Database migrations
3. Static file collection
4. Notification templates creation
5. Superuser creation (if credentials provided)
6. Demo data seeding (if enabled)

### Manual Docker Deployment

```bash
# Clone repository
git clone https://github.com/rhematek-solutions/aureon.git
cd aureon

# Configure environment
cp .env.example .env
nano .env  # Edit with production values

# Deploy (single command - everything automatic)
docker compose -f docker-compose.prod.yml up -d
```

### SSL/TLS Setup

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d aureon.yourdomain.com
```

For detailed instructions, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md).

---

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key (50+ chars) | `your-secret-key-here` |
| `DEBUG` | Debug mode (False in production) | `False` |
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql://user:pass@localhost:5432/dbname` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |

### Stripe Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `STRIPE_PUBLIC_KEY` | Stripe publishable key | `pk_live_xxx` |
| `STRIPE_SECRET_KEY` | Stripe secret key | `sk_live_xxx` |
| `DJSTRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret | `whsec_xxx` |

### Email Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `EMAIL_BACKEND` | Email backend class | `django.core.mail.backends.smtp.EmailBackend` |
| `EMAIL_HOST` | SMTP host | `smtp.gmail.com` |
| `EMAIL_PORT` | SMTP port | `587` |
| `EMAIL_HOST_USER` | SMTP username | `your-email@gmail.com` |
| `EMAIL_HOST_PASSWORD` | SMTP password | `your-app-password` |
| `DEFAULT_FROM_EMAIL` | Default sender email | `noreply@yourcompany.com` |

### Security Settings (Production)

| Variable | Description | Default |
|----------|-------------|---------|
| `SECURE_SSL_REDIRECT` | Redirect HTTP to HTTPS | `True` |
| `SESSION_COOKIE_SECURE` | Use secure cookies | `True` |
| `CSRF_COOKIE_SECURE` | Secure CSRF cookies | `True` |
| `SECURE_HSTS_SECONDS` | HSTS max-age | `31536000` |

### Optional Services

| Variable | Description | Example |
|----------|-------------|---------|
| `SENTRY_DSN` | Sentry error tracking | `https://xxx@sentry.io/xxx` |
| `AWS_ACCESS_KEY_ID` | AWS access key (for S3) | `AKIAXXXXXXXX` |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | `your-secret` |
| `AWS_STORAGE_BUCKET_NAME` | S3 bucket name | `aureon-media` |

See `.env.example` for a complete list of all available environment variables.

---

## Architecture

### System Architecture Diagram

```
                                    [Internet]
                                         |
                                         v
                              +--------------------+
                              |      Nginx         |
                              |   (Reverse Proxy)  |
                              |   SSL/TLS, Static  |
                              +--------------------+
                                         |
                    +--------------------+--------------------+
                    |                    |                    |
                    v                    v                    v
           +----------------+   +----------------+   +----------------+
           |   Django App   |   |  Celery Worker |   |  Celery Beat   |
           |   (Gunicorn)   |   | (Background)   |   |  (Scheduler)   |
           +----------------+   +----------------+   +----------------+
                    |                    |                    |
                    +--------------------+--------------------+
                    |                    |
                    v                    v
           +----------------+   +----------------+
           |   PostgreSQL   |   |     Redis      |
           |   (Database)   |   | (Cache/Broker) |
           +----------------+   +----------------+
                    |
                    v
           +----------------+
           |    Stripe      |
           |   (Payments)   |
           +----------------+
```

### Multi-Tenancy

Aureon uses a simplified single-database architecture optimized for rapid development. Multi-tenancy support is planned for a future phase.

### Application Structure

```
aureon/
|-- apps/
|   |-- accounts/         # User authentication, 2FA, API keys
|   |-- clients/          # CRM and contact management
|   |-- contracts/        # Contract creation, templates, e-signatures
|   |-- invoicing/        # Invoice generation, PDF creation
|   |-- payments/         # Stripe payment processing
|   |-- subscriptions/   # Recurring billing and subscriptions
|   |-- notifications/    # Email templates and automation
|   |-- analytics/        # Dashboards, MRR tracking, metrics
|   |-- documents/        # Document storage and management
|   |-- webhooks/         # Stripe and external webhook handling
|   |-- integrations/     # Third-party integrations
|-- config/               # Django settings and configuration
|-- docker/               # Docker configuration files
|-- frontend/             # React dashboard application
|-- static/               # Static assets
|-- templates/            # Django templates
+-- tests/                # Test suite
```

### Data Flow

1. **Lead Capture** - Client record created in CRM
2. **Proposal** - Contract template generated with dynamic fields
3. **E-Signature** - Contract signed digitally by both parties
4. **Milestone/Trigger** - Invoice automatically created
5. **Payment** - Stripe processes payment via webhook
6. **Receipt** - Instant delivery to client via email
7. **Analytics** - Real-time dashboard updates with metrics

---

## API Documentation

### API Base URL

- **Development**: `http://localhost:8001/api/`
- **Production**: `https://aureon.rhematek-solutions.com/api/`

### Interactive Documentation

- **Swagger UI**: `/api/docs/`
- **ReDoc**: `/api/redoc/`
- **OpenAPI Schema**: `/api/schema/`

### API Endpoints Overview

| Module | Endpoint | Description |
|--------|----------|-------------|
| Authentication | `/api/auth/` | JWT login, registration, 2FA |
| Clients | `/api/api/clients/` | Client CRUD, notes, documents |
| Contracts | `/api/api/contracts/` | Contract management, milestones |
| Invoices | `/api/api/invoices/` | Invoice generation, payments |
| Payments | `/api/api/payments/` | Payment processing, refunds |
| Analytics | `/api/analytics/` | Dashboard metrics, reports |
| Webhooks | `/webhooks/stripe/` | Stripe webhook endpoint |

For detailed API documentation with request/response examples, see [API_DOCUMENTATION.md](API_DOCUMENTATION.md).

---

## Contributing

We welcome contributions from the community! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

### Development Setup

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Quality

**Platform Metrics**: 2711 tests passing, 99.83% code coverage

- Run tests: `pytest`
- Check coverage: `pytest` (coverage is auto-configured via `.coveragerc`)
- Lint code: `flake8 apps/`
- Format code: `black apps/`
- Sort imports: `isort apps/`

---

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

---

## Support

### Contact

- **CEO**: Stephane Arthur Victor - stephane@rhematek-solutions.com
- **Support**: support@rhematek-solutions.com
- **Security Issues**: security@rhematek-solutions.com
- **System Alerts**: alerts@rhematek-solutions.com

### Resources

- [Documentation](https://docs.aureon.rhematek-solutions.com)
- [Community Forum](https://community.aureon.rhematek-solutions.com)
- [Issue Tracker](https://github.com/rhematek-solutions/aureon/issues)
- [Roadmap](https://github.com/rhematek-solutions/aureon/projects)

---

## Acknowledgments

- Django and Django REST Framework communities
- Stripe for payment infrastructure
- All open-source contributors

---

**Aureon** - Automated Financial Management Platform
Copyright 2025 Rhematek Solutions. All rights reserved.

*From Signature to Cash, Everything Runs Automatically.*
