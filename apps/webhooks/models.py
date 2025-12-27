"""Webhook models for tracking incoming webhook events."""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.fields import ArrayField


class WebhookEvent(models.Model):
    """
    Model for tracking all incoming webhook events.

    Stores webhook data for audit trails and debugging.
    """

    # Event Sources
    STRIPE = 'stripe'
    CUSTOM = 'custom'

    SOURCE_CHOICES = [
        (STRIPE, _('Stripe')),
        (CUSTOM, _('Custom Webhook')),
    ]

    # Event Statuses
    PENDING = 'pending'
    PROCESSING = 'processing'
    PROCESSED = 'processed'
    FAILED = 'failed'
    RETRYING = 'retrying'

    STATUS_CHOICES = [
        (PENDING, _('Pending')),
        (PROCESSING, _('Processing')),
        (PROCESSED, _('Processed Successfully')),
        (FAILED, _('Failed')),
        (RETRYING, _('Retrying')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Source Information
    source = models.CharField(
        _('Webhook Source'),
        max_length=50,
        choices=SOURCE_CHOICES,
        default=CUSTOM
    )

    event_type = models.CharField(
        _('Event Type'),
        max_length=255,
        help_text=_('Type of webhook event (e.g., payment_intent.succeeded)')
    )

    event_id = models.CharField(
        _('External Event ID'),
        max_length=255,
        unique=True,
        help_text=_('Unique identifier from the webhook source')
    )

    # Status Tracking
    status = models.CharField(
        _('Processing Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING
    )

    # Payload Data
    payload = models.JSONField(
        _('Event Payload'),
        help_text=_('Full webhook payload data')
    )

    headers = models.JSONField(
        _('Request Headers'),
        default=dict,
        blank=True,
        help_text=_('HTTP headers from the webhook request')
    )

    # Processing Information
    processed_at = models.DateTimeField(
        _('Processed At'),
        null=True,
        blank=True,
        help_text=_('When the webhook was successfully processed')
    )

    error_message = models.TextField(
        _('Error Message'),
        blank=True,
        help_text=_('Error message if processing failed')
    )

    retry_count = models.PositiveIntegerField(
        _('Retry Count'),
        default=0,
        help_text=_('Number of processing retry attempts')
    )

    max_retries = models.PositiveIntegerField(
        _('Max Retries'),
        default=3,
        help_text=_('Maximum number of retry attempts')
    )

    # Response Information
    response_code = models.PositiveIntegerField(
        _('Response Code'),
        null=True,
        blank=True,
        help_text=_('HTTP response code sent back')
    )

    response_body = models.JSONField(
        _('Response Body'),
        null=True,
        blank=True,
        help_text=_('Response data sent back to webhook source')
    )

    # Metadata
    ip_address = models.GenericIPAddressField(
        _('IP Address'),
        null=True,
        blank=True,
        help_text=_('IP address of the webhook sender')
    )

    user_agent = models.CharField(
        _('User Agent'),
        max_length=500,
        blank=True,
        help_text=_('User agent of the webhook request')
    )

    # Timestamps
    received_at = models.DateTimeField(
        _('Received At'),
        auto_now_add=True,
        help_text=_('When the webhook was received')
    )

    updated_at = models.DateTimeField(
        _('Updated At'),
        auto_now=True
    )

    class Meta:
        verbose_name = _('Webhook Event')
        verbose_name_plural = _('Webhook Events')
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['event_id']),
            models.Index(fields=['source', 'event_type']),
            models.Index(fields=['status']),
            models.Index(fields=['-received_at']),
        ]

    def __str__(self):
        return f"{self.source} - {self.event_type} ({self.status})"

    def mark_as_processing(self):
        """Mark webhook as currently being processed."""
        self.status = self.PROCESSING
        self.save(update_fields=['status', 'updated_at'])

    def mark_as_processed(self, response_data=None):
        """Mark webhook as successfully processed."""
        from django.utils import timezone
        self.status = self.PROCESSED
        self.processed_at = timezone.now()
        self.response_code = 200
        if response_data:
            self.response_body = response_data
        self.save(update_fields=['status', 'processed_at', 'response_code', 'response_body', 'updated_at'])

    def mark_as_failed(self, error_message, should_retry=True):
        """Mark webhook as failed and optionally queue for retry."""
        self.status = self.RETRYING if (should_retry and self.retry_count < self.max_retries) else self.FAILED
        self.error_message = str(error_message)
        self.retry_count += 1
        self.response_code = 500
        self.save(update_fields=['status', 'error_message', 'retry_count', 'response_code', 'updated_at'])

    @property
    def can_retry(self):
        """Check if webhook can be retried."""
        return self.retry_count < self.max_retries and self.status in [self.FAILED, self.RETRYING]

    @property
    def is_stripe_event(self):
        """Check if this is a Stripe webhook."""
        return self.source == self.STRIPE


class WebhookEndpoint(models.Model):
    """
    Model for managing outgoing webhook endpoints.

    Allows users to configure webhooks to external systems.
    """

    # Event Types
    EVENT_TYPES = [
        ('invoice.created', _('Invoice Created')),
        ('invoice.paid', _('Invoice Paid')),
        ('invoice.overdue', _('Invoice Overdue')),
        ('payment.succeeded', _('Payment Succeeded')),
        ('payment.failed', _('Payment Failed')),
        ('contract.signed', _('Contract Signed')),
        ('contract.completed', _('Contract Completed')),
        ('client.created', _('Client Created')),
        ('client.updated', _('Client Updated')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Endpoint Configuration
    url = models.URLField(
        _('Webhook URL'),
        max_length=500,
        help_text=_('URL where webhook POST requests will be sent')
    )

    secret_key = models.CharField(
        _('Secret Key'),
        max_length=255,
        help_text=_('Secret key for HMAC signature verification')
    )

    # Event Subscriptions
    event_types = ArrayField(
        models.CharField(max_length=50),
        verbose_name=_('Subscribed Event Types'),
        help_text=_('List of event types this endpoint subscribes to')
    )

    # Status
    is_active = models.BooleanField(
        _('Active'),
        default=True,
        help_text=_('Whether this webhook endpoint is active')
    )

    # HTTP Configuration
    headers = models.JSONField(
        _('Custom Headers'),
        default=dict,
        blank=True,
        help_text=_('Custom HTTP headers to include in requests')
    )

    timeout = models.PositiveIntegerField(
        _('Timeout (seconds)'),
        default=30,
        help_text=_('Request timeout in seconds')
    )

    # Retry Configuration
    max_retries = models.PositiveIntegerField(
        _('Max Retries'),
        default=3,
        help_text=_('Maximum number of retry attempts for failed deliveries')
    )

    retry_delay = models.PositiveIntegerField(
        _('Retry Delay (seconds)'),
        default=60,
        help_text=_('Delay between retry attempts in seconds')
    )

    # Statistics
    total_deliveries = models.PositiveIntegerField(
        _('Total Deliveries'),
        default=0,
        help_text=_('Total number of webhook deliveries attempted')
    )

    successful_deliveries = models.PositiveIntegerField(
        _('Successful Deliveries'),
        default=0,
        help_text=_('Number of successful deliveries')
    )

    failed_deliveries = models.PositiveIntegerField(
        _('Failed Deliveries'),
        default=0,
        help_text=_('Number of failed deliveries')
    )

    last_delivery_at = models.DateTimeField(
        _('Last Delivery At'),
        null=True,
        blank=True,
        help_text=_('Timestamp of last delivery attempt')
    )

    last_success_at = models.DateTimeField(
        _('Last Success At'),
        null=True,
        blank=True,
        help_text=_('Timestamp of last successful delivery')
    )

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Webhook Endpoint')
        verbose_name_plural = _('Webhook Endpoints')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.url} ({len(self.event_types)} events)"

    def record_delivery(self, success=True):
        """Record a webhook delivery attempt."""
        from django.utils import timezone
        self.total_deliveries += 1
        self.last_delivery_at = timezone.now()

        if success:
            self.successful_deliveries += 1
            self.last_success_at = timezone.now()
        else:
            self.failed_deliveries += 1

        self.save(update_fields=[
            'total_deliveries',
            'successful_deliveries',
            'failed_deliveries',
            'last_delivery_at',
            'last_success_at',
            'updated_at'
        ])

    @property
    def success_rate(self):
        """Calculate webhook success rate."""
        if self.total_deliveries == 0:
            return 0
        return (self.successful_deliveries / self.total_deliveries) * 100
