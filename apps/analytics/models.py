"""Analytics models for tracking metrics and KPIs."""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class RevenueMetric(models.Model):
    """
    Monthly revenue metrics and KPIs.

    Aggregates financial data per month for analytics.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Time Period
    year = models.PositiveIntegerField(
        _('Year'),
        help_text=_('Year for this metric period')
    )

    month = models.PositiveIntegerField(
        _('Month'),
        help_text=_('Month (1-12) for this metric period')
    )

    # Revenue Metrics
    total_revenue = models.DecimalField(
        _('Total Revenue'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_('Total revenue for the period')
    )

    recurring_revenue = models.DecimalField(
        _('Recurring Revenue (MRR)'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_('Monthly Recurring Revenue')
    )

    one_time_revenue = models.DecimalField(
        _('One-Time Revenue'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_('Non-recurring revenue for the period')
    )

    # Invoice Metrics
    invoices_sent = models.PositiveIntegerField(
        _('Invoices Sent'),
        default=0
    )

    invoices_paid = models.PositiveIntegerField(
        _('Invoices Paid'),
        default=0
    )

    invoices_overdue = models.PositiveIntegerField(
        _('Invoices Overdue'),
        default=0
    )

    average_invoice_value = models.DecimalField(
        _('Average Invoice Value'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    # Payment Metrics
    payments_received = models.PositiveIntegerField(
        _('Payments Received'),
        default=0
    )

    payments_failed = models.PositiveIntegerField(
        _('Payments Failed'),
        default=0
    )

    refunds_issued = models.PositiveIntegerField(
        _('Refunds Issued'),
        default=0
    )

    refund_amount = models.DecimalField(
        _('Refund Amount'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    # Client Metrics
    new_clients = models.PositiveIntegerField(
        _('New Clients'),
        default=0,
        help_text=_('New clients added this period')
    )

    churned_clients = models.PositiveIntegerField(
        _('Churned Clients'),
        default=0,
        help_text=_('Clients lost this period')
    )

    active_clients = models.PositiveIntegerField(
        _('Active Clients'),
        default=0,
        help_text=_('Total active clients at end of period')
    )

    # Contract Metrics
    contracts_signed = models.PositiveIntegerField(
        _('Contracts Signed'),
        default=0
    )

    contracts_completed = models.PositiveIntegerField(
        _('Contracts Completed'),
        default=0
    )

    active_contracts = models.PositiveIntegerField(
        _('Active Contracts'),
        default=0
    )

    total_contract_value = models.DecimalField(
        _('Total Contract Value'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    # Calculated Metrics
    payment_success_rate = models.DecimalField(
        _('Payment Success Rate'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_('Percentage of successful payments')
    )

    churn_rate = models.DecimalField(
        _('Churn Rate'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_('Client churn rate percentage')
    )

    # Timestamps
    calculated_at = models.DateTimeField(
        _('Calculated At'),
        auto_now=True,
        help_text=_('When these metrics were last calculated')
    )

    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)

    class Meta:
        verbose_name = _('Revenue Metric')
        verbose_name_plural = _('Revenue Metrics')
        ordering = ['-year', '-month']
        unique_together = [['year', 'month']]
        indexes = [
            models.Index(fields=['-year', '-month']),
        ]

    def __str__(self):
        return f"{self.year}-{self.month:02d}: ${self.total_revenue}"

    @property
    def period_name(self):
        """Get period name (e.g., 'January 2025')."""
        from datetime import date
        return date(self.year, self.month, 1).strftime('%B %Y')


class ClientMetric(models.Model):
    """
    Per-client analytics and metrics.

    Tracks financial performance per client.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    client = models.OneToOneField(
        'clients.Client',
        on_delete=models.CASCADE,
        related_name='metrics'
    )

    # Lifetime Value Metrics
    lifetime_value = models.DecimalField(
        _('Lifetime Value'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_('Total revenue from this client')
    )

    average_invoice_value = models.DecimalField(
        _('Average Invoice Value'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    # Invoice Metrics
    total_invoices = models.PositiveIntegerField(
        _('Total Invoices'),
        default=0
    )

    paid_invoices = models.PositiveIntegerField(
        _('Paid Invoices'),
        default=0
    )

    overdue_invoices = models.PositiveIntegerField(
        _('Overdue Invoices'),
        default=0
    )

    outstanding_balance = models.DecimalField(
        _('Outstanding Balance'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    # Payment Metrics
    total_payments = models.PositiveIntegerField(
        _('Total Payments'),
        default=0
    )

    failed_payments = models.PositiveIntegerField(
        _('Failed Payments'),
        default=0
    )

    # Contract Metrics
    total_contracts = models.PositiveIntegerField(
        _('Total Contracts'),
        default=0
    )

    active_contracts = models.PositiveIntegerField(
        _('Active Contracts'),
        default=0
    )

    # Engagement Metrics
    last_invoice_date = models.DateField(
        _('Last Invoice Date'),
        null=True,
        blank=True
    )

    last_payment_date = models.DateField(
        _('Last Payment Date'),
        null=True,
        blank=True
    )

    days_since_last_payment = models.PositiveIntegerField(
        _('Days Since Last Payment'),
        default=0
    )

    # Calculated Scores
    payment_reliability_score = models.DecimalField(
        _('Payment Reliability Score'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_('Score 0-100 based on payment history')
    )

    # Timestamps
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)

    class Meta:
        verbose_name = _('Client Metric')
        verbose_name_plural = _('Client Metrics')
        ordering = ['-lifetime_value']

    def __str__(self):
        return f"Metrics for {self.client.full_name}"


class ActivityLog(models.Model):
    """
    Activity log for tracking user and system actions.

    Creates an audit trail of important events.
    """

    # Activity Types
    INVOICE_CREATED = 'invoice_created'
    INVOICE_SENT = 'invoice_sent'
    INVOICE_PAID = 'invoice_paid'
    PAYMENT_RECEIVED = 'payment_received'
    PAYMENT_FAILED = 'payment_failed'
    CONTRACT_SIGNED = 'contract_signed'
    CONTRACT_COMPLETED = 'contract_completed'
    CLIENT_CREATED = 'client_created'
    CLIENT_UPDATED = 'client_updated'
    USER_LOGIN = 'user_login'
    USER_LOGOUT = 'user_logout'

    ACTIVITY_TYPE_CHOICES = [
        (INVOICE_CREATED, _('Invoice Created')),
        (INVOICE_SENT, _('Invoice Sent')),
        (INVOICE_PAID, _('Invoice Paid')),
        (PAYMENT_RECEIVED, _('Payment Received')),
        (PAYMENT_FAILED, _('Payment Failed')),
        (CONTRACT_SIGNED, _('Contract Signed')),
        (CONTRACT_COMPLETED, _('Contract Completed')),
        (CLIENT_CREATED, _('Client Created')),
        (CLIENT_UPDATED, _('Client Updated')),
        (USER_LOGIN, _('User Login')),
        (USER_LOGOUT, _('User Logout')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Activity Information
    activity_type = models.CharField(
        _('Activity Type'),
        max_length=50,
        choices=ACTIVITY_TYPE_CHOICES
    )

    description = models.CharField(
        _('Description'),
        max_length=500,
        help_text=_('Human-readable description of the activity')
    )

    # Actor
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        related_name='activities',
        null=True,
        blank=True,
        help_text=_('User who performed this activity')
    )

    # Related Objects (using JSONField for flexibility)
    related_objects = models.JSONField(
        _('Related Objects'),
        default=dict,
        blank=True,
        help_text=_('IDs and types of related objects')
    )

    # Metadata
    metadata = models.JSONField(
        _('Metadata'),
        default=dict,
        blank=True,
        help_text=_('Additional activity data')
    )

    ip_address = models.GenericIPAddressField(
        _('IP Address'),
        null=True,
        blank=True
    )

    user_agent = models.CharField(
        _('User Agent'),
        max_length=500,
        blank=True
    )

    # Timestamp
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)

    class Meta:
        verbose_name = _('Activity Log')
        verbose_name_plural = _('Activity Logs')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['activity_type', '-created_at']),
        ]

    def __str__(self):
        actor = self.user.email if self.user else 'System'
        return f"{actor}: {self.description}"
