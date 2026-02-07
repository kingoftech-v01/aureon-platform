# Aureon Platform - Project Roadmap & Strategy

## Decision (2026-02-07)

### Problem
- Multi-tenancy (django-tenants) adds massive complexity
- Too many apps at once = impossible to test properly
- Need a working MVP first before scaling

### Strategy: Phased Approach

---

## Phase 1: Remove Multi-Tenancy
**Goal:** Simplify the entire codebase to a single-project architecture.

- Remove `django-tenants` dependency
- Remove `apps/tenants/` app entirely
- Remove tenant FK from all models (User, Client, Contract, Invoice, etc.)
- Simplify `config/settings.py` (remove tenant middleware, tenant DB router)
- Simplify `config/urls.py` (remove tenant URL routing)
- Remove `config/db_router.py` tenant logic
- Update all views/serializers to remove tenant filtering
- Remove domain management features
- Single database, no schema-per-tenant

---

## Phase 2: Focus on MVP-Critical Apps (100% functional + 100% coverage)
**Goal:** Make the core financial workflow work end-to-end perfectly.

### MVP Core Apps (in priority order):
1. **accounts** - User auth, registration, login, roles, 2FA
2. **clients** - Client management (CRM basics)
3. **contracts** - Contract creation, templates, e-signature workflow
4. **invoicing** - Invoice generation, sending, tracking
5. **payments** - Stripe payments, refunds, receipts
6. **notifications** - Email/in-app notifications for the above workflows
7. **core** - Shared utilities, validators, security

### For each MVP app:
- [ ] All models fully implemented and tested
- [ ] All views/API endpoints working
- [ ] All serializers validated
- [ ] All Celery tasks functional (not stubs)
- [ ] All signals connected
- [ ] Admin interface working
- [ ] 100% code coverage with unit + integration + security tests

---

## Phase 3: Secondary Apps (implement one by one)
**Goal:** Add features incrementally, each with 100% coverage before moving on.

### Secondary Apps:
8. **subscriptions** - Recurring billing via Stripe
9. **analytics** - Dashboards, metrics, reporting
10. **documents** - Document vault, file management
11. **webhooks** - Incoming/outgoing webhook management
12. **integrations** - QuickBooks, Xero, calendar sync
13. **website** - Marketing site, blog, landing pages

### For each secondary app:
- [ ] Full implementation (no stubs)
- [ ] 100% code coverage
- [ ] Integration tested with MVP apps

---

## Phase 4: Re-introduce Multi-Tenancy
**Goal:** Scale to multi-tenant SaaS once everything works perfectly.

- Re-add `django-tenants`
- Add tenant FK back to all models
- Implement tenant isolation (schema-per-tenant or row-level)
- Tenant-aware middleware and URL routing
- Domain management
- Tenant onboarding flow
- Full test coverage for multi-tenant scenarios

---

## Apps to Remove/Archive (Legacy Scaffolds)
- `management/` - Legacy scaffold, can be deleted
- `main/` - Legacy scaffold, can be deleted
- `finance/` - Legacy scaffold, can be deleted
- `custom_account/` - Legacy scaffold, can be deleted
- `frontend-marketing/` - Empty directory, delete

---

## Current State (Before Phase 1)
- 14 Django apps, most partially implemented
- django-tenants adds complexity to every DB operation
- ~57% code coverage
- Many Celery tasks were stubs (now implemented)
- Frontend (React) has real API calls but needs backend to work
