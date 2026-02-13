"""
Email account, message, attachment, and template models.
"""

import uuid
from string import Template

from django.db import models
from django.utils.translation import gettext_lazy as _


class EmailAccount(models.Model):
    """
    Email account configuration for sending/receiving emails.
    """

    # Provider Choices
    SMTP = 'smtp'
    GMAIL = 'gmail'
    OUTLOOK = 'outlook'
    SES = 'ses'

    PROVIDER_CHOICES = [
        (SMTP, _('SMTP')),
        (GMAIL, _('Gmail')),
        (OUTLOOK, _('Outlook')),
        (SES, _('SES')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='email_accounts',
        help_text=_('User who owns this email account')
    )

    email_address = models.EmailField(
        _('Email Address'),
        help_text=_('Email address for this account')
    )

    display_name = models.CharField(
        _('Display Name'),
        max_length=255,
        blank=True,
        help_text=_('Display name shown in sent emails')
    )

    provider = models.CharField(
        _('Provider'),
        max_length=20,
        choices=PROVIDER_CHOICES,
        default=SMTP,
        help_text=_('Email service provider')
    )

    config = models.JSONField(
        _('Configuration'),
        default=dict,
        blank=True,
        help_text=_('Provider-specific configuration (SMTP settings, API keys, etc.)')
    )

    is_active = models.BooleanField(
        _('Active'),
        default=True,
        help_text=_('Whether this email account is active')
    )

    is_default = models.BooleanField(
        _('Default'),
        default=False,
        help_text=_('Whether this is the default email account for the user')
    )

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Email Account')
        verbose_name_plural = _('Email Accounts')
        ordering = ['-is_default', '-created_at']
        unique_together = [['user', 'email_address']]

    def __str__(self):
        return f"{self.display_name} <{self.email_address}>"


class EmailMessage(models.Model):
    """
    Email message model for tracking sent and received emails.
    """

    # Direction Choices
    INBOUND = 'inbound'
    OUTBOUND = 'outbound'

    DIRECTION_CHOICES = [
        (INBOUND, _('Inbound')),
        (OUTBOUND, _('Outbound')),
    ]

    # Status Choices
    DRAFT = 'draft'
    QUEUED = 'queued'
    SENT = 'sent'
    DELIVERED = 'delivered'
    FAILED = 'failed'
    RECEIVED = 'received'

    STATUS_CHOICES = [
        (DRAFT, _('Draft')),
        (QUEUED, _('Queued')),
        (SENT, _('Sent')),
        (DELIVERED, _('Delivered')),
        (FAILED, _('Failed')),
        (RECEIVED, _('Received')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    account = models.ForeignKey(
        EmailAccount,
        on_delete=models.CASCADE,
        related_name='messages',
        help_text=_('Email account used for this message')
    )

    direction = models.CharField(
        _('Direction'),
        max_length=20,
        choices=DIRECTION_CHOICES,
        default=OUTBOUND,
        help_text=_('Whether the email is inbound or outbound')
    )

    from_email = models.EmailField(
        _('From Email'),
        help_text=_('Sender email address')
    )

    to_emails = models.JSONField(
        _('To Emails'),
        default=list,
        help_text=_('List of recipient email addresses')
    )

    cc_emails = models.JSONField(
        _('CC Emails'),
        default=list,
        blank=True,
        help_text=_('List of CC email addresses')
    )

    bcc_emails = models.JSONField(
        _('BCC Emails'),
        default=list,
        blank=True,
        help_text=_('List of BCC email addresses')
    )

    subject = models.CharField(
        _('Subject'),
        max_length=500,
        blank=True,
        help_text=_('Email subject line')
    )

    body_text = models.TextField(
        _('Body (Text)'),
        blank=True,
        help_text=_('Plain text email body')
    )

    body_html = models.TextField(
        _('Body (HTML)'),
        blank=True,
        help_text=_('HTML email body')
    )

    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=DRAFT,
        help_text=_('Current status of the email')
    )

    # Related entities
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_messages',
        help_text=_('Associated client')
    )

    contract = models.ForeignKey(
        'contracts.Contract',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_messages',
        help_text=_('Associated contract')
    )

    invoice = models.ForeignKey(
        'invoicing.Invoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_messages',
        help_text=_('Associated invoice')
    )

    # Email threading
    message_id = models.CharField(
        _('Message-ID'),
        max_length=255,
        blank=True,
        unique=True,
        null=True,
        help_text=_('Email Message-ID header')
    )

    in_reply_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies',
        help_text=_('Email this is a reply to')
    )

    thread_id = models.CharField(
        _('Thread ID'),
        max_length=255,
        blank=True,
        help_text=_('Thread identifier for grouping related emails')
    )

    # Tracking
    is_read = models.BooleanField(
        _('Read'),
        default=False,
        help_text=_('Whether the email has been read')
    )

    opened_at = models.DateTimeField(
        _('Opened At'),
        null=True,
        blank=True,
        help_text=_('When the email was first opened by the recipient')
    )

    opened_count = models.IntegerField(
        _('Opened Count'),
        default=0,
        help_text=_('Number of times the email was opened')
    )

    sent_at = models.DateTimeField(
        _('Sent At'),
        null=True,
        blank=True,
        help_text=_('When the email was sent')
    )

    received_at = models.DateTimeField(
        _('Received At'),
        null=True,
        blank=True,
        help_text=_('When the email was received')
    )

    # Metadata
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
        verbose_name = _('Email Message')
        verbose_name_plural = _('Email Messages')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['account']),
            models.Index(fields=['status']),
            models.Index(fields=['client']),
            models.Index(fields=['thread_id']),
            models.Index(fields=['direction']),
        ]

    def __str__(self):
        return f"{self.subject} - {self.status}"


class EmailAttachment(models.Model):
    """
    Attachment for an email message.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    email = models.ForeignKey(
        EmailMessage,
        on_delete=models.CASCADE,
        related_name='attachments',
        help_text=_('Email message this attachment belongs to')
    )

    file = models.FileField(
        _('File'),
        upload_to='emails/attachments/',
        help_text=_('Attached file')
    )

    file_name = models.CharField(
        _('File Name'),
        max_length=255,
        help_text=_('Original file name')
    )

    file_size = models.PositiveIntegerField(
        _('File Size'),
        null=True,
        editable=False,
        help_text=_('File size in bytes')
    )

    file_type = models.CharField(
        _('File Type'),
        max_length=100,
        blank=True,
        help_text=_('MIME type of the file')
    )

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)

    class Meta:
        verbose_name = _('Email Attachment')
        verbose_name_plural = _('Email Attachments')

    def __str__(self):
        return self.file_name

    def save(self, *args, **kwargs):
        """Set file size from file on save."""
        if self.file:
            try:
                self.file_size = self.file.size
            except Exception:
                pass
        super().save(*args, **kwargs)


class EmailTemplate(models.Model):
    """
    Reusable email template with variable substitution.
    """

    # Category Choices
    GENERAL = 'general'
    FOLLOW_UP = 'follow_up'
    INVOICE = 'invoice'
    CONTRACT = 'contract'
    REMINDER = 'reminder'
    WELCOME = 'welcome'

    CATEGORY_CHOICES = [
        (GENERAL, _('General')),
        (FOLLOW_UP, _('Follow-up')),
        (INVOICE, _('Invoice')),
        (CONTRACT, _('Contract')),
        (REMINDER, _('Reminder')),
        (WELCOME, _('Welcome')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    name = models.CharField(
        _('Template Name'),
        max_length=255,
        help_text=_('Name of the email template')
    )

    subject = models.CharField(
        _('Subject'),
        max_length=500,
        help_text=_('Email subject line template')
    )

    body_text = models.TextField(
        _('Body (Text)'),
        blank=True,
        help_text=_('Plain text email body template')
    )

    body_html = models.TextField(
        _('Body (HTML)'),
        blank=True,
        help_text=_('HTML email body template')
    )

    category = models.CharField(
        _('Category'),
        max_length=20,
        choices=CATEGORY_CHOICES,
        default=GENERAL,
        help_text=_('Template category')
    )

    available_variables = models.JSONField(
        _('Available Variables'),
        default=list,
        blank=True,
        help_text=_('List of variable names available for substitution')
    )

    is_active = models.BooleanField(
        _('Active'),
        default=True,
        help_text=_('Whether this template is active')
    )

    owner = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_templates',
        help_text=_('User who created this template')
    )

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Email Template')
        verbose_name_plural = _('Email Templates')
        ordering = ['name']

    def __str__(self):
        return self.name

    def render(self, context):
        """
        Render the template with the given context using string.Template substitution.

        Args:
            context: A dictionary of variable names to values.

        Returns:
            A dictionary with rendered 'subject', 'body_text', and 'body_html'.
        """
        rendered_subject = Template(self.subject).safe_substitute(context)
        rendered_body_text = Template(self.body_text).safe_substitute(context)
        rendered_body_html = Template(self.body_html).safe_substitute(context)

        return {
            'subject': rendered_subject,
            'body_text': rendered_body_text,
            'body_html': rendered_body_html,
        }
