"""
Proposal models for creating and managing client proposals.
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class Proposal(models.Model):
    """
    Proposal model representing proposals sent to clients.
    """

    # Proposal Status
    DRAFT = 'draft'
    SENT = 'sent'
    VIEWED = 'viewed'
    ACCEPTED = 'accepted'
    DECLINED = 'declined'
    EXPIRED = 'expired'
    CONVERTED = 'converted'

    STATUS_CHOICES = [
        (DRAFT, _('Draft')),
        (SENT, _('Sent')),
        (VIEWED, _('Viewed')),
        (ACCEPTED, _('Accepted')),
        (DECLINED, _('Declined')),
        (EXPIRED, _('Expired')),
        (CONVERTED, _('Converted')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Proposal Number (auto-generated)
    proposal_number = models.CharField(
        _('Proposal Number'),
        max_length=50,
        unique=True,
        help_text=_('Unique proposal identifier (e.g., PRP-00001)')
    )

    # Client Relationship
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE,
        related_name='proposals',
        help_text=_('Client this proposal is for')
    )

    # Basic Proposal Info
    title = models.CharField(
        _('Proposal Title'),
        max_length=255,
        help_text=_('Brief title describing the proposal')
    )

    description = models.TextField(
        _('Description'),
        blank=True,
        help_text=_('Detailed description of the proposal')
    )

    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=DRAFT
    )

    # Validity
    valid_until = models.DateField(
        _('Valid Until'),
        help_text=_('Proposal expiration date')
    )

    # Financial Details
    total_value = models.DecimalField(
        _('Total Value'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_('Total proposal value')
    )

    currency = models.CharField(
        _('Currency'),
        max_length=3,
        default='USD',
        help_text=_('Currency code (e.g., USD, EUR, GBP)')
    )

    # Assignment
    owner = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_proposals',
        help_text=_('Team member responsible for this proposal')
    )

    # Contract Link
    contract = models.ForeignKey(
        'contracts.Contract',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='proposals',
        help_text=_('Contract generated from this proposal')
    )

    # Tracking Dates
    sent_at = models.DateTimeField(
        _('Sent At'),
        null=True,
        blank=True,
        help_text=_('When the proposal was sent to the client')
    )

    viewed_at = models.DateTimeField(
        _('Viewed At'),
        null=True,
        blank=True,
        help_text=_('When the client first viewed the proposal')
    )

    accepted_at = models.DateTimeField(
        _('Accepted At'),
        null=True,
        blank=True,
        help_text=_('When the client accepted the proposal')
    )

    declined_at = models.DateTimeField(
        _('Declined At'),
        null=True,
        blank=True,
        help_text=_('When the client declined the proposal')
    )

    # Client Response
    client_message = models.TextField(
        _('Client Message'),
        blank=True,
        help_text=_('Message from the client upon acceptance or decline')
    )

    signature = models.TextField(
        _('Signature'),
        blank=True,
        help_text=_('Client digital signature or e-signature data')
    )

    # Document Management
    pdf_file = models.FileField(
        _('PDF File'),
        upload_to='proposals/pdfs/',
        null=True,
        blank=True,
        help_text=_('Generated PDF proposal')
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
        verbose_name = _('Proposal')
        verbose_name_plural = _('Proposals')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['proposal_number']),
            models.Index(fields=['client']),
            models.Index(fields=['status']),
            models.Index(fields=['owner']),
        ]

    def __str__(self):
        return f"{self.proposal_number} - {self.title}"

    def save(self, *args, **kwargs):
        """Generate proposal number if not set."""
        if not self.proposal_number:
            # Get the latest proposal number
            last_proposal = Proposal.objects.order_by('-proposal_number').first()
            if last_proposal and last_proposal.proposal_number.startswith('PRP-'):
                try:
                    last_num = int(last_proposal.proposal_number.split('-')[1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1

            self.proposal_number = f"PRP-{new_num:05d}"

        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        """Check if proposal is expired based on valid_until date."""
        from django.utils import timezone
        if self.status in [self.ACCEPTED, self.CONVERTED]:
            return False
        return timezone.now().date() > self.valid_until


class ProposalSection(models.Model):
    """
    Section within a proposal for structured content.
    """

    # Section Types
    OVERVIEW = 'overview'
    SCOPE = 'scope'
    TIMELINE = 'timeline'
    PRICING = 'pricing'
    TERMS = 'terms'
    CUSTOM = 'custom'

    SECTION_TYPE_CHOICES = [
        (OVERVIEW, _('Overview')),
        (SCOPE, _('Scope')),
        (TIMELINE, _('Timeline')),
        (PRICING, _('Pricing')),
        (TERMS, _('Terms')),
        (CUSTOM, _('Custom')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.CASCADE,
        related_name='sections',
        help_text=_('Proposal this section belongs to')
    )

    title = models.CharField(
        _('Section Title'),
        max_length=255,
        help_text=_('Title of the section')
    )

    content = models.TextField(
        _('Content'),
        blank=True,
        help_text=_('Section content')
    )

    order = models.IntegerField(
        _('Order'),
        default=0,
        help_text=_('Display order of the section')
    )

    section_type = models.CharField(
        _('Section Type'),
        max_length=20,
        choices=SECTION_TYPE_CHOICES,
        default=CUSTOM
    )

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Proposal Section')
        verbose_name_plural = _('Proposal Sections')
        ordering = ['order']

    def __str__(self):
        return f"{self.proposal.proposal_number} - {self.title}"


class ProposalPricingOption(models.Model):
    """
    Pricing option within a proposal for offering multiple tiers.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.CASCADE,
        related_name='pricing_options',
        help_text=_('Proposal this pricing option belongs to')
    )

    name = models.CharField(
        _('Option Name'),
        max_length=255,
        help_text=_('Name of the pricing option')
    )

    description = models.TextField(
        _('Description'),
        blank=True,
        help_text=_('Description of the pricing option')
    )

    price = models.DecimalField(
        _('Price'),
        max_digits=12,
        decimal_places=2,
        help_text=_('Price for this option')
    )

    is_recommended = models.BooleanField(
        _('Is Recommended'),
        default=False,
        help_text=_('Whether this is the recommended option')
    )

    features = models.JSONField(
        _('Features'),
        default=list,
        blank=True,
        help_text=_('List of features included in this option')
    )

    order = models.IntegerField(
        _('Order'),
        default=0,
        help_text=_('Display order of the pricing option')
    )

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Proposal Pricing Option')
        verbose_name_plural = _('Proposal Pricing Options')
        ordering = ['order']

    def __str__(self):
        return f"{self.name} - {self.price}"


class ProposalActivity(models.Model):
    """
    Activity log for tracking proposal events.
    """

    # Activity Types
    CREATED = 'created'
    SENT = 'sent'
    VIEWED = 'viewed'
    ACCEPTED = 'accepted'
    DECLINED = 'declined'
    EDITED = 'edited'
    CONVERTED = 'converted'

    ACTIVITY_TYPE_CHOICES = [
        (CREATED, _('Created')),
        (SENT, _('Sent')),
        (VIEWED, _('Viewed')),
        (ACCEPTED, _('Accepted')),
        (DECLINED, _('Declined')),
        (EDITED, _('Edited')),
        (CONVERTED, _('Converted')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.CASCADE,
        related_name='activities',
        help_text=_('Proposal this activity relates to')
    )

    activity_type = models.CharField(
        _('Activity Type'),
        max_length=20,
        choices=ACTIVITY_TYPE_CHOICES,
        help_text=_('Type of activity')
    )

    description = models.TextField(
        _('Description'),
        blank=True,
        help_text=_('Description of the activity')
    )

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_('User who performed the activity')
    )

    ip_address = models.GenericIPAddressField(
        _('IP Address'),
        null=True,
        blank=True,
        help_text=_('IP address of the user who performed the activity')
    )

    metadata = models.JSONField(
        _('Metadata'),
        default=dict,
        blank=True,
        help_text=_('Additional metadata in JSON format')
    )

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)

    class Meta:
        verbose_name = _('Proposal Activity')
        verbose_name_plural = _('Proposal Activities')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.proposal.proposal_number} - {self.activity_type}"
