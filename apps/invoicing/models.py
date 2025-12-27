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
        # TODO: Implement PDF generation with ReportLab or WeasyPrint
        pass


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
