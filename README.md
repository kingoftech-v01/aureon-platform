# Aureon by Rhematek Solutions

**From Signature to Cash, Everything Runs Automatically.**

Aureon is a comprehensive SaaS platform that automates end-to-end client financial workflows: lead-to-contract, contract generation and e-signature, auto-invoicing, payment collection via Stripe, receipt delivery, and real-time dashboards.

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE.md)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/django-5.0-green.svg)](https://www.djangoproject.com/)
[![React](https://img.shields.io/badge/react-18+-blue.svg)](https://reactjs.org/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)
- [Support](#support)

---

## Overview

### Mission

Eliminate the complexity of financial administration for modern businesses. Empower agencies, freelancers, and startups to automate their contracts, billing, and payments through an intelligent, secure, and transparent platform.

### Target Markets

- **Digital Agencies**: Managing recurring client contracts and multiple revenue streams
- **Freelancers & Coaches**: Professional solo operators managing multiple clients
- **SaaS Startups**: Subscription-based businesses requiring tight financial integration

### Value Propositions

- **End-to-end automation**: From proposal to payment with minimal manual intervention
- **Faster cash flow**: Automatic invoice creation and Stripe-based collection
- **Transparent client experience**: Branded contracts, e-signatures, and receipting in a single portal
- **Compliance and auditability**: Immutable activity logs, digital signatures, and versioned contracts
- **Scalable pricing and billing**: Time-based, milestone-based, and subscription models

---

## Key Features

### 🏢 Client Onboarding and CRM
- Contact management with roles, tags, and lifecycle stages
- Lead capture via embeddable forms and integrations
- Customizable client portals with branded UI

### 📄 Contracts and E-Signatures
- Contract templates with dynamic fields and placeholders
- Automated proposal-to-contract conversion with version control
- E-signature workflows (eIDAS/ESIGN/UETA compliant)
- Milestone and conditional clauses

### 💰 Automated Invoicing
- Invoice generation tied to contract milestones or recurring billing
- Stripe integration for payments, installments, and automated retries
- Proration, credits, refunds, and tax handling (VAT/GST)

### 📧 Receipts and Notifications
- Instant receipts sent by email or within the client portal
- Real-time payment status and invoice aging reminders
- Audit logs and exportable reports for accounting

### 💳 Payments and Treasury Automation
- Stripe webhooks for status updates and automations
- Multi-currency and multi-region tax configurations
- Reconciliation tools for QuickBooks and Xero

### 📁 Document Management
- Central document vault for contracts, receipts, and attachments
- Role-based access control (RBAC) and granular permissions
- Encryption at rest and in transit

### 📊 Analytics and Reporting
- Cash flow dashboards and aging reports
- Conversion funnels: lead → proposal → contract → payment
- Revenue recognition reports for GAAP/IFRS compliance

### 🔐 Security and Compliance
- SOC 2-type controls and secure development lifecycle
- GDPR/CCPA data handling and data subject access requests
- Digital signatures with tamper-evident records

---

## Technology Stack

### Backend
- **Framework**: Django 5.0 with Django REST Framework
- **Database**: PostgreSQL 15 with multi-schema tenancy (django-tenants)
- **Caching**: Redis 7
- **Task Queue**: Celery with Celery Beat
- **Authentication**: Django Allauth + JWT
- **Payments**: Stripe + dj-stripe

### Frontend
- **Framework**: React 18+ with TypeScript
- **UI Library**: Bootstrap 5
- **State Management**: React Context + React Query
- **Charts**: Chart.js / Recharts
- **Forms**: React Hook Form

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Web Server**: Nginx with SSL/TLS (Let's Encrypt)
- **Monitoring**: Prometheus + Grafana
- **Error Tracking**: Sentry
- **CI/CD**: GitHub Actions

### Security
- Argon2 password hashing
- JWT token authentication
- Content Security Policy (CSP)
- CORS protection
- Rate limiting and brute force protection (django-axes)

---

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

### Installation

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
docker-compose -f docker-compose.prod.yml up --build
```

4. **Run database migrations**
```bash
docker-compose exec web python manage.py migrate
```

5. **Create a superuser**
```bash
docker-compose exec web python manage.py createsuperuser
```

6. **Access the application**
- **Main Site**: https://aureon.rhematek-solutions.com
- **Admin Panel**: https://aureon.rhematek-solutions.com/admin
- **API Documentation**: https://aureon.rhematek-solutions.com/api/docs

---

## Architecture

### Multi-Tenancy

Aureon uses **Django-Tenants** to provide full schema-based tenant isolation. Each organization (tenant) has its own PostgreSQL schema, ensuring complete data separation while running on a single codebase.

### Application Structure

```
aureon/
├── apps/
│   ├── tenants/          # Tenant management
│   ├── accounts/         # User authentication
│   ├── clients/          # CRM and contact management
│   ├── contracts/        # Contract creation and e-signatures
│   ├── invoicing/        # Invoice generation
│   ├── payments/         # Stripe payment processing
│   ├── notifications/    # Email and SMS notifications
│   ├── analytics/        # Dashboards and reporting
│   ├── documents/        # Document storage and management
│   ├── webhooks/         # External webhook management
│   ├── integrations/     # Third-party integrations
│   └── website/          # Public marketing website
├── config/               # Django settings and configuration
├── docker/               # Docker configuration files
├── frontend/             # React dashboard application
├── static/               # Static assets
├── templates/            # Django templates
└── tests/                # Test suite
```

### Data Flow

1. **Lead Capture** → Client record created
2. **Proposal** → Contract template generated
3. **E-Signature** → Contract signed digitally
4. **Milestone/Trigger** → Invoice automatically created
5. **Payment** → Stripe processes payment
6. **Receipt** → Instant delivery to client
7. **Analytics** → Real-time dashboard updates

---

## Documentation

- [Setup Instructions](docs/SETUP.md)
- [API Documentation](https://aureon.rhematek-solutions.com/api/docs)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Architecture Overview](docs/ARCHITECTURE.md)
- [Contributing Guide](CONTRIBUTING.md)
- [Security Policy](SECURITY.md)
- [Changelog](CHANGELOG.md)

---

## Contributing

We welcome contributions from the community! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

### Development Setup

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

---

## Support

### Contact

- **CEO**: Stéphane Arthur Victor - stephane@rhematek-solutions.com
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
© 2025 Rhematek Solutions. All rights reserved.

*From Signature to Cash, Everything Runs Automatically.*
