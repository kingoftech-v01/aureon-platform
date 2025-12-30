"""
Documents Celery tasks for Aureon SaaS Platform.

These tasks handle document processing.
"""
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2)
def process_document(self, document_id):
    """
    Process an uploaded document (e.g., OCR, virus scan).
    """
    try:
        logger.info(f"Processing document {document_id}...")
        return {'status': 'success', 'document_id': document_id}
    except Exception as exc:
        logger.error(f"Document processing failed: {exc}")
        raise self.retry(exc=exc, countdown=60)
