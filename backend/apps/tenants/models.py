"""
Tenant models for multi-tenancy support.
"""

import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Tenant(models.Model):
    """
    Tenant model representing an organization on the platform.

    Each tenant has its own set of clients, contracts, invoices, etc.
    Matches the frontend Tenant interface.
    """

    # Plan choices
    FREE = 'free'
    STARTER = 'starter'
    PROFESSIONAL = 'professional'
    ENTERPRISE = 'enterprise'

    PLAN_CHOICES = [
        (FREE, _('Free')),
        (STARTER, _('Starter')),
        (PROFESSIONAL, _('Professional')),
        (ENTERPRISE, _('Enterprise')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    name = models.CharField(
        _('Name'),
        max_length=255,
        help_text=_('Organization or business name')
    )

    slug = models.SlugField(
        _('Slug'),
        unique=True,
        help_text=_('URL-friendly identifier for the tenant')
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_tenants',
        help_text=_('User who owns this tenant')
    )

    plan = models.CharField(
        _('Plan'),
        max_length=20,
        choices=PLAN_CHOICES,
        default=FREE,
        help_text=_('Current subscription plan')
    )

    is_active = models.BooleanField(
        _('Active'),
        default=True,
        help_text=_('Whether this tenant is currently active')
    )

    trial_ends_at = models.DateTimeField(
        _('Trial Ends At'),
        null=True,
        blank=True,
        help_text=_('When the trial period ends')
    )

    # Usage limits
    max_users = models.IntegerField(
        _('Max Users'),
        default=5,
        help_text=_('Maximum number of users allowed')
    )

    max_clients = models.IntegerField(
        _('Max Clients'),
        default=50,
        help_text=_('Maximum number of clients allowed')
    )

    max_contracts_per_month = models.IntegerField(
        _('Max Contracts Per Month'),
        default=10,
        help_text=_('Maximum contracts that can be created per month')
    )

    max_invoices_per_month = models.IntegerField(
        _('Max Invoices Per Month'),
        default=20,
        help_text=_('Maximum invoices that can be created per month')
    )

    storage_limit_gb = models.DecimalField(
        _('Storage Limit (GB)'),
        max_digits=10,
        decimal_places=2,
        default=1.0,
        help_text=_('Storage limit in gigabytes')
    )

    # Branding
    logo = models.ImageField(
        _('Logo'),
        upload_to='tenants/logos/',
        null=True,
        blank=True,
        help_text=_('Tenant logo image')
    )

    primary_color = models.CharField(
        _('Primary Color'),
        max_length=7,
        default='#007cff',
        help_text=_('Primary brand color (hex)')
    )

    accent_color = models.CharField(
        _('Accent Color'),
        max_length=7,
        default='#00d9c0',
        help_text=_('Accent brand color (hex)')
    )

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Tenant')
        verbose_name_plural = _('Tenants')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['owner']),
            models.Index(fields=['is_active']),
            models.Index(fields=['plan']),
        ]

    def __str__(self):
        return f"{self.name} ({self.slug})"

    @property
    def is_on_trial(self):
        """Check if tenant is currently on trial."""
        from django.utils import timezone
        if not self.trial_ends_at:
            return False
        return timezone.now() < self.trial_ends_at

    @property
    def is_trial_expired(self):
        """Check if tenant's trial has expired."""
        from django.utils import timezone
        if not self.trial_ends_at:
            return False
        return timezone.now() >= self.trial_ends_at


class Domain(models.Model):
    """
    Custom domain associated with a tenant.

    Allows tenants to use custom domains for their client portal.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='domains',
        help_text=_('Tenant this domain belongs to')
    )

    domain = models.CharField(
        _('Domain'),
        max_length=255,
        unique=True,
        help_text=_('Custom domain name (e.g., billing.example.com)')
    )

    is_primary = models.BooleanField(
        _('Primary'),
        default=False,
        help_text=_('Whether this is the primary domain for the tenant')
    )

    is_verified = models.BooleanField(
        _('Verified'),
        default=False,
        help_text=_('Whether domain ownership has been verified')
    )

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)

    class Meta:
        verbose_name = _('Domain')
        verbose_name_plural = _('Domains')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['domain']),
            models.Index(fields=['tenant']),
        ]

    def __str__(self):
        primary = " (primary)" if self.is_primary else ""
        verified = " [verified]" if self.is_verified else " [unverified]"
        return f"{self.domain}{primary}{verified}"
