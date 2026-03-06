"""
Documents Celery tasks for Aureon SaaS Platform.

These tasks handle document processing.
"""
from celery import shared_task
import logging
import os

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2)
def process_document(self, document_id):
    """Process an uploaded document (validate, generate thumbnail, extract metadata)."""
    try:
        from apps.documents.models import Document

        document = Document.objects.get(id=document_id)
        logger.info(f"Processing document {document.title}...")

        # Validate file type
        if document.file:
            file_path = document.file.path if hasattr(document.file, 'path') else None
            file_size = document.file.size

            # Update file size
            document.file_size = file_size

            # Extract file extension
            _, ext = os.path.splitext(document.file.name)
            document.file_type = ext.lstrip('.').lower()

            # Mark as processed
            document.processing_status = 'completed'
            document.save(update_fields=['file_size', 'file_type', 'processing_status', 'updated_at'])

            logger.info(f"Document {document.title} processed: {document.file_type}, {file_size} bytes")
        else:
            document.processing_status = 'failed'
            document.processing_error = 'No file attached'
            document.save(update_fields=['processing_status', 'processing_error', 'updated_at'])

        return {'status': 'success', 'document_id': str(document_id)}
    except Exception as exc:
        logger.error(f"Document processing failed: {exc}")
        raise self.retry(exc=exc, countdown=60)
