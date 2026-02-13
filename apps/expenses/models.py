"""
Expense tracking and categorization models.
"""

import uuid
from decimal import Decimal
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator


class ExpenseCategory(models.Model):
    """
    Category for organizing expenses.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    name = models.CharField(
        _('Name'),
        max_length=100,
        help_text=_('Category name')
    )

    description = models.TextField(
        _('Description'),
        blank=True,
        help_text=_('Category description')
    )

    color = models.CharField(
        _('Color'),
        max_length=7,
        blank=True,
        help_text=_('Hex color code (e.g., #FF5733)')
    )

    is_active = models.BooleanField(
        _('Active'),
        default=True,
        help_text=_('Whether this category is currently active')
    )

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Expense Category')
        verbose_name_plural = _('Expense Categories')
        ordering = ['name']

    def __str__(self):
        return self.name


class Expense(models.Model):
    """
    Expense model for tracking business expenses.
    """

    # Payment Methods
    CARD = 'card'
    CASH = 'cash'
    BANK_TRANSFER = 'bank_transfer'
    OTHER = 'other'

    PAYMENT_METHOD_CHOICES = [
        (CARD, _('Card')),
        (CASH, _('Cash')),
        (BANK_TRANSFER, _('Bank Transfer')),
        (OTHER, _('Other')),
    ]

    # Expense Status
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    INVOICED = 'invoiced'

    STATUS_CHOICES = [
        (PENDING, _('Pending')),
        (APPROVED, _('Approved')),
        (REJECTED, _('Rejected')),
        (INVOICED, _('Invoiced')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    description = models.CharField(
        _('Description'),
        max_length=500,
        help_text=_('Brief description of the expense')
    )

    amount = models.DecimalField(
        _('Amount'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_('Expense amount')
    )

    currency = models.CharField(
        _('Currency'),
        max_length=3,
        default='USD',
        help_text=_('Currency code (e.g., USD, EUR, GBP)')
    )

    category = models.ForeignKey(
        'expenses.ExpenseCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='expenses',
        help_text=_('Expense category')
    )

    expense_date = models.DateField(
        _('Expense Date'),
        help_text=_('Date the expense was incurred')
    )

    # Relationships
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='expenses',
        help_text=_('Associated client (if applicable)')
    )

    contract = models.ForeignKey(
        'contracts.Contract',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='expenses',
        help_text=_('Associated contract (if applicable)')
    )

    invoice = models.ForeignKey(
        'invoicing.Invoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='expenses',
        help_text=_('Associated invoice (if invoiced)')
    )

    # Billing
    is_billable = models.BooleanField(
        _('Billable'),
        default=False,
        help_text=_('Whether this expense is billable to a client')
    )

    is_invoiced = models.BooleanField(
        _('Invoiced'),
        default=False,
        help_text=_('Whether this expense has been invoiced')
    )

    # Receipt
    receipt_file = models.FileField(
        _('Receipt File'),
        upload_to='expenses/receipts/',
        null=True,
        blank=True,
        help_text=_('Uploaded receipt file')
    )

    receipt_number = models.CharField(
        _('Receipt Number'),
        max_length=100,
        blank=True,
        help_text=_('Receipt or reference number')
    )

    # Vendor
    vendor = models.CharField(
        _('Vendor'),
        max_length=255,
        blank=True,
        help_text=_('Vendor or merchant name')
    )

    # Payment Method
    payment_method = models.CharField(
        _('Payment Method'),
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default=CARD,
        help_text=_('Method of payment used')
    )

    # Status
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING,
        help_text=_('Current expense status')
    )

    # User Tracking
    submitted_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='submitted_expenses',
        help_text=_('User who submitted the expense')
    )

    approved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_expenses',
        help_text=_('User who approved the expense')
    )

    approved_at = models.DateTimeField(
        _('Approved At'),
        null=True,
        blank=True,
        help_text=_('When the expense was approved')
    )

    # Notes
    notes = models.TextField(
        _('Notes'),
        blank=True,
        help_text=_('Additional notes about the expense')
    )

    # Tags and Metadata
    tags = models.JSONField(
        _('Tags'),
        default=list,
        blank=True,
        help_text=_('Tags for categorization')
    )

    metadata = models.JSONField(
        _('Metadata'),
        default=dict,
        blank=True,
        help_text=_('Additional metadata in JSON format')
    )

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Expense')
        verbose_name_plural = _('Expenses')
        ordering = ['-expense_date']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['client']),
            models.Index(fields=['status']),
            models.Index(fields=['submitted_by']),
            models.Index(fields=['expense_date']),
        ]

    def __str__(self):
        return f"{self.description} - {self.amount} {self.currency}"

    @property
    def is_pending(self):
        """Check if expense is pending approval."""
        return self.status == self.PENDING
