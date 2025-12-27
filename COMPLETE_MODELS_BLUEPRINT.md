# Aureon SaaS Platform - Complete Models Blueprint

## Complete Django Apps Structure

This document provides the complete model definitions for all Django apps in the Aureon SaaS platform.

---

## ✅ 1. apps/tenants/ - IMPLEMENTED

### Models:
- **Tenant**: Organization with multi-tenancy support
- **Domain**: Domain management for tenants

**Status**: ✅ Complete (models, admin, serializers, views, URLs)

---

## ✅ 2. apps/accounts/ - IMPLEMENTED

### Models:
- **User**: Custom user with roles and permissions
- **UserInvitation**: Team invitation system
- **ApiKey**: API authentication

**Status**: ✅ Complete (models, admin, serializers, views, URLs)

---

## ✅ 3. apps/clients/ - MODELS IMPLEMENTED

### Models:
- **Client**: CRM client/contact management
- **ClientNote**: Notes and interactions
- **ClientDocument**: Document attachments

**Status**: ✅ Models + Admin complete
**Pending**: Serializers, Views, URLs

---

## 4. apps/contracts/ - CORE BUSINESS LOGIC

### Required Models:

#### **Contract**
```python
class Contract(models.Model):
    """Main contract model with versioning and e-signature support."""

    # Contract Types
    ONE_TIME = 'one_time'
    RECURRING = 'recurring'
    MILESTONE = 'milestone'

    # Status
    DRAFT = 'draft'
    SENT = 'sent'
    VIEWED = 'viewed'
    SIGNED = 'signed'
    ACTIVE = 'active'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

    id = UUIDField(primary_key=True)
    client = ForeignKey(Client)
    template = ForeignKey(ContractTemplate, null=True)

    # Contract Details
    title = CharField(max_length=255)
    contract_number = CharField(max_length=50, unique=True)
    contract_type = CharField(choices=CONTRACT_TYPE_CHOICES)
    status = CharField(choices=STATUS_CHOICES, default=DRAFT)

    # Financial
    total_value = DecimalField(max_digits=12, decimal_places=2)
    currency = CharField(max_length=3, default='USD')

    # Content
    content = TextField()  # HTML or Markdown
    terms_and_conditions = TextField()

    # Dates
    start_date = DateField()
    end_date = DateField(null=True)
    signed_at = DateTimeField(null=True)

    # E-Signature
    signature_provider = CharField()  # 'docusign', 'internal', etc.
    signature_envelope_id = CharField()
    signer_name = CharField()
    signer_email = EmailField()
    signer_ip = GenericIPAddressField(null=True)
    signature_image = ImageField(null=True)

    # PDF Storage
    pdf_file = FileField(upload_to='contracts/pdfs/')
    signed_pdf_file = FileField(null=True)

    # Version Control
    version = PositiveIntegerField(default=1)
    parent_contract = ForeignKey('self', null=True)

    # Metadata
    created_by = ForeignKey(User)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    metadata = JSONField(default=dict)
```

#### **ContractTemplate**
```python
class ContractTemplate(models.Model):
    """Reusable contract templates."""

    id = UUIDField(primary_key=True)
    name = CharField(max_length=255)
    category = CharField()  # 'services', 'consulting', 'saas', etc.
    content = TextField()  # Template with {{placeholders}}

    # Variables/Placeholders
    variables = JSONField(default=list)  # List of variable names

    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
```

#### **ContractMilestone**
```python
class ContractMilestone(models.Model):
    """Milestones for milestone-based contracts."""

    id = UUIDField(primary_key=True)
    contract = ForeignKey(Contract)

    title = CharField(max_length=255)
    description = TextField()
    amount = DecimalField(max_digits=12, decimal_places=2)
    due_date = DateField()

    # Status
    is_completed = BooleanField(default=False)
    completed_at = DateTimeField(null=True)
    invoice = ForeignKey('invoicing.Invoice', null=True)

    order = PositiveIntegerField(default=0)
```

---

## 5. apps/invoicing/ - BILLING ENGINE

### Required Models:

#### **Invoice**
```python
class Invoice(models.Model):
    """Invoice model with Stripe integration."""

    # Status
    DRAFT = 'draft'
    SENT = 'sent'
    VIEWED = 'viewed'
    PAID = 'paid'
    PARTIALLY_PAID = 'partially_paid'
    OVERDUE = 'overdue'
    CANCELLED = 'cancelled'
    REFUNDED = 'refunded'

    id = UUIDField(primary_key=True)
    invoice_number = CharField(max_length=50, unique=True)

    # Relationships
    client = ForeignKey(Client)
    contract = ForeignKey(Contract, null=True)
    milestone = ForeignKey(ContractMilestone, null=True)

    # Financial
    subtotal = DecimalField(max_digits=12, decimal_places=2)
    tax_rate = DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_amount = DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = DecimalField(max_digits=12, decimal_places=2)
    amount_paid = DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_due = DecimalField(max_digits=12, decimal_places=2)

    currency = CharField(max_length=3, default='USD')

    # Dates
    issue_date = DateField()
    due_date = DateField()
    paid_at = DateTimeField(null=True)

    # Status
    status = CharField(choices=STATUS_CHOICES, default=DRAFT)

    # Stripe Integration
    stripe_invoice_id = CharField(max_length=255, null=True)
    stripe_payment_intent_id = CharField(max_length=255, null=True)

    # Payment Link
    payment_link = URLField(null=True)
    payment_link_expires_at = DateTimeField(null=True)

    # PDF
    pdf_file = FileField(upload_to='invoices/pdfs/')

    # Recurring
    is_recurring = BooleanField(default=False)
    recurrence_interval = CharField()  # 'monthly', 'quarterly', 'yearly'
    next_invoice_date = DateField(null=True)

    # Reminders
    reminder_sent_count = PositiveIntegerField(default=0)
    last_reminder_sent_at = DateTimeField(null=True)

    # Notes
    notes = TextField(blank=True)

    # Metadata
    created_by = ForeignKey(User)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    metadata = JSONField(default=dict)
```

#### **InvoiceItem**
```python
class InvoiceItem(models.Model):
    """Line items for invoices."""

    id = UUIDField(primary_key=True)
    invoice = ForeignKey(Invoice, related_name='items')

    description = CharField(max_length=255)
    quantity = DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = DecimalField(max_digits=12, decimal_places=2)
    amount = DecimalField(max_digits=12, decimal_places=2)

    # Tax
    tax_rate = DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_amount = DecimalField(max_digits=12, decimal_places=2, default=0)

    order = PositiveIntegerField(default=0)
```

#### **RecurringInvoice**
```python
class RecurringInvoice(models.Model):
    """Recurring invoice schedules."""

    id = UUIDField(primary_key=True)
    client = ForeignKey(Client)
    contract = ForeignKey(Contract, null=True)

    # Schedule
    interval = CharField()  # 'daily', 'weekly', 'monthly', 'yearly'
    interval_count = PositiveIntegerField(default=1)
    start_date = DateField()
    end_date = DateField(null=True)  # null = no end

    # Template
    amount = DecimalField(max_digits=12, decimal_places=2)
    description = CharField(max_length=255)
    items = JSONField(default=list)

    # Status
    is_active = BooleanField(default=True)
    last_invoice_created_at = DateTimeField(null=True)
    next_invoice_date = DateField()

    created_at = DateTimeField(auto_now_add=True)
```

---

## 6. apps/payments/ - STRIPE INTEGRATION

### Required Models:

#### **Payment**
```python
class Payment(models.Model):
    """Payment records linked to invoices."""

    # Status
    PENDING = 'pending'
    PROCESSING = 'processing'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'
    REFUNDED = 'refunded'
    CANCELLED = 'cancelled'

    # Payment Methods
    CARD = 'card'
    BANK_TRANSFER = 'bank_transfer'
    ACH = 'ach'
    SEPA = 'sepa'

    id = UUIDField(primary_key=True)
    payment_number = CharField(max_length=50, unique=True)

    # Relationships
    invoice = ForeignKey(Invoice)
    client = ForeignKey(Client)

    # Financial
    amount = DecimalField(max_digits=12, decimal_places=2)
    currency = CharField(max_length=3)
    fee = DecimalField(max_digits=12, decimal_places=2, default=0)
    net_amount = DecimalField(max_digits=12, decimal_places=2)

    # Stripe
    stripe_payment_intent_id = CharField(max_length=255, unique=True)
    stripe_charge_id = CharField(max_length=255, null=True)
    stripe_payment_method_id = CharField(max_length=255, null=True)

    # Payment Details
    payment_method = CharField(choices=METHOD_CHOICES)
    card_last4 = CharField(max_length=4, null=True)
    card_brand = CharField(max_length=20, null=True)

    # Status
    status = CharField(choices=STATUS_CHOICES, default=PENDING)
    failure_reason = CharField(max_length=255, null=True)

    # Dates
    paid_at = DateTimeField(null=True)
    refunded_at = DateTimeField(null=True)

    # Receipt
    receipt_url = URLField(null=True)
    receipt_number = CharField(max_length=50, null=True)

    # Metadata
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    metadata = JSONField(default=dict)
```

#### **PaymentMethod**
```python
class PaymentMethod(models.Model):
    """Saved payment methods for clients."""

    id = UUIDField(primary_key=True)
    client = ForeignKey(Client, related_name='payment_methods')

    # Stripe
    stripe_payment_method_id = CharField(max_length=255, unique=True)

    # Card Details
    type = CharField(max_length=20)  # 'card', 'bank_account', etc.
    card_brand = CharField(max_length=20, null=True)
    card_last4 = CharField(max_length=4, null=True)
    card_exp_month = PositiveIntegerField(null=True)
    card_exp_year = PositiveIntegerField(null=True)

    # Status
    is_default = BooleanField(default=False)
    is_active = BooleanField(default=True)

    created_at = DateTimeField(auto_now_add=True)
```

#### **Refund**
```python
class Refund(models.Model):
    """Refund records."""

    id = UUIDField(primary_key=True)
    payment = ForeignKey(Payment, related_name='refunds')

    amount = DecimalField(max_digits=12, decimal_places=2)
    reason = CharField(max_length=255)

    # Stripe
    stripe_refund_id = CharField(max_length=255, unique=True)

    status = CharField(max_length=20)
    processed_at = DateTimeField(null=True)

    created_at = DateTimeField(auto_now_add=True)
```

---

## 7. apps/notifications/ - NOTIFICATION ENGINE

### Required Models:

#### **NotificationTemplate**
```python
class NotificationTemplate(models.Model):
    """Email/SMS templates."""

    id = UUIDField(primary_key=True)
    name = CharField(max_length=255)
    event_type = CharField()  # 'invoice_sent', 'payment_received', etc.

    # Email
    email_subject = CharField(max_length=255)
    email_body = TextField()  # HTML template

    # SMS
    sms_body = CharField(max_length=160, blank=True)

    # Variables
    variables = JSONField(default=list)

    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
```

#### **Notification**
```python
class Notification(models.Model):
    """Notification records."""

    # Types
    EMAIL = 'email'
    SMS = 'sms'
    IN_APP = 'in_app'

    id = UUIDField(primary_key=True)
    user = ForeignKey(User)

    notification_type = CharField(choices=TYPE_CHOICES)
    title = CharField(max_length=255)
    message = TextField()

    # Status
    is_read = BooleanField(default=False)
    read_at = DateTimeField(null=True)

    # Links
    action_url = URLField(null=True)

    created_at = DateTimeField(auto_now_add=True)
```

#### **EmailLog**
```python
class EmailLog(models.Model):
    """Email delivery tracking."""

    id = UUIDField(primary_key=True)
    recipient = EmailField()
    subject = CharField(max_length=255)
    body = TextField()

    # Status
    status = CharField()  # 'queued', 'sent', 'delivered', 'failed', 'bounced'
    sent_at = DateTimeField(null=True)
    delivered_at = DateTimeField(null=True)
    opened_at = DateTimeField(null=True)

    # Provider
    provider = CharField()  # 'ses', 'sendgrid', etc.
    provider_message_id = CharField(max_length=255, null=True)

    error_message = TextField(null=True)
    created_at = DateTimeField(auto_now_add=True)
```

---

## 8. apps/analytics/ - REPORTING ENGINE

### Required Models:

#### **AnalyticsSnapshot**
```python
class AnalyticsSnapshot(models.Model):
    """Daily analytics snapshots."""

    id = UUIDField(primary_key=True)
    snapshot_date = DateField(unique=True)

    # Revenue Metrics
    daily_revenue = DecimalField(max_digits=12, decimal_places=2)
    monthly_recurring_revenue = DecimalField(max_digits=12, decimal_places=2)
    annual_recurring_revenue = DecimalField(max_digits=12, decimal_places=2)

    # Client Metrics
    total_clients = PositiveIntegerField()
    active_clients = PositiveIntegerField()
    new_clients = PositiveIntegerField()
    churned_clients = PositiveIntegerField()

    # Invoice Metrics
    invoices_sent = PositiveIntegerField()
    invoices_paid = PositiveIntegerField()
    invoices_overdue = PositiveIntegerField()

    # Contract Metrics
    active_contracts = PositiveIntegerField()
    contract_value = DecimalField(max_digits=12, decimal_places=2)

    created_at = DateTimeField(auto_now_add=True)
```

#### **RevenueMetric**
```python
class RevenueMetric(models.Model):
    """Detailed revenue tracking."""

    id = UUIDField(primary_key=True)
    metric_date = DateField()

    # Revenue
    gross_revenue = DecimalField(max_digits=12, decimal_places=2)
    net_revenue = DecimalField(max_digits=12, decimal_places=2)
    fees = DecimalField(max_digits=12, decimal_places=2)

    # Breakdown
    revenue_by_type = JSONField(default=dict)  # {one_time:, recurring:, milestone:}

    created_at = DateTimeField(auto_now_add=True)
```

---

## 9. apps/documents/ - DOCUMENT MANAGEMENT

### Required Models:

#### **Document**
```python
class Document(models.Model):
    """Central document repository."""

    # Types
    CONTRACT = 'contract'
    INVOICE = 'invoice'
    RECEIPT = 'receipt'
    ATTACHMENT = 'attachment'

    id = UUIDField(primary_key=True)
    document_type = CharField(choices=TYPE_CHOICES)

    name = CharField(max_length=255)
    file = FileField(upload_to='documents/')
    file_size = PositiveIntegerField()
    file_hash = CharField(max_length=64)  # SHA-256 for integrity

    # Relationships (generic)
    related_client = ForeignKey(Client, null=True)
    related_contract = ForeignKey(Contract, null=True)
    related_invoice = ForeignKey(Invoice, null=True)

    # Versioning
    version = PositiveIntegerField(default=1)
    parent_document = ForeignKey('self', null=True)

    uploaded_by = ForeignKey(User)
    created_at = DateTimeField(auto_now_add=True)
```

---

## 10. apps/webhooks/ - WEBHOOK MANAGEMENT

### Required Models:

#### **Webhook**
```python
class Webhook(models.Model):
    """Outgoing webhook configurations."""

    id = UUIDField(primary_key=True)
    url = URLField()
    events = JSONField(default=list)  # List of event types to trigger

    # Authentication
    secret = CharField(max_length=255)  # For signature verification

    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
```

#### **WebhookEvent**
```python
class WebhookEvent(models.Model):
    """Webhook event log."""

    id = UUIDField(primary_key=True)
    webhook = ForeignKey(Webhook)

    event_type = CharField(max_length=100)
    payload = JSONField()

    # Delivery
    status = CharField()  # 'pending', 'delivered', 'failed'
    attempts = PositiveIntegerField(default=0)
    last_attempt_at = DateTimeField(null=True)
    delivered_at = DateTimeField(null=True)

    response_status_code = PositiveIntegerField(null=True)
    response_body = TextField(null=True)

    created_at = DateTimeField(auto_now_add=True)
```

---

## 11. apps/integrations/ - THIRD-PARTY INTEGRATIONS

### Required Models:

#### **Integration**
```python
class Integration(models.Model):
    """Available integrations."""

    # Types
    QUICKBOOKS = 'quickbooks'
    XERO = 'xero'
    ZAPIER = 'zapier'
    SLACK = 'slack'

    id = UUIDField(primary_key=True)
    integration_type = CharField(choices=TYPE_CHOICES)

    name = CharField(max_length=255)
    description = TextField()
    icon = ImageField(null=True)

    is_available = BooleanField(default=True)
```

#### **IntegrationConnection**
```python
class IntegrationConnection(models.Model):
    """Active integration connections."""

    id = UUIDField(primary_key=True)
    integration = ForeignKey(Integration)

    # OAuth Tokens
    access_token = CharField(max_length=500)
    refresh_token = CharField(max_length=500, null=True)
    token_expires_at = DateTimeField(null=True)

    # Configuration
    settings = JSONField(default=dict)

    is_active = BooleanField(default=True)
    last_synced_at = DateTimeField(null=True)

    created_at = DateTimeField(auto_now_add=True)
```

---

## Summary

### Total Models: 40+

**Implemented (8)**:
1. Tenant
2. Domain
3. User
4. UserInvitation
5. ApiKey
6. Client
7. ClientNote
8. ClientDocument

**Remaining (32)**:
- Contracts: Contract, ContractTemplate, ContractMilestone (3)
- Invoicing: Invoice, InvoiceItem, RecurringInvoice (3)
- Payments: Payment, PaymentMethod, Refund (3)
- Notifications: NotificationTemplate, Notification, EmailLog (3)
- Analytics: AnalyticsSnapshot, RevenueMetric (2)
- Documents: Document, DocumentVersion (2)
- Webhooks: Webhook, WebhookEvent (2)
- Integrations: Integration, IntegrationConnection (2)

---

**Next Implementation Priority**:
1. Contracts app (core business logic)
2. Invoicing app (revenue generation)
3. Payments app (Stripe integration)
4. Notifications app (customer communication)
5. Analytics app (business intelligence)
