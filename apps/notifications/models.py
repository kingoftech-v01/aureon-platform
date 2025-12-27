"""Notification models for email, SMS, and in-app notifications."""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField

User = get_user_model()


class NotificationTemplate(models.Model):
    """
    Template for automated notifications.

    Supports dynamic variables and multiple channels.
    """

    # Template Types
    INVOICE_CREATED = 'invoice_created'
    INVOICE_SENT = 'invoice_sent'
    INVOICE_PAID = 'invoice_paid'
    INVOICE_OVERDUE = 'invoice_overdue'
    PAYMENT_RECEIVED = 'payment_received'
    PAYMENT_FAILED = 'payment_failed'
    PAYMENT_RECEIPT = 'payment_receipt'
    CONTRACT_SIGNED = 'contract_signed'
    CONTRACT_EXPIRING = 'contract_expiring'
    CLIENT_WELCOME = 'client_welcome'
    REMINDER_PAYMENT_DUE = 'reminder_payment_due'

    TEMPLATE_TYPE_CHOICES = [
        (INVOICE_CREATED, _('Invoice Created')),
        (INVOICE_SENT, _('Invoice Sent to Client')),
        (INVOICE_PAID, _('Invoice Paid')),
        (INVOICE_OVERDUE, _('Invoice Overdue')),
        (PAYMENT_RECEIVED, _('Payment Received')),
        (PAYMENT_FAILED, _('Payment Failed')),
        (PAYMENT_RECEIPT, _('Payment Receipt')),
        (CONTRACT_SIGNED, _('Contract Signed')),
        (CONTRACT_EXPIRING, _('Contract Expiring Soon')),
        (CLIENT_WELCOME, _('New Client Welcome')),
        (REMINDER_PAYMENT_DUE, _('Payment Due Reminder')),
    ]

    # Channels
    EMAIL = 'email'
    SMS = 'sms'
    IN_APP = 'in_app'

    CHANNEL_CHOICES = [
        (EMAIL, _('Email')),
        (SMS, _('SMS')),
        (IN_APP, _('In-App Notification')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Template Information
    name = models.CharField(
        _('Template Name'),
        max_length=255,
        help_text=_('Descriptive name for this template')
    )

    template_type = models.CharField(
        _('Template Type'),
        max_length=50,
        choices=TEMPLATE_TYPE_CHOICES,
        unique=True,
        help_text=_('Type of notification this template is for')
    )

    channel = models.CharField(
        _('Channel'),
        max_length=20,
        choices=CHANNEL_CHOICES,
        default=EMAIL
    )

    # Email-specific fields
    subject = models.CharField(
        _('Email Subject'),
        max_length=255,
        blank=True,
        help_text=_('Subject line for email notifications. Supports {{variables}}')
    )

    body_text = models.TextField(
        _('Plain Text Body'),
        help_text=_('Plain text version of the message. Supports {{variables}}')
    )

    body_html = models.TextField(
        _('HTML Body'),
        blank=True,
        help_text=_('HTML version of the message. Supports {{variables}}')
    )

    # Configuration
    is_active = models.BooleanField(
        _('Active'),
        default=True,
        help_text=_('Whether this template is currently active')
    )

    send_to_client = models.BooleanField(
        _('Send to Client'),
        default=True,
        help_text=_('Send this notification to the client')
    )

    send_to_owner = models.BooleanField(
        _('Send to Owner'),
        default=False,
        help_text=_('Send this notification to the contract/invoice owner')
    )

    # Metadata
    available_variables = ArrayField(
        models.CharField(max_length=100),
        verbose_name=_('Available Variables'),
        default=list,
        blank=True,
        help_text=_('List of available template variables')
    )

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Notification Template')
        verbose_name_plural = _('Notification Templates')
        ordering = ['template_type']

    def __str__(self):
        return f"{self.name} ({self.get_channel_display()})"

    def render(self, context):
        """
        Render template with provided context variables.

        Args:
            context: Dict of template variables

        Returns:
            dict: Rendered template with subject, body_text, body_html
        """
        import re

        def replace_vars(text):
            """Replace {{variable}} placeholders with context values."""
            if not text:
                return text

            def replacer(match):
                var_name = match.group(1)
                return str(context.get(var_name, f'{{{{{var_name}}}}}'))

            return re.sub(r'\{\{(\w+)\}\}', replacer, text)

        return {
            'subject': replace_vars(self.subject),
            'body_text': replace_vars(self.body_text),
            'body_html': replace_vars(self.body_html) if self.body_html else None,
        }


class Notification(models.Model):
    """
    Individual notification sent to a user.

    Tracks delivery status and user interactions.
    """

    # Status
    PENDING = 'pending'
    SENT = 'sent'
    DELIVERED = 'delivered'
    FAILED = 'failed'
    READ = 'read'

    STATUS_CHOICES = [
        (PENDING, _('Pending')),
        (SENT, _('Sent')),
        (DELIVERED, _('Delivered')),
        (FAILED, _('Failed')),
        (READ, _('Read')),
    ]

    # Priority
    LOW = 'low'
    NORMAL = 'normal'
    HIGH = 'high'
    URGENT = 'urgent'

    PRIORITY_CHOICES = [
        (LOW, _('Low')),
        (NORMAL, _('Normal')),
        (HIGH, _('High')),
        (URGENT, _('Urgent')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Recipient
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True,
        help_text=_('User receiving this notification (if logged in)')
    )

    email = models.EmailField(
        _('Email Address'),
        blank=True,
        help_text=_('Email address for notification (if not to a user)')
    )

    phone = models.CharField(
        _('Phone Number'),
        max_length=20,
        blank=True,
        help_text=_('Phone number for SMS notifications')
    )

    # Template Reference
    template = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.SET_NULL,
        related_name='notifications',
        null=True,
        blank=True,
        help_text=_('Template used for this notification')
    )

    # Content
    subject = models.CharField(
        _('Subject'),
        max_length=255,
        blank=True
    )

    message_text = models.TextField(
        _('Message (Plain Text)'),
        help_text=_('Plain text message content')
    )

    message_html = models.TextField(
        _('Message (HTML)'),
        blank=True,
        help_text=_('HTML message content')
    )

    # Metadata
    channel = models.CharField(
        _('Channel'),
        max_length=20,
        choices=NotificationTemplate.CHANNEL_CHOICES,
        default=NotificationTemplate.EMAIL
    )

    priority = models.CharField(
        _('Priority'),
        max_length=20,
        choices=PRIORITY_CHOICES,
        default=NORMAL
    )

    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING
    )

    # Delivery Information
    sent_at = models.DateTimeField(
        _('Sent At'),
        null=True,
        blank=True
    )

    delivered_at = models.DateTimeField(
        _('Delivered At'),
        null=True,
        blank=True
    )

    read_at = models.DateTimeField(
        _('Read At'),
        null=True,
        blank=True
    )

    failed_at = models.DateTimeField(
        _('Failed At'),
        null=True,
        blank=True
    )

    error_message = models.TextField(
        _('Error Message'),
        blank=True,
        help_text=_('Error message if delivery failed')
    )

    # External References
    external_id = models.CharField(
        _('External ID'),
        max_length=255,
        blank=True,
        help_text=_('ID from email/SMS provider')
    )

    # Related Objects
    related_invoice = models.ForeignKey(
        'invoicing.Invoice',
        on_delete=models.SET_NULL,
        related_name='notifications',
        null=True,
        blank=True
    )

    related_payment = models.ForeignKey(
        'payments.Payment',
        on_delete=models.SET_NULL,
        related_name='notifications',
        null=True,
        blank=True
    )

    related_contract = models.ForeignKey(
        'contracts.Contract',
        on_delete=models.SET_NULL,
        related_name='notifications',
        null=True,
        blank=True
    )

    # Tracking
    retry_count = models.PositiveIntegerField(
        _('Retry Count'),
        default=0
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
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['email', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        recipient = self.user.email if self.user else self.email
        return f"{self.get_channel_display()} to {recipient}: {self.subject}"

    def mark_as_sent(self, external_id=None):
        """Mark notification as sent."""
        from django.utils import timezone
        self.status = self.SENT
        self.sent_at = timezone.now()
        if external_id:
            self.external_id = external_id
        self.save(update_fields=['status', 'sent_at', 'external_id', 'updated_at'])

    def mark_as_delivered(self):
        """Mark notification as delivered."""
        from django.utils import timezone
        self.status = self.DELIVERED
        self.delivered_at = timezone.now()
        self.save(update_fields=['status', 'delivered_at', 'updated_at'])

    def mark_as_read(self):
        """Mark notification as read."""
        from django.utils import timezone
        self.status = self.READ
        self.read_at = timezone.now()
        self.save(update_fields=['status', 'read_at', 'updated_at'])

    def mark_as_failed(self, error_message):
        """Mark notification as failed."""
        from django.utils import timezone
        self.status = self.FAILED
        self.failed_at = timezone.now()
        self.error_message = str(error_message)
        self.retry_count += 1
        self.save(update_fields=['status', 'failed_at', 'error_message', 'retry_count', 'updated_at'])

    @property
    def is_read(self):
        """Check if notification has been read."""
        return self.status == self.READ

    @property
    def recipient(self):
        """Get recipient string."""
        if self.user:
            return self.user.email
        return self.email or self.phone
