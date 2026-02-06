"""Document management models."""

import uuid
import os
from django.db import models
from django.utils.translation import gettext_lazy as _


class Document(models.Model):
    """Document vault model for storing contracts, receipts, and attachments."""

    # Document Types
    CONTRACT = 'contract'
    INVOICE = 'invoice'
    RECEIPT = 'receipt'
    PROPOSAL = 'proposal'
    ATTACHMENT = 'attachment'
    OTHER = 'other'

    TYPE_CHOICES = [
        (CONTRACT, _('Contract')),
        (INVOICE, _('Invoice')),
        (RECEIPT, _('Receipt')),
        (PROPOSAL, _('Proposal')),
        (ATTACHMENT, _('Attachment')),
        (OTHER, _('Other')),
    ]

    # Processing Status
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'

    PROCESSING_STATUS_CHOICES = [
        (PENDING, _('Pending')),
        (PROCESSING, _('Processing')),
        (COMPLETED, _('Completed')),
        (FAILED, _('Failed')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    title = models.CharField(_('Title'), max_length=255, help_text=_('Document title'))

    description = models.TextField(_('Description'), blank=True, help_text=_('Document description'))

    document_type = models.CharField(
        _('Document Type'), max_length=20, choices=TYPE_CHOICES, default=OTHER
    )

    file = models.FileField(_('File'), upload_to='documents/%Y/%m/', help_text=_('Uploaded document file'))

    file_type = models.CharField(_('File Type'), max_length=20, blank=True, help_text=_('File extension'))

    file_size = models.PositiveIntegerField(_('File Size (bytes)'), default=0)

    # Relationships
    uploaded_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='uploaded_documents'
    )

    client = models.ForeignKey(
        'clients.Client', on_delete=models.CASCADE, null=True, blank=True,
        related_name='documents'
    )

    contract = models.ForeignKey(
        'contracts.Contract', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='documents'
    )

    invoice = models.ForeignKey(
        'invoicing.Invoice', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='documents'
    )

    # Processing
    processing_status = models.CharField(
        _('Processing Status'), max_length=20, choices=PROCESSING_STATUS_CHOICES, default=PENDING
    )
    processing_error = models.TextField(_('Processing Error'), blank=True)

    # Access Control
    is_public = models.BooleanField(_('Public'), default=False,
        help_text=_('Whether this document is accessible via client portal'))

    # Tags
    tags = models.JSONField(_('Tags'), default=list, blank=True)

    # Metadata
    metadata = models.JSONField(_('Metadata'), default=dict, blank=True)

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        app_label = 'documents'
        verbose_name = _('Document')
        verbose_name_plural = _('Documents')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['document_type']),
            models.Index(fields=['client']),
            models.Index(fields=['uploaded_by']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.file and not self.file_type:
            _, ext = os.path.splitext(self.file.name)
            self.file_type = ext.lstrip('.').lower()
        if self.file and not self.file_size:
            try:
                self.file_size = self.file.size
            except Exception:
                pass
        super().save(*args, **kwargs)

    @property
    def file_extension(self):
        if self.file:
            _, ext = os.path.splitext(self.file.name)
            return ext.lstrip('.')
        return ''

    @property
    def is_pdf(self):
        return self.file_type == 'pdf'

    @property
    def is_image(self):
        return self.file_type in ('jpg', 'jpeg', 'png', 'gif', 'webp')
