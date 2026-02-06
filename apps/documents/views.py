"""Document views."""

import logging
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import FileResponse
from .models import Document
from .serializers import DocumentSerializer, DocumentUploadSerializer

logger = logging.getLogger(__name__)


class DocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for document CRUD and file operations."""

    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'tags']
    ordering_fields = ['created_at', 'title', 'file_size', 'document_type']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = Document.objects.select_related('uploaded_by', 'client', 'contract', 'invoice')

        # Filter by document type
        doc_type = self.request.query_params.get('document_type')
        if doc_type:
            queryset = queryset.filter(document_type=doc_type)

        # Filter by client
        client_id = self.request.query_params.get('client')
        if client_id:
            queryset = queryset.filter(client_id=client_id)

        # Filter by contract
        contract_id = self.request.query_params.get('contract')
        if contract_id:
            queryset = queryset.filter(contract_id=contract_id)

        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return DocumentUploadSerializer
        return DocumentSerializer

    def perform_create(self, serializer):
        document = serializer.save(uploaded_by=self.request.user)
        # Queue document processing
        try:
            from .tasks import process_document
            process_document.delay(str(document.id))
        except Exception as e:
            logger.warning(f"Could not queue document processing: {e}")

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download a document file."""
        document = self.get_object()
        if not document.file:
            return Response({'error': 'No file attached'}, status=status.HTTP_404_NOT_FOUND)
        return FileResponse(document.file.open('rb'), as_attachment=True, filename=document.file.name.split('/')[-1])

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search documents by query."""
        query = request.query_params.get('q', '')
        if not query:
            return Response({'results': []})

        documents = self.get_queryset().filter(
            models.Q(title__icontains=query) |
            models.Q(description__icontains=query)
        )[:20]

        serializer = self.get_serializer(documents, many=True)
        return Response({'results': serializer.data})

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get document statistics."""
        qs = self.get_queryset()
        from django.db.models import Sum, Count
        stats = {
            'total': qs.count(),
            'total_size': qs.aggregate(total=Sum('file_size'))['total'] or 0,
            'by_type': list(qs.values('document_type').annotate(count=Count('id')).order_by('-count')),
        }
        return Response(stats)
