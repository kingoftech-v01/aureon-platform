"""
Invoice and invoice item models.
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal


class Invoice(models.Model):
    """
    Invoice model for billing clients.
    """

    # Invoice Status
    DRAFT = 'draft'
    SENT = 'sent'
    VIEWED = 'viewed'
    PAID = 'paid'
    PARTIALLY_PAID = 'partially_paid'
    OVERDUE = 'overdue'
    CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (DRAFT, _('Draft')),
        (SENT, _('Sent')),
        (VIEWED, _('Viewed')),
        (PAID, _('Paid')),
        (PARTIALLY_PAID, _('Partially Paid')),
        (OVERDUE, _('Overdue')),
        (CANCELLED, _('Cancelled')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Invoice Number (auto-generated)
    invoice_number = models.CharField(
        _('Invoice Number'),
        max_length=50,
        unique=True,
        help_text=_('Unique invoice identifier (e.g., INV-001)')
    )

    # Client Relationship
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE,
        related_name='invoices',
        help_text=_('Client being invoiced')
    )

    # Contract Relationship (optional)
    contract = models.ForeignKey(
        'contracts.Contract',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
        help_text=_('Associated contract (if applicable)')
    )

    # Status
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=DRAFT
    )

    # Dates
    issue_date = models.DateField(
        _('Issue Date'),
        help_text=_('Date the invoice was issued')
    )

    due_date = models.DateField(
        _('Due Date'),
        help_text=_('Payment due date')
    )

    # Financial Details
    subtotal = models.DecimalField(
        _('Subtotal'),
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_('Sum of all line items')
    )

    tax_rate = models.DecimalField(
        _('Tax Rate (%)'),
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_('Tax rate as percentage')
    )

    tax_amount = models.DecimalField(
        _('Tax Amount'),
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_('Calculated tax amount')
    )

    discount_amount = models.DecimalField(
        _('Discount Amount'),
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_('Discount applied to invoice')
    )

    total = models.DecimalField(
        _('Total'),
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_('Total amount due')
    )

    paid_amount = models.DecimalField(
        _('Paid Amount'),
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_('Amount paid so far')
    )

    currency = models.CharField(
        _('Currency'),
        max_length=3,
        default='USD',
        help_text=_('Currency code (e.g., USD, EUR, GBP)')
    )

    # Payment Information
    payment_method = models.CharField(
        _('Payment Method'),
        max_length=50,
        blank=True,
        help_text=_('Payment method used')
    )

    payment_reference = models.CharField(
        _('Payment Reference'),
        max_length=255,
        blank=True,
        help_text=_('Payment reference or transaction ID')
    )

    paid_at = models.DateTimeField(
        _('Paid At'),
        null=True,
        blank=True,
        help_text=_('When the invoice was fully paid')
    )

    # Notes and Terms
    notes = models.TextField(
        _('Notes'),
        blank=True,
        help_text=_('Additional notes for the client')
    )

    terms = models.TextField(
        _('Payment Terms'),
        blank=True,
        help_text=_('Payment terms and conditions')
    )

    # Document Management
    pdf_file = models.FileField(
        _('PDF File'),
        upload_to='invoices/pdfs/',
        blank=True,
        null=True,
        help_text=_('Generated PDF invoice')
    )

    # Stripe Integration
    stripe_invoice_id = models.CharField(
        _('Stripe Invoice ID'),
        max_length=255,
        blank=True,
        help_text=_('Stripe invoice ID for payment tracking')
    )

    stripe_payment_intent_id = models.CharField(
        _('Stripe Payment Intent ID'),
        max_length=255,
        blank=True,
        help_text=_('Stripe payment intent ID')
    )

    # Email Tracking
    sent_at = models.DateTimeField(
        _('Sent At'),
        null=True,
        blank=True,
        help_text=_('When the invoice was sent to the client')
    )

    viewed_at = models.DateTimeField(
        _('Viewed At'),
        null=True,
        blank=True,
        help_text=_('When the client first viewed the invoice')
    )

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    # Metadata
    metadata = models.JSONField(
        _('Metadata'),
        default=dict,
        blank=True,
        help_text=_('Additional metadata in JSON format')
    )

    class Meta:
        verbose_name = _('Invoice')
        verbose_name_plural = _('Invoices')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['client']),
            models.Index(fields=['contract']),
            models.Index(fields=['status']),
            models.Index(fields=['issue_date', 'due_date']),
        ]

    def __str__(self):
        return f"{self.invoice_number} - {self.client.get_display_name()}"

    def save(self, *args, **kwargs):
        """Generate invoice number if not set."""
        if not self.invoice_number:
            # Get the latest invoice number
            last_invoice = Invoice.objects.order_by('-invoice_number').first()
            if last_invoice and last_invoice.invoice_number.startswith('INV-'):
                try:
                    last_num = int(last_invoice.invoice_number.split('-')[1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1

            self.invoice_number = f"INV-{new_num:05d}"

        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        """Check if invoice is overdue."""
        from django.utils import timezone
        if self.status in [self.PAID, self.CANCELLED]:
            return False
        return timezone.now().date() > self.due_date

    @property
    def balance_due(self):
        """Calculate balance due."""
        return self.total - self.paid_amount

    @property
    def is_fully_paid(self):
        """Check if invoice is fully paid."""
        return self.paid_amount >= self.total

    def calculate_totals(self):
        """Calculate invoice totals from line items."""
        # Calculate subtotal from items
        items = self.items.all()
        self.subtotal = sum(item.amount for item in items)

        # Calculate tax
        self.tax_amount = (self.subtotal * self.tax_rate) / 100

        # Calculate total
        self.total = self.subtotal + self.tax_amount - self.discount_amount

        self.save()

    def mark_as_sent(self):
        """Mark invoice as sent."""
        from django.utils import timezone

        if self.status == self.DRAFT:
            self.status = self.SENT
            self.sent_at = timezone.now()
            self.save()

    def mark_as_paid(self, payment_amount=None, payment_method=None, payment_reference=None):
        """Mark invoice as paid."""
        from django.utils import timezone

        if payment_amount is None:
            payment_amount = self.balance_due

        self.paid_amount += payment_amount

        if self.is_fully_paid:
            self.status = self.PAID
            self.paid_at = timezone.now()
        else:
            self.status = self.PARTIALLY_PAID

        if payment_method:
            self.payment_method = payment_method
        if payment_reference:
            self.payment_reference = payment_reference

        self.save()

        # Update client financial summary
        self.client.update_financial_summary()

        # Update contract financial summary if applicable
        if self.contract:
            self.contract.update_financial_summary()

    def generate_pdf(self):
        """Generate PDF invoice."""
        from apps.invoicing.tasks import generate_invoice
        generate_invoice.delay(str(self.id))


class InvoiceItem(models.Model):
    """
    Line item in an invoice.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items',
        help_text=_('Invoice this item belongs to')
    )

    description = models.TextField(
        _('Description'),
        help_text=_('Description of the item or service')
    )

    quantity = models.DecimalField(
        _('Quantity'),
        max_digits=10,
        decimal_places=2,
        default=1,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_('Quantity of items')
    )

    unit_price = models.DecimalField(
        _('Unit Price'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_('Price per unit')
    )

    amount = models.DecimalField(
        _('Amount'),
        max_digits=12,
        decimal_places=2,
        help_text=_('Total amount (quantity × unit_price)')
    )

    # Order
    order = models.IntegerField(
        _('Order'),
        default=0,
        help_text=_('Display order of the item')
    )

    class Meta:
        verbose_name = _('Invoice Item')
        verbose_name_plural = _('Invoice Items')
        ordering = ['order']

    def __str__(self):
        return f"{self.description} - {self.amount}"

    def save(self, *args, **kwargs):
        """Calculate amount on save."""
        self.amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class RecurringInvoice(models.Model):
    """
    Recurring invoice template for automatic invoice generation.
    """

    # Frequency choices
    WEEKLY = 'weekly'
    BIWEEKLY = 'biweekly'
    MONTHLY = 'monthly'
    QUARTERLY = 'quarterly'
    ANNUALLY = 'annually'

    FREQUENCY_CHOICES = [
        (WEEKLY, _('Weekly')),
        (BIWEEKLY, _('Bi-weekly')),
        (MONTHLY, _('Monthly')),
        (QUARTERLY, _('Quarterly')),
        (ANNUALLY, _('Annually')),
    ]

    # Status choices
    ACTIVE = 'active'
    PAUSED = 'paused'
    CANCELLED = 'cancelled'
    COMPLETED = 'completed'

    STATUS_CHOICES = [
        (ACTIVE, _('Active')),
        (PAUSED, _('Paused')),
        (CANCELLED, _('Cancelled')),
        (COMPLETED, _('Completed')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE,
        related_name='recurring_invoices',
        help_text=_('Client to invoice')
    )

    contract = models.ForeignKey(
        'contracts.Contract',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recurring_invoices',
        help_text=_('Associated contract')
    )

    template_name = models.CharField(
        _('Template Name'),
        max_length=255,
        help_text=_('Descriptive name for this recurring invoice')
    )

    frequency = models.CharField(
        _('Frequency'),
        max_length=20,
        choices=FREQUENCY_CHOICES,
        default=MONTHLY
    )

    start_date = models.DateField(
        _('Start Date'),
        help_text=_('When to start generating invoices')
    )

    end_date = models.DateField(
        _('End Date'),
        blank=True,
        null=True,
        help_text=_('When to stop generating invoices (optional)')
    )

    next_run_date = models.DateField(
        _('Next Run Date'),
        help_text=_('Next date to generate invoice')
    )

    amount = models.DecimalField(
        _('Amount'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_('Invoice amount per cycle')
    )

    currency = models.CharField(
        _('Currency'),
        max_length=3,
        default='USD'
    )

    tax_rate = models.DecimalField(
        _('Tax Rate (%)'),
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    discount_amount = models.DecimalField(
        _('Discount Amount'),
        max_digits=12,
        decimal_places=2,
        default=0
    )

    items_template = models.JSONField(
        _('Items Template'),
        default=list,
        blank=True,
        help_text=_('Template for invoice line items')
    )

    auto_send = models.BooleanField(
        _('Auto Send'),
        default=True,
        help_text=_('Automatically send invoice after generation')
    )

    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=ACTIVE
    )

    invoices_generated = models.IntegerField(
        _('Invoices Generated'),
        default=0,
        help_text=_('Number of invoices generated')
    )

    last_generated_at = models.DateTimeField(
        _('Last Generated At'),
        null=True,
        blank=True
    )

    owner = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recurring_invoices',
        help_text=_('Owner of this recurring invoice')
    )

    notes = models.TextField(
        _('Notes'),
        blank=True
    )

    metadata = models.JSONField(
        _('Metadata'),
        default=dict,
        blank=True
    )

    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Recurring Invoice')
        verbose_name_plural = _('Recurring Invoices')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client']),
            models.Index(fields=['status']),
            models.Index(fields=['next_run_date']),
            models.Index(fields=['frequency']),
        ]

    def __str__(self):
        return f"{self.template_name} - {self.client} ({self.frequency})"

    @property
    def is_due(self):
        """Check if invoice is due for generation."""
        from django.utils import timezone
        if self.status != self.ACTIVE:
            return False
        return self.next_run_date <= timezone.now().date()

    def calculate_next_run_date(self):
        """Calculate the next run date based on frequency."""
        from dateutil.relativedelta import relativedelta

        if self.frequency == self.WEEKLY:
            self.next_run_date = self.next_run_date + relativedelta(weeks=1)
        elif self.frequency == self.BIWEEKLY:
            self.next_run_date = self.next_run_date + relativedelta(weeks=2)
        elif self.frequency == self.MONTHLY:
            self.next_run_date = self.next_run_date + relativedelta(months=1)
        elif self.frequency == self.QUARTERLY:
            self.next_run_date = self.next_run_date + relativedelta(months=3)
        elif self.frequency == self.ANNUALLY:
            self.next_run_date = self.next_run_date + relativedelta(years=1)

        # Check if completed
        if self.end_date and self.next_run_date > self.end_date:
            self.status = self.COMPLETED

        self.save(update_fields=['next_run_date', 'status', 'updated_at'])

    def generate_invoice(self):
        """Generate an invoice from this recurring template."""
        from django.utils import timezone

        invoice = Invoice.objects.create(
            client=self.client,
            contract=self.contract,
            status=Invoice.DRAFT,
            issue_date=timezone.now().date(),
            due_date=timezone.now().date() + timezone.timedelta(days=30),
            tax_rate=self.tax_rate,
            discount_amount=self.discount_amount,
            currency=self.currency,
            notes=self.notes,
        )

        # Create items from template
        for item_data in self.items_template:
            InvoiceItem.objects.create(
                invoice=invoice,
                description=item_data.get('description', ''),
                quantity=Decimal(str(item_data.get('quantity', 1))),
                unit_price=Decimal(str(item_data.get('unit_price', 0))),
                amount=Decimal(str(item_data.get('quantity', 1))) * Decimal(str(item_data.get('unit_price', 0))),
                order=item_data.get('order', 0),
            )

        # If no template items, create a single item with the amount
        if not self.items_template:
            InvoiceItem.objects.create(
                invoice=invoice,
                description=self.template_name,
                quantity=Decimal('1'),
                unit_price=self.amount,
                amount=self.amount,
            )

        invoice.calculate_totals()

        # Update tracking
        self.invoices_generated += 1
        self.last_generated_at = timezone.now()
        self.save(update_fields=['invoices_generated', 'last_generated_at', 'updated_at'])

        # Calculate next run date
        self.calculate_next_run_date()

        # Auto-send if enabled
        if self.auto_send:
            invoice.mark_as_sent()

        return invoice


class LateFeePolicy(models.Model):
    """
    Policy for calculating and applying late fees to overdue invoices.
    """

    # Fee type choices
    FLAT = 'flat'
    PERCENTAGE = 'percentage'

    FEE_TYPE_CHOICES = [
        (FLAT, _('Flat Amount')),
        (PERCENTAGE, _('Percentage of Invoice')),
    ]

    # Apply frequency choices
    ONCE = 'once'
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'

    APPLY_FREQUENCY_CHOICES = [
        (ONCE, _('Once')),
        (DAILY, _('Daily')),
        (WEEKLY, _('Weekly')),
        (MONTHLY, _('Monthly')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    name = models.CharField(
        _('Policy Name'),
        max_length=255,
        help_text=_('Name for this late fee policy')
    )

    fee_type = models.CharField(
        _('Fee Type'),
        max_length=20,
        choices=FEE_TYPE_CHOICES,
        default=PERCENTAGE
    )

    fee_amount = models.DecimalField(
        _('Fee Amount'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_('Flat amount or percentage value')
    )

    grace_period_days = models.IntegerField(
        _('Grace Period (days)'),
        default=0,
        help_text=_('Days after due date before late fees apply')
    )

    max_fee_amount = models.DecimalField(
        _('Max Fee Amount'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Maximum fee cap (for percentage fees)')
    )

    is_compound = models.BooleanField(
        _('Compound'),
        default=False,
        help_text=_('Whether to compound on previous fees')
    )

    apply_frequency = models.CharField(
        _('Apply Frequency'),
        max_length=20,
        choices=APPLY_FREQUENCY_CHOICES,
        default=ONCE
    )

    is_active = models.BooleanField(
        _('Active'),
        default=True
    )

    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Late Fee Policy')
        verbose_name_plural = _('Late Fee Policies')
        ordering = ['name']

    def __str__(self):
        if self.fee_type == self.FLAT:
            return f"{self.name} - ${self.fee_amount} flat"
        return f"{self.name} - {self.fee_amount}%"

    def calculate_fee(self, invoice_total):
        """Calculate the late fee amount for a given invoice total."""
        if self.fee_type == self.FLAT:
            fee = self.fee_amount
        else:
            fee = (invoice_total * self.fee_amount) / Decimal('100')

        if self.max_fee_amount and fee > self.max_fee_amount:
            fee = self.max_fee_amount

        return fee


class PaymentReminder(models.Model):
    """
    Scheduled payment reminders for invoices.
    """

    # Reminder type choices
    BEFORE_DUE = 'before_due'
    ON_DUE = 'on_due'
    AFTER_DUE = 'after_due'

    REMINDER_TYPE_CHOICES = [
        (BEFORE_DUE, _('Before Due Date')),
        (ON_DUE, _('On Due Date')),
        (AFTER_DUE, _('After Due Date')),
    ]

    # Status choices
    SCHEDULED = 'scheduled'
    SENT = 'sent'
    CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (SCHEDULED, _('Scheduled')),
        (SENT, _('Sent')),
        (CANCELLED, _('Cancelled')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='payment_reminders',
        help_text=_('Invoice this reminder is for')
    )

    reminder_type = models.CharField(
        _('Reminder Type'),
        max_length=20,
        choices=REMINDER_TYPE_CHOICES,
        default=BEFORE_DUE
    )

    days_offset = models.IntegerField(
        _('Days Offset'),
        default=7,
        help_text=_('Days before/after due date to send reminder')
    )

    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=SCHEDULED
    )

    scheduled_date = models.DateField(
        _('Scheduled Date'),
        help_text=_('Date the reminder is scheduled to be sent')
    )

    sent_at = models.DateTimeField(
        _('Sent At'),
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)

    class Meta:
        verbose_name = _('Payment Reminder')
        verbose_name_plural = _('Payment Reminders')
        ordering = ['scheduled_date']
        indexes = [
            models.Index(fields=['invoice', 'status']),
            models.Index(fields=['scheduled_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Reminder for {self.invoice.invoice_number} - {self.reminder_type} ({self.status})"

    @property
    def is_due(self):
        """Check if reminder is due to be sent."""
        from django.utils import timezone
        if self.status != self.SCHEDULED:
            return False
        return self.scheduled_date <= timezone.now().date()

    def mark_sent(self):
        """Mark reminder as sent."""
        from django.utils import timezone
        self.status = self.SENT
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at'])
