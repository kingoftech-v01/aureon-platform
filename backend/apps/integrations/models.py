"""Integration models for third-party service connections."""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class Integration(models.Model):
    """Third-party integration configuration."""

    # Service Types
    QUICKBOOKS = 'quickbooks'
    XERO = 'xero'
    GOOGLE_CALENDAR = 'google_calendar'
    OUTLOOK = 'outlook'
    SLACK = 'slack'
    CUSTOM = 'custom'

    SERVICE_CHOICES = [
        (QUICKBOOKS, _('QuickBooks')),
        (XERO, _('Xero')),
        (GOOGLE_CALENDAR, _('Google Calendar')),
        (OUTLOOK, _('Microsoft Outlook')),
        (SLACK, _('Slack')),
        (CUSTOM, _('Custom Integration')),
    ]

    # Status
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    ERROR = 'error'

    STATUS_CHOICES = [
        (ACTIVE, _('Active')),
        (INACTIVE, _('Inactive')),
        (ERROR, _('Error')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(_('Name'), max_length=255, help_text=_('Display name for this integration'))

    service_type = models.CharField(_('Service Type'), max_length=30, choices=SERVICE_CHOICES)

    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES, default=INACTIVE)

    # Configuration
    config = models.JSONField(_('Configuration'), default=dict, blank=True,
        help_text=_('Service-specific configuration (API keys, endpoints, etc.)'))

    # OAuth tokens (encrypted in production)
    access_token = models.TextField(_('Access Token'), blank=True)
    refresh_token = models.TextField(_('Refresh Token'), blank=True)
    token_expires_at = models.DateTimeField(_('Token Expires At'), null=True, blank=True)

    # Sync settings
    sync_enabled = models.BooleanField(_('Sync Enabled'), default=True)
    sync_interval_minutes = models.PositiveIntegerField(_('Sync Interval (minutes)'), default=60)
    last_sync_at = models.DateTimeField(_('Last Sync'), null=True, blank=True)
    last_sync_status = models.CharField(_('Last Sync Status'), max_length=20, blank=True)
    last_sync_error = models.TextField(_('Last Sync Error'), blank=True)

    # Webhook
    webhook_url = models.URLField(_('Webhook URL'), blank=True)
    webhook_secret = models.CharField(_('Webhook Secret'), max_length=255, blank=True)

    # Metadata
    metadata = models.JSONField(_('Metadata'), default=dict, blank=True)

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        app_label = 'integrations'
        verbose_name = _('Integration')
        verbose_name_plural = _('Integrations')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_service_type_display()})"

    @property
    def is_connected(self):
        return self.status == self.ACTIVE and bool(self.access_token)

    @property
    def needs_reauth(self):
        if not self.token_expires_at:
            return False
        from django.utils import timezone
        return timezone.now() >= self.token_expires_at


class IntegrationSyncLog(models.Model):
    """Log of integration sync operations."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    integration = models.ForeignKey(
        Integration, on_delete=models.CASCADE, related_name='sync_logs'
    )

    status = models.CharField(_('Status'), max_length=20)
    records_synced = models.PositiveIntegerField(_('Records Synced'), default=0)
    errors = models.JSONField(_('Errors'), default=list, blank=True)
    duration_ms = models.PositiveIntegerField(_('Duration (ms)'), default=0)
    metadata = models.JSONField(_('Metadata'), default=dict, blank=True)

    started_at = models.DateTimeField(_('Started At'), auto_now_add=True)
    completed_at = models.DateTimeField(_('Completed At'), null=True, blank=True)

    class Meta:
        app_label = 'integrations'
        verbose_name = _('Integration Sync Log')
        verbose_name_plural = _('Integration Sync Logs')
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.integration.name} sync at {self.started_at}"
