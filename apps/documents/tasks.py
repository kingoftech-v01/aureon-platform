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

        # Validate file type - check via name attribute to support
        # storage backends that may not implement __bool__ (e.g. S3)
        has_file = getattr(document.file, 'name', None)
        if has_file:
            file_path = document.file.path if hasattr(document.file, 'path') else None
            file_size = document.file.size

            # Run virus scan on uploaded files
            try:
                from apps.core.validators import FileUploadValidator
                validator = FileUploadValidator(
                    check_mime=False,
                    virus_scan=True,
                    max_size=None,
                )
                validator(document.file)
                logger.info(f"Virus scan passed for document {document.title}")
            except Exception as scan_exc:
                logger.warning(f"Virus scan skipped or failed for document {document.title}: {scan_exc}")

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
