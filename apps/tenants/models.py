"""
Tenant models for multi-tenancy support.

This module defines the core tenant models using django-tenants.
Each tenant represents an isolated organization with its own data.
"""

from django.db import models
from django_tenants.models import TenantMixin, DomainMixin
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator


class Tenant(TenantMixin):
    """
    Tenant model representing an organization/company in the SaaS platform.

    Each tenant has its own PostgreSQL schema with isolated data.
    Supports agencies, freelancers, and SaaS startups.
    """

    # Tenant Types
    FREELANCER = 'freelancer'
    AGENCY = 'agency'
    STARTUP = 'startup'
    ENTERPRISE = 'enterprise'

    TENANT_TYPE_CHOICES = [
        (FREELANCER, _('Freelancer')),
        (AGENCY, _('Digital Agency')),
        (STARTUP, _('SaaS Startup')),
        (ENTERPRISE, _('Enterprise')),
    ]

    # Subscription Plans
    FREE = 'free'
    STARTER = 'starter'
    PRO = 'pro'
    BUSINESS = 'business'

    PLAN_CHOICES = [
        (FREE, _('Free Plan')),
        (STARTER, _('Starter Plan - $19/month')),
        (PRO, _('Pro Plan - $49/month')),
        (BUSINESS, _('Business Plan - $99/month')),
    ]

    # Organization Details
    name = models.CharField(
        _('Organization Name'),
        max_length=255,
        help_text=_('The official name of the organization')
    )

    slug = models.SlugField(
        _('Slug'),
        max_length=100,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[a-z0-9-]+$',
                message=_('Slug can only contain lowercase letters, numbers, and hyphens')
            )
        ],
        help_text=_('Unique identifier for the tenant (used in subdomain)')
    )

    tenant_type = models.CharField(
        _('Tenant Type'),
        max_length=20,
        choices=TENANT_TYPE_CHOICES,
        default=FREELANCER
    )

    # Subscription & Billing
    plan = models.CharField(
        _('Subscription Plan'),
        max_length=20,
        choices=PLAN_CHOICES,
        default=FREE
    )

    stripe_customer_id = models.CharField(
        _('Stripe Customer ID'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('Stripe customer ID for billing')
    )

    stripe_subscription_id = models.CharField(
        _('Stripe Subscription ID'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('Active Stripe subscription ID')
    )

    # Contact Information
    contact_email = models.EmailField(
        _('Contact Email'),
        help_text=_('Primary contact email for the organization')
    )

    contact_phone = models.CharField(
        _('Contact Phone'),
        max_length=20,
        blank=True,
        help_text=_('Contact phone number')
    )

    # Address
    address_line1 = models.CharField(_('Address Line 1'), max_length=255, blank=True)
    address_line2 = models.CharField(_('Address Line 2'), max_length=255, blank=True)
    city = models.CharField(_('City'), max_length=100, blank=True)
    state = models.CharField(_('State/Province'), max_length=100, blank=True)
    postal_code = models.CharField(_('Postal Code'), max_length=20, blank=True)
    country = models.CharField(_('Country'), max_length=100, default='United States')

    # Branding
    logo = models.ImageField(
        _('Company Logo'),
        upload_to='tenants/logos/',
        blank=True,
        null=True,
        help_text=_('Company logo for branding')
    )

    primary_color = models.CharField(
        _('Primary Brand Color'),
        max_length=7,
        default='#1E40AF',
        help_text=_('Hex color code for primary brand color')
    )

    secondary_color = models.CharField(
        _('Secondary Brand Color'),
        max_length=7,
        default='#10B981',
        help_text=_('Hex color code for secondary/accent color')
    )

    # Settings
    timezone = models.CharField(
        _('Timezone'),
        max_length=50,
        default='UTC',
        help_text=_('Default timezone for the organization')
    )

    currency = models.CharField(
        _('Default Currency'),
        max_length=3,
        default='USD',
        help_text=_('ISO currency code (USD, EUR, GBP, etc.)')
    )

    language = models.CharField(
        _('Default Language'),
        max_length=10,
        default='en',
        help_text=_('Default language code')
    )

    # Features & Limits
    max_users = models.PositiveIntegerField(
        _('Maximum Users'),
        default=1,
        help_text=_('Maximum number of users allowed for this tenant')
    )

    max_clients = models.PositiveIntegerField(
        _('Maximum Clients'),
        default=10,
        help_text=_('Maximum number of clients allowed')
    )

    max_contracts = models.PositiveIntegerField(
        _('Maximum Contracts'),
        default=5,
        help_text=_('Maximum active contracts allowed')
    )

    max_invoices_per_month = models.PositiveIntegerField(
        _('Max Invoices Per Month'),
        default=10,
        help_text=_('Maximum invoices that can be created per month')
    )

    # Feature Flags
    enable_api_access = models.BooleanField(
        _('Enable API Access'),
        default=False,
        help_text=_('Allow API access for integrations')
    )

    enable_custom_branding = models.BooleanField(
        _('Enable Custom Branding'),
        default=False,
        help_text=_('Allow custom branding in client portals')
    )

    enable_multi_currency = models.BooleanField(
        _('Enable Multi-Currency'),
        default=False,
        help_text=_('Support multiple currencies')
    )

    enable_advanced_analytics = models.BooleanField(
        _('Enable Advanced Analytics'),
        default=False,
        help_text=_('Access to advanced analytics and reporting')
    )

    # Status
    is_active = models.BooleanField(
        _('Active'),
        default=True,
        help_text=_('Whether the tenant is currently active')
    )

    is_trial = models.BooleanField(
        _('Trial Account'),
        default=True,
        help_text=_('Whether this is a trial account')
    )

    trial_ends_at = models.DateTimeField(
        _('Trial End Date'),
        blank=True,
        null=True,
        help_text=_('When the trial period ends')
    )

    # Timestamps
    created_on = models.DateTimeField(_('Created On'), auto_now_add=True)
    modified_on = models.DateTimeField(_('Modified On'), auto_now=True)

    # Metadata
    metadata = models.JSONField(
        _('Metadata'),
        default=dict,
        blank=True,
        help_text=_('Additional metadata in JSON format')
    )

    # Auto-created schemas (inherited from TenantMixin)
    # schema_name is automatically created by TenantMixin

    class Meta:
        verbose_name = _('Tenant')
        verbose_name_plural = _('Tenants')
        ordering = ['-created_on']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['schema_name']),
            models.Index(fields=['plan']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.tenant_type})"

    def save(self, *args, **kwargs):
        """Override save to set schema_name from slug if not set."""
        if not self.schema_name:
            self.schema_name = self.slug
        super().save(*args, **kwargs)

    @property
    def is_on_trial(self):
        """Check if tenant is currently on trial."""
        from django.utils import timezone
        if not self.is_trial:
            return False
        if self.trial_ends_at:
            return timezone.now() < self.trial_ends_at
        return True

    @property
    def days_until_trial_ends(self):
        """Calculate days remaining in trial."""
        from django.utils import timezone
        if not self.is_on_trial or not self.trial_ends_at:
            return 0
        delta = self.trial_ends_at - timezone.now()
        return max(0, delta.days)

    def can_add_user(self):
        """Check if tenant can add more users."""
        current_users = self.users.filter(is_active=True).count()
        return current_users < self.max_users

    def can_add_client(self):
        """Check if tenant can add more clients."""
        # This will be checked when clients app is implemented
        return True  # Placeholder

    def upgrade_plan(self, new_plan):
        """Upgrade tenant to a new plan with appropriate limits."""
        plan_limits = {
            self.FREE: {
                'max_users': 1,
                'max_clients': 10,
                'max_contracts': 1,
                'max_invoices_per_month': 10,
                'enable_api_access': False,
                'enable_custom_branding': False,
                'enable_multi_currency': False,
                'enable_advanced_analytics': False,
            },
            self.STARTER: {
                'max_users': 3,
                'max_clients': 50,
                'max_contracts': 10,
                'max_invoices_per_month': 100,
                'enable_api_access': False,
                'enable_custom_branding': True,
                'enable_multi_currency': False,
                'enable_advanced_analytics': False,
            },
            self.PRO: {
                'max_users': 10,
                'max_clients': 200,
                'max_contracts': 50,
                'max_invoices_per_month': 500,
                'enable_api_access': True,
                'enable_custom_branding': True,
                'enable_multi_currency': True,
                'enable_advanced_analytics': True,
            },
            self.BUSINESS: {
                'max_users': 50,
                'max_clients': 1000,
                'max_contracts': 500,
                'max_invoices_per_month': 5000,
                'enable_api_access': True,
                'enable_custom_branding': True,
                'enable_multi_currency': True,
                'enable_advanced_analytics': True,
            },
        }

        if new_plan in plan_limits:
            self.plan = new_plan
            limits = plan_limits[new_plan]
            for key, value in limits.items():
                setattr(self, key, value)
            self.save()


class Domain(DomainMixin):
    """
    Domain model for tenant subdomains.

    Each tenant can have multiple domains (e.g., primary subdomain and custom domains).
    """

    # Domain priority
    is_primary = models.BooleanField(
        _('Primary Domain'),
        default=True,
        help_text=_('Whether this is the primary domain for the tenant')
    )

    # SSL Settings
    ssl_enabled = models.BooleanField(
        _('SSL Enabled'),
        default=True,
        help_text=_('Whether SSL/TLS is enabled for this domain')
    )

    # Status
    is_verified = models.BooleanField(
        _('Verified'),
        default=False,
        help_text=_('Whether the domain ownership has been verified')
    )

    verified_at = models.DateTimeField(
        _('Verified At'),
        blank=True,
        null=True,
        help_text=_('When the domain was verified')
    )

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Domain')
        verbose_name_plural = _('Domains')
        ordering = ['-is_primary', 'domain']
        indexes = [
            models.Index(fields=['domain']),
            models.Index(fields=['tenant', 'is_primary']),
        ]

    def __str__(self):
        primary = " (Primary)" if self.is_primary else ""
        return f"{self.domain}{primary}"

    def save(self, *args, **kwargs):
        """Override save to ensure only one primary domain per tenant."""
        if self.is_primary:
            # Set all other domains for this tenant to non-primary
            Domain.objects.filter(
                tenant=self.tenant,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)
