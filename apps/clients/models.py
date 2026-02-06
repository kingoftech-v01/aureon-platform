"""
Client and contact models for CRM functionality.
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import EmailValidator
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.postgres.fields import ArrayField


class Client(models.Model):
    """
    Client/Contact model for CRM.

    Represents a client or prospect in the system.
    """

    # Lifecycle Stages
    LEAD = 'lead'
    PROSPECT = 'prospect'
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    CHURNED = 'churned'

    STAGE_CHOICES = [
        (LEAD, _('Lead - Initial Contact')),
        (PROSPECT, _('Prospect - Qualified Lead')),
        (ACTIVE, _('Active Client')),
        (INACTIVE, _('Inactive')),
        (CHURNED, _('Churned')),
    ]

    # Client Types
    INDIVIDUAL = 'individual'
    COMPANY = 'company'

    TYPE_CHOICES = [
        (INDIVIDUAL, _('Individual')),
        (COMPANY, _('Company')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Basic Information
    client_type = models.CharField(
        _('Client Type'),
        max_length=20,
        choices=TYPE_CHOICES,
        default=COMPANY
    )

    # Company Info (for company clients)
    company_name = models.CharField(
        _('Company Name'),
        max_length=255,
        blank=True,
        help_text=_('Name of the company (if client is a company)')
    )

    # Individual Info
    first_name = models.CharField(
        _('First Name'),
        max_length=100,
        help_text=_('First name of primary contact')
    )

    last_name = models.CharField(
        _('Last Name'),
        max_length=100,
        help_text=_('Last name of primary contact')
    )

    email = models.EmailField(
        _('Email Address'),
        validators=[EmailValidator()],
        help_text=_('Primary email address')
    )

    phone = PhoneNumberField(
        _('Phone Number'),
        blank=True,
        null=True,
        help_text=_('Primary phone number')
    )

    # Additional Contact Info
    secondary_email = models.EmailField(
        _('Secondary Email'),
        blank=True,
        help_text=_('Secondary email address')
    )

    secondary_phone = PhoneNumberField(
        _('Secondary Phone'),
        blank=True,
        null=True,
        help_text=_('Secondary phone number')
    )

    website = models.URLField(
        _('Website'),
        blank=True,
        help_text=_('Company or personal website')
    )

    # Address
    address_line1 = models.CharField(_('Address Line 1'), max_length=255, blank=True)
    address_line2 = models.CharField(_('Address Line 2'), max_length=255, blank=True)
    city = models.CharField(_('City'), max_length=100, blank=True)
    state = models.CharField(_('State/Province'), max_length=100, blank=True)
    postal_code = models.CharField(_('Postal Code'), max_length=20, blank=True)
    country = models.CharField(_('Country'), max_length=100, default='United States')

    # Business Details
    industry = models.CharField(
        _('Industry'),
        max_length=100,
        blank=True,
        help_text=_('Industry or business sector')
    )

    company_size = models.CharField(
        _('Company Size'),
        max_length=50,
        blank=True,
        help_text=_('Number of employees (e.g., "1-10", "11-50", etc.)')
    )

    annual_revenue = models.DecimalField(
        _('Annual Revenue'),
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_('Estimated annual revenue')
    )

    # Tax Information
    tax_id = models.CharField(
        _('Tax ID / VAT Number'),
        max_length=50,
        blank=True,
        help_text=_('Tax identification number or VAT number')
    )

    # CRM Fields
    lifecycle_stage = models.CharField(
        _('Lifecycle Stage'),
        max_length=20,
        choices=STAGE_CHOICES,
        default=LEAD,
        help_text=_('Current stage in the customer lifecycle')
    )

    source = models.CharField(
        _('Lead Source'),
        max_length=100,
        blank=True,
        help_text=_('How the client found you (e.g., "Website", "Referral", "Cold Outreach")')
    )

    tags = ArrayField(
        models.CharField(max_length=50),
        default=list,
        blank=True,
        help_text=_('Tags for categorization')
    )

    # Assignment
    owner = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_clients',
        help_text=_('Team member responsible for this client')
    )

    # Financial Summary (computed from invoices/contracts)
    total_value = models.DecimalField(
        _('Total Contract Value'),
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_('Total value of all contracts')
    )

    total_paid = models.DecimalField(
        _('Total Paid'),
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_('Total amount paid by client')
    )

    outstanding_balance = models.DecimalField(
        _('Outstanding Balance'),
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_('Current outstanding balance')
    )

    # Portal Access
    portal_access_enabled = models.BooleanField(
        _('Portal Access'),
        default=True,
        help_text=_('Whether client can access the client portal')
    )

    portal_user = models.OneToOneField(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='client_profile',
        help_text=_('User account for client portal access')
    )

    # Notes & History
    notes = models.TextField(
        _('Notes'),
        blank=True,
        help_text=_('Internal notes about the client')
    )

    # Status
    is_active = models.BooleanField(
        _('Active'),
        default=True,
        help_text=_('Whether the client is currently active')
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
        verbose_name = _('Client')
        verbose_name_plural = _('Clients')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['company_name']),
            models.Index(fields=['lifecycle_stage']),
            models.Index(fields=['owner']),
            models.Index(fields=['is_active']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(client_type='company', company_name__isnull=False) | models.Q(client_type='individual'),
                name='company_name_required_for_companies'
            )
        ]

    def __str__(self):
        if self.client_type == self.COMPANY and self.company_name:
            return f"{self.company_name} ({self.get_full_name()})"
        return self.get_full_name()

    def get_full_name(self):
        """Return full name of contact."""
        return f"{self.first_name} {self.last_name}".strip()

    def get_display_name(self):
        """Return display name (company name or full name)."""
        if self.client_type == self.COMPANY and self.company_name:
            return self.company_name
        return self.get_full_name()

    @property
    def is_company(self):
        """Check if client is a company."""
        return self.client_type == self.COMPANY

    @property
    def payment_status(self):
        """Get payment status indicator."""
        if self.outstanding_balance > 0:
            return 'outstanding'
        elif self.total_paid > 0:
            return 'paid_up'
        return 'no_transactions'

    def update_financial_summary(self):
        """Update financial summary from related invoices and contracts."""
        from apps.invoicing.models import Invoice
        from apps.contracts.models import Contract
        from django.db.models import Sum

        # Calculate total revenue from paid invoices
        paid_total = Invoice.objects.filter(
            client=self,
            status=Invoice.PAID
        ).aggregate(total=Sum('total'))['total'] or 0

        # Calculate outstanding balance
        outstanding = Invoice.objects.filter(
            client=self,
            status__in=[Invoice.SENT, Invoice.VIEWED, Invoice.PARTIALLY_PAID]
        ).aggregate(total=Sum('total'))['total'] or 0

        self.total_revenue = paid_total
        self.outstanding_balance = outstanding
        self.save(update_fields=['total_revenue', 'outstanding_balance', 'updated_at'])

    def create_portal_access(self):
        """Create portal user account for client."""
        if self.portal_user:
            return self.portal_user

        from apps.accounts.models import User
        import secrets

        # Generate random password
        password = secrets.token_urlsafe(16)

        # Create user account
        user = User.objects.create_user(
            email=self.email,
            password=password,
            first_name=self.first_name,
            last_name=self.last_name,
            role=User.CLIENT,
            # Note: tenant will be set in signal
        )

        self.portal_user = user
        self.save()

        try:
            from apps.notifications.services import NotificationService
            NotificationService.send_client_welcome(self)
        except Exception:
            pass

        return user


class ClientNote(models.Model):
    """
    Notes and interactions with clients.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='client_notes',
        help_text=_('Client this note belongs to')
    )

    author = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='authored_notes',
        help_text=_('User who created the note')
    )

    note_type = models.CharField(
        _('Note Type'),
        max_length=50,
        choices=[
            ('general', _('General Note')),
            ('call', _('Phone Call')),
            ('meeting', _('Meeting')),
            ('email', _('Email')),
            ('task', _('Task/Follow-up')),
        ],
        default='general'
    )

    subject = models.CharField(
        _('Subject'),
        max_length=255,
        blank=True,
        help_text=_('Note subject or title')
    )

    content = models.TextField(
        _('Content'),
        help_text=_('Note content')
    )

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Client Note')
        verbose_name_plural = _('Client Notes')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client', '-created_at']),
            models.Index(fields=['author']),
        ]

    def __str__(self):
        return f"Note for {self.client} by {self.author} - {self.created_at.strftime('%Y-%m-%d')}"


class ClientDocument(models.Model):
    """
    Documents attached to clients.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='documents',
        help_text=_('Client this document belongs to')
    )

    name = models.CharField(
        _('Document Name'),
        max_length=255,
        help_text=_('Name of the document')
    )

    file = models.FileField(
        _('File'),
        upload_to='clients/documents/',
        help_text=_('Document file')
    )

    file_size = models.PositiveIntegerField(
        _('File Size'),
        help_text=_('File size in bytes'),
        editable=False,
        null=True
    )

    file_type = models.CharField(
        _('File Type'),
        max_length=50,
        blank=True,
        help_text=_('MIME type of the file')
    )

    description = models.TextField(
        _('Description'),
        blank=True,
        help_text=_('Document description')
    )

    uploaded_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='uploaded_client_documents',
        help_text=_('User who uploaded the document')
    )

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)

    class Meta:
        verbose_name = _('Client Document')
        verbose_name_plural = _('Client Documents')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client', '-created_at']),
        ]

    def __str__(self):
        return f"{self.name} - {self.client}"

    def save(self, *args, **kwargs):
        """Set file size on save."""
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)
