"""
Contract and milestone models.
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal


class Contract(models.Model):
    """
    Contract model representing agreements with clients.
    """

    # Contract Types
    FIXED_PRICE = 'fixed_price'
    HOURLY = 'hourly'
    RETAINER = 'retainer'
    MILESTONE = 'milestone'

    TYPE_CHOICES = [
        (FIXED_PRICE, _('Fixed Price')),
        (HOURLY, _('Hourly')),
        (RETAINER, _('Retainer')),
        (MILESTONE, _('Milestone-based')),
    ]

    # Contract Status
    DRAFT = 'draft'
    PENDING = 'pending'
    ACTIVE = 'active'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'
    ON_HOLD = 'on_hold'

    STATUS_CHOICES = [
        (DRAFT, _('Draft')),
        (PENDING, _('Pending Signature')),
        (ACTIVE, _('Active')),
        (COMPLETED, _('Completed')),
        (CANCELLED, _('Cancelled')),
        (ON_HOLD, _('On Hold')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Contract Number (auto-generated)
    contract_number = models.CharField(
        _('Contract Number'),
        max_length=50,
        unique=True,
        help_text=_('Unique contract identifier (e.g., CNT-001)')
    )

    # Client Relationship
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE,
        related_name='contracts',
        help_text=_('Client this contract is with')
    )

    # Basic Contract Info
    title = models.CharField(
        _('Contract Title'),
        max_length=255,
        help_text=_('Brief title describing the contract')
    )

    description = models.TextField(
        _('Description'),
        help_text=_('Detailed description of the contract scope')
    )

    contract_type = models.CharField(
        _('Contract Type'),
        max_length=20,
        choices=TYPE_CHOICES,
        default=FIXED_PRICE
    )

    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=DRAFT
    )

    # Dates
    start_date = models.DateField(
        _('Start Date'),
        help_text=_('Contract start date')
    )

    end_date = models.DateField(
        _('End Date'),
        blank=True,
        null=True,
        help_text=_('Contract end date (if applicable)')
    )

    # Financial Details
    value = models.DecimalField(
        _('Contract Value'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_('Total contract value')
    )

    currency = models.CharField(
        _('Currency'),
        max_length=3,
        default='USD',
        help_text=_('Currency code (e.g., USD, EUR, GBP)')
    )

    hourly_rate = models.DecimalField(
        _('Hourly Rate'),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_('Hourly rate (for hourly contracts)')
    )

    estimated_hours = models.DecimalField(
        _('Estimated Hours'),
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_('Estimated hours (for hourly contracts)')
    )

    # Payment Terms
    payment_terms = models.TextField(
        _('Payment Terms'),
        blank=True,
        help_text=_('Payment terms and conditions (e.g., "Net 30", "50% upfront")')
    )

    invoice_schedule = models.CharField(
        _('Invoice Schedule'),
        max_length=50,
        blank=True,
        help_text=_('When to generate invoices (e.g., "Monthly", "Upon milestone completion")')
    )

    # Terms and Conditions
    terms_and_conditions = models.TextField(
        _('Terms and Conditions'),
        blank=True,
        help_text=_('Full contract terms and conditions')
    )

    # Signature & Approval
    signed_at = models.DateTimeField(
        _('Signed At'),
        blank=True,
        null=True,
        help_text=_('When the contract was signed')
    )

    signed_by_client = models.BooleanField(
        _('Signed by Client'),
        default=False,
        help_text=_('Whether the client has signed the contract')
    )

    signed_by_company = models.BooleanField(
        _('Signed by Company'),
        default=False,
        help_text=_('Whether the company has signed the contract')
    )

    signature_client = models.TextField(
        _('Client Signature'),
        blank=True,
        help_text=_('Client digital signature or e-signature ID')
    )

    signature_company = models.TextField(
        _('Company Signature'),
        blank=True,
        help_text=_('Company digital signature or e-signature ID')
    )

    # Document Management
    contract_file = models.FileField(
        _('Contract File'),
        upload_to='contracts/files/',
        blank=True,
        null=True,
        help_text=_('PDF or document file of the contract')
    )

    docusign_envelope_id = models.CharField(
        _('DocuSign Envelope ID'),
        max_length=255,
        blank=True,
        help_text=_('DocuSign envelope ID for e-signature tracking')
    )

    # Assignment
    owner = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_contracts',
        help_text=_('Team member responsible for this contract')
    )

    # Financial Tracking
    invoiced_amount = models.DecimalField(
        _('Invoiced Amount'),
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_('Total amount invoiced for this contract')
    )

    paid_amount = models.DecimalField(
        _('Paid Amount'),
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_('Total amount paid for this contract')
    )

    # Progress Tracking
    completion_percentage = models.IntegerField(
        _('Completion %'),
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_('Overall contract completion percentage (0-100)')
    )

    # Notes
    notes = models.TextField(
        _('Internal Notes'),
        blank=True,
        help_text=_('Internal notes about the contract')
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
        verbose_name = _('Contract')
        verbose_name_plural = _('Contracts')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['contract_number']),
            models.Index(fields=['client']),
            models.Index(fields=['status']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['owner']),
        ]

    def __str__(self):
        return f"{self.contract_number} - {self.title}"

    def save(self, *args, **kwargs):
        """Generate contract number if not set."""
        if not self.contract_number:
            # Get the latest contract number
            last_contract = Contract.objects.order_by('-contract_number').first()
            if last_contract and last_contract.contract_number.startswith('CNT-'):
                try:
                    last_num = int(last_contract.contract_number.split('-')[1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1

            self.contract_number = f"CNT-{new_num:05d}"

        super().save(*args, **kwargs)

    @property
    def is_signed(self):
        """Check if contract is fully signed."""
        return self.signed_by_client and self.signed_by_company

    @property
    def total_value(self):
        """Return the total contract value (alias for value)."""
        return self.value

    @property
    def outstanding_amount(self):
        """Calculate outstanding amount."""
        return self.invoiced_amount - self.paid_amount

    @property
    def is_active_period(self):
        """Check if contract is in active date range."""
        from django.utils import timezone
        today = timezone.now().date()

        if self.end_date:
            return self.start_date <= today <= self.end_date
        return self.start_date <= today

    def update_financial_summary(self):
        """Update financial summary from invoices."""
        from apps.invoicing.models import Invoice
        from django.db.models import Sum

        # Calculate invoiced amount
        invoiced = Invoice.objects.filter(
            contract=self
        ).aggregate(Sum('total'))['total__sum'] or 0

        # Calculate paid amount
        paid = Invoice.objects.filter(
            contract=self,
            status='paid'
        ).aggregate(Sum('total'))['total__sum'] or 0

        self.invoiced_amount = invoiced
        self.paid_amount = paid
        self.save()

    def update_completion_percentage(self):
        """Update completion percentage from milestones."""
        milestones = self.milestones.all()
        if not milestones.exists():
            return

        total_milestones = milestones.count()
        completed_milestones = milestones.filter(status=ContractMilestone.COMPLETED).count()

        self.completion_percentage = int((completed_milestones / total_milestones) * 100)
        self.save()


class ContractMilestone(models.Model):
    """
    Contract milestone for tracking progress and payments.
    """

    # Milestone Status
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (PENDING, _('Pending')),
        (IN_PROGRESS, _('In Progress')),
        (COMPLETED, _('Completed')),
        (CANCELLED, _('Cancelled')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='milestones',
        help_text=_('Contract this milestone belongs to')
    )

    title = models.CharField(
        _('Milestone Title'),
        max_length=255,
        help_text=_('Brief title describing the milestone')
    )

    description = models.TextField(
        _('Description'),
        blank=True,
        help_text=_('Detailed description of milestone deliverables')
    )

    due_date = models.DateField(
        _('Due Date'),
        help_text=_('Expected completion date')
    )

    amount = models.DecimalField(
        _('Milestone Amount'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_('Payment amount for this milestone')
    )

    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING
    )

    # Completion Tracking
    completed_at = models.DateTimeField(
        _('Completed At'),
        blank=True,
        null=True,
        help_text=_('When the milestone was completed')
    )

    completed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='completed_milestones',
        help_text=_('User who marked the milestone as complete')
    )

    # Invoice Link
    invoice_generated = models.BooleanField(
        _('Invoice Generated'),
        default=False,
        help_text=_('Whether an invoice has been generated for this milestone')
    )

    # Order
    order = models.IntegerField(
        _('Order'),
        default=0,
        help_text=_('Display order of the milestone')
    )

    # Deliverables
    deliverables = models.JSONField(
        _('Deliverables'),
        default=list,
        blank=True,
        help_text=_('List of deliverables for this milestone')
    )

    # Notes
    notes = models.TextField(
        _('Notes'),
        blank=True,
        help_text=_('Notes about the milestone')
    )

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Contract Milestone')
        verbose_name_plural = _('Contract Milestones')
        ordering = ['order', 'due_date']
        indexes = [
            models.Index(fields=['contract', 'status']),
            models.Index(fields=['due_date']),
        ]

    def __str__(self):
        return f"{self.contract.contract_number} - {self.title}"

    @property
    def is_overdue(self):
        """Check if milestone is overdue."""
        from django.utils import timezone
        if self.status in [self.COMPLETED, self.CANCELLED]:
            return False
        return timezone.now().date() > self.due_date
