"""
Tests for documents Celery tasks.

Covers:
- process_document: file validation, metadata extraction, error handling, retries
"""

import uuid
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from celery.exceptions import Retry

from apps.documents.models import Document
from apps.documents.tasks import process_document


@pytest.fixture
def document_with_file(db):
    """Create a document with a mock file attached."""
    doc = Document.objects.create(
        title='Task Test Doc',
        description='For task testing.',
        document_type=Document.CONTRACT,
        processing_status=Document.PENDING,
    )
    return doc


@pytest.fixture
def document_no_file(db):
    """Create a document with no file."""
    doc = Document.objects.create(
        title='No File Doc',
        description='Missing file.',
        document_type=Document.OTHER,
        processing_status=Document.PENDING,
    )
    return doc


# ---------------------------------------------------------------------------
# process_document
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestProcessDocument:

    def test_processes_document_with_file(self, document_with_file):
        """Document with a valid file should be marked as completed."""
        mock_file = MagicMock()
        mock_file.name = 'contract.pdf'
        mock_file.size = 2048
        mock_file.path = '/tmp/contract.pdf'
        type(mock_file).path = PropertyMock(return_value='/tmp/contract.pdf')

        # Patch the file on the document
        with patch.object(Document, 'file', new_callable=PropertyMock) as mock_field:
            mock_field.return_value = mock_file
            # Make bool(document.file) truthy
            mock_file.__bool__ = MagicMock(return_value=True)

            result = process_document(document_with_file.id)

        assert result['status'] == 'success'
        assert result['document_id'] == str(document_with_file.id)

        document_with_file.refresh_from_db()
        assert document_with_file.processing_status == 'completed'
        assert document_with_file.file_size == 2048
        assert document_with_file.file_type == 'pdf'

    def test_no_file_marks_as_failed(self, document_no_file):
        """Document without a file should be marked as failed."""
        result = process_document(document_no_file.id)

        assert result['status'] == 'success'
        document_no_file.refresh_from_db()
        assert document_no_file.processing_status == 'failed'
        assert document_no_file.processing_error == 'No file attached'

    def test_nonexistent_document_retries(self):
        """Processing a non-existent document should trigger a retry."""
        fake_id = uuid.uuid4()
        with pytest.raises(Exception):
            process_document(fake_id)

    def test_extracts_file_extension(self, document_with_file):
        """Should extract file extension correctly."""
        mock_file = MagicMock()
        mock_file.name = 'report.DOCX'
        mock_file.size = 512
        mock_file.path = '/tmp/report.DOCX'
        type(mock_file).path = PropertyMock(return_value='/tmp/report.DOCX')
        mock_file.__bool__ = MagicMock(return_value=True)

        with patch.object(Document, 'file', new_callable=PropertyMock) as mock_field:
            mock_field.return_value = mock_file

            result = process_document(document_with_file.id)

        document_with_file.refresh_from_db()
        assert document_with_file.file_type == 'docx'

    def test_returns_document_id_as_string(self, document_no_file):
        """Result should contain document_id as a string."""
        result = process_document(document_no_file.id)
        assert isinstance(result['document_id'], str)

    def test_file_without_path_attribute(self, document_with_file):
        """Should handle files without a 'path' attribute (e.g., S3 storage)."""
        mock_file = MagicMock(spec=['name', 'size', 'read'])
        mock_file.name = 'cloud_doc.pdf'
        mock_file.size = 4096
        mock_file.__bool__ = MagicMock(return_value=True)
        # hasattr(mock_file, 'path') should be False since 'path' not in spec

        with patch.object(Document, 'file', new_callable=PropertyMock) as mock_field:
            mock_field.return_value = mock_file

            result = process_document(document_with_file.id)

        document_with_file.refresh_from_db()
        assert document_with_file.processing_status == 'completed'
        assert document_with_file.file_size == 4096
