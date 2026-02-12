"""
Payment and transaction models.
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal


class Payment(models.Model):
    """
    Payment model for tracking payments and transactions.
    """

    # Payment Status
    PENDING = 'pending'
    PROCESSING = 'processing'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    REFUNDED = 'refunded'

    STATUS_CHOICES = [
        (PENDING, _('Pending')),
        (PROCESSING, _('Processing')),
        (SUCCEEDED, _('Succeeded')),
        (FAILED, _('Failed')),
        (CANCELLED, _('Cancelled')),
        (REFUNDED, _('Refunded')),
    ]

    # Payment Method
    CARD = 'card'
    BANK_TRANSFER = 'bank_transfer'
    CASH = 'cash'
    CHECK = 'check'
    OTHER = 'other'

    METHOD_CHOICES = [
        (CARD, _('Credit/Debit Card')),
        (BANK_TRANSFER, _('Bank Transfer')),
        (CASH, _('Cash')),
        (CHECK, _('Check')),
        (OTHER, _('Other')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Invoice Relationship
    invoice = models.ForeignKey(
        'invoicing.Invoice',
        on_delete=models.CASCADE,
        related_name='payments',
        null=True,
        blank=True,
        help_text=_('Invoice this payment is for')
    )

    # Payment Details
    amount = models.DecimalField(
        _('Amount'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_('Payment amount')
    )

    currency = models.CharField(
        _('Currency'),
        max_length=3,
        default='USD',
        help_text=_('Currency code (e.g., USD, EUR, GBP)')
    )

    payment_method = models.CharField(
        _('Payment Method'),
        max_length=20,
        choices=METHOD_CHOICES,
        default=CARD
    )

    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING
    )

    # Transaction Information
    transaction_id = models.CharField(
        _('Transaction ID'),
        max_length=255,
        unique=True,
        help_text=_('Unique transaction identifier')
    )

    payment_date = models.DateTimeField(
        _('Payment Date'),
        help_text=_('When the payment was made')
    )

    # Stripe Integration
    stripe_payment_intent_id = models.CharField(
        _('Stripe Payment Intent ID'),
        max_length=255,
        blank=True,
        unique=True,
        null=True,
        help_text=_('Stripe payment intent ID')
    )

    stripe_charge_id = models.CharField(
        _('Stripe Charge ID'),
        max_length=255,
        blank=True,
        help_text=_('Stripe charge ID')
    )

    stripe_customer_id = models.CharField(
        _('Stripe Customer ID'),
        max_length=255,
        blank=True,
        help_text=_('Stripe customer ID')
    )

    # Card Details (last 4 digits only for security)
    card_last4 = models.CharField(
        _('Card Last 4 Digits'),
        max_length=4,
        blank=True,
        help_text=_('Last 4 digits of card number')
    )

    card_brand = models.CharField(
        _('Card Brand'),
        max_length=20,
        blank=True,
        help_text=_('Card brand (Visa, Mastercard, etc.)')
    )

    # Refund Information
    refunded_amount = models.DecimalField(
        _('Refunded Amount'),
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_('Amount refunded')
    )

    refund_reason = models.TextField(
        _('Refund Reason'),
        blank=True,
        help_text=_('Reason for refund')
    )

    refunded_at = models.DateTimeField(
        _('Refunded At'),
        null=True,
        blank=True,
        help_text=_('When the payment was refunded')
    )

    # Failure Information
    failure_code = models.CharField(
        _('Failure Code'),
        max_length=50,
        blank=True,
        help_text=_('Error code if payment failed')
    )

    failure_message = models.TextField(
        _('Failure Message'),
        blank=True,
        help_text=_('Error message if payment failed')
    )

    # Notes
    notes = models.TextField(
        _('Notes'),
        blank=True,
        help_text=_('Additional notes about the payment')
    )

    # Receipt
    receipt_url = models.URLField(
        _('Receipt URL'),
        blank=True,
        help_text=_('URL to payment receipt')
    )

    receipt_sent = models.BooleanField(
        _('Receipt Sent'),
        default=False,
        help_text=_('Whether receipt was sent to client')
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
        verbose_name = _('Payment')
        verbose_name_plural = _('Payments')
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['invoice']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_method']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['stripe_payment_intent_id']),
            models.Index(fields=['payment_date']),
        ]

    def __str__(self):
        return f"Payment {self.transaction_id} - {self.amount} {self.currency}"

    def save(self, *args, **kwargs):
        """Generate transaction ID if not set."""
        if not self.transaction_id:
            # Generate unique transaction ID
            import hashlib
            from django.utils import timezone

            invoice_id = self.invoice_id or "no-invoice"
            hash_input = f"{invoice_id}-{timezone.now().isoformat()}"
            hash_digest = hashlib.sha256(hash_input.encode()).hexdigest()[:12]
            self.transaction_id = f"TXN-{hash_digest.upper()}"

        super().save(*args, **kwargs)

    @property
    def is_successful(self):
        """Check if payment was successful."""
        return self.status == self.SUCCEEDED

    @property
    def net_amount(self):
        """Calculate net amount after refunds."""
        return self.amount - self.refunded_amount

    def process_refund(self, refund_amount, reason=None):
        """
        Process a refund for this payment.

        Args:
            refund_amount: Amount to refund
            reason: Reason for the refund
        """
        from django.utils import timezone

        if self.status != self.SUCCEEDED:
            raise ValueError("Only successful payments can be refunded")

        if refund_amount > (self.amount - self.refunded_amount):
            raise ValueError("Refund amount exceeds available amount")

        self.refunded_amount += refund_amount

        if self.refunded_amount >= self.amount:
            self.status = self.REFUNDED
            self.refunded_at = timezone.now()

        if reason:
            self.refund_reason = reason

        self.save()

        # Update invoice paid amount
        self.invoice.paid_amount -= refund_amount
        self.invoice.save()


class PaymentMethod(models.Model):
    """
    Saved payment methods for clients.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Client Relationship
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE,
        related_name='payment_methods',
        help_text=_('Client who owns this payment method')
    )

    # Payment Method Details
    type = models.CharField(
        _('Type'),
        max_length=20,
        choices=Payment.METHOD_CHOICES,
        default=Payment.CARD
    )

    is_default = models.BooleanField(
        _('Is Default'),
        default=False,
        help_text=_('Whether this is the default payment method')
    )

    # Card Details (for card payments)
    card_last4 = models.CharField(
        _('Card Last 4 Digits'),
        max_length=4,
        blank=True
    )

    card_brand = models.CharField(
        _('Card Brand'),
        max_length=20,
        blank=True
    )

    card_exp_month = models.IntegerField(
        _('Card Expiration Month'),
        null=True,
        blank=True
    )

    card_exp_year = models.IntegerField(
        _('Card Expiration Year'),
        null=True,
        blank=True
    )

    # Stripe Integration
    stripe_payment_method_id = models.CharField(
        _('Stripe Payment Method ID'),
        max_length=255,
        unique=True,
        help_text=_('Stripe payment method ID')
    )

    # Status
    is_active = models.BooleanField(
        _('Active'),
        default=True,
        help_text=_('Whether this payment method is active')
    )

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Payment Method')
        verbose_name_plural = _('Payment Methods')
        ordering = ['-is_default', '-created_at']
        indexes = [
            models.Index(fields=['client', 'is_default']),
            models.Index(fields=['stripe_payment_method_id']),
        ]

    def __str__(self):
        if self.type == Payment.CARD:
            return f"{self.card_brand} •••• {self.card_last4}"
        return f"{self.get_type_display()}"

    def save(self, *args, **kwargs):
        """Ensure only one default payment method per client."""
        if self.is_default:
            # Set all other payment methods for this client as non-default
            PaymentMethod.objects.filter(
                client=self.client,
                is_default=True
            ).exclude(id=self.id).update(is_default=False)

        super().save(*args, **kwargs)
