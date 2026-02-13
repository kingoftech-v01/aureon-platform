"""
Frontend views for the documents app.

Provides class-based views for document listing, detail, and upload.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView
from django.db.models import Q

from .models import Document


class DocumentListView(LoginRequiredMixin, ListView):
    """List all documents in the document vault with filtering."""
    template_name = 'documents/document_list.html'
    context_object_name = 'documents'

    def get_queryset(self):
        queryset = Document.objects.select_related('uploaded_by', 'client', 'contract').all()
        doc_type = self.request.GET.get('type')
        if doc_type:
            queryset = queryset.filter(document_type=doc_type)
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Documents'
        context['type_choices'] = Document.TYPE_CHOICES
        context['current_type'] = self.request.GET.get('type', '')
        context['search_query'] = self.request.GET.get('q', '')
        context['total_documents'] = Document.objects.count()
        return context


class DocumentDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of a single document with metadata."""
    template_name = 'documents/document_detail.html'
    model = Document
    context_object_name = 'document'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Document: {self.object.title}'
        context['is_pdf'] = self.object.is_pdf
        context['is_image'] = self.object.is_image
        context['file_extension'] = self.object.file_extension
        context['file_size'] = self.object.file_size
        context['uploaded_by'] = self.object.uploaded_by
        context['client'] = self.object.client
        context['contract'] = self.object.contract
        context['invoice'] = self.object.invoice
        return context


class DocumentUploadView(LoginRequiredMixin, TemplateView):
    """Document upload page."""
    template_name = 'documents/document_upload.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Upload Document'
        context['type_choices'] = Document.TYPE_CHOICES
        from apps.clients.models import Client
        context['clients'] = Client.objects.filter(is_active=True)
        from apps.contracts.models import Contract
        context['contracts'] = Contract.objects.exclude(status='cancelled')
        return context
