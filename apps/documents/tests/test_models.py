"""
Tests for document models.

Tests cover:
- Document creation and defaults
- File extension detection
- is_pdf / is_image properties
- Auto-detection of file_type on save
- String representation
"""

import uuid
import pytest
from unittest.mock import MagicMock, PropertyMock, patch
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.documents.models import Document


@pytest.mark.django_db
class TestDocument:
    """Tests for the Document model."""

    def _create_document(self, filename='report.pdf', content=b'%PDF-1.4 fake', **overrides):
        """Helper to create a Document with a fake uploaded file."""
        uploaded_file = SimpleUploadedFile(filename, content, content_type='application/pdf')
        defaults = {
            'title': 'Test Document',
            'description': 'A test document for unit testing.',
            'document_type': Document.CONTRACT,
            'file': uploaded_file,
        }
        defaults.update(overrides)
        return Document.objects.create(**defaults)

    def test_create_document(self):
        """Document should be created with correct field values."""
        doc = self._create_document()

        assert doc.pk is not None
        assert isinstance(doc.id, uuid.UUID)
        assert doc.title == 'Test Document'
        assert doc.description == 'A test document for unit testing.'
        assert doc.document_type == Document.CONTRACT
        assert doc.file is not None
        assert doc.processing_status == Document.PENDING
        assert doc.is_public is False
        assert doc.tags == []
        assert doc.metadata == {}
        assert doc.created_at is not None
        assert doc.updated_at is not None

    def test_document_str(self):
        """String representation should return the title."""
        doc = self._create_document(title='My Contract')
        assert str(doc) == 'My Contract'

    def test_document_file_extension(self):
        """file_extension property should return the extension without dot."""
        doc = self._create_document(filename='contract.pdf')
        assert doc.file_extension == 'pdf'

    def test_document_file_extension_multiple_dots(self):
        """file_extension should handle filenames with multiple dots."""
        doc = self._create_document(filename='my.report.final.docx', content=b'docx content')
        assert doc.file_extension == 'docx'

    def test_document_file_extension_no_extension(self):
        """file_extension should return empty string for files without extension."""
        doc = self._create_document(filename='README', content=b'readme content')
        assert doc.file_extension == ''

    def test_document_is_pdf(self):
        """is_pdf should be True for PDF files."""
        doc = self._create_document(filename='invoice.pdf')
        assert doc.is_pdf is True

    def test_document_is_pdf_false(self):
        """is_pdf should be False for non-PDF files."""
        doc = self._create_document(filename='image.png', content=b'\x89PNG')
        assert doc.is_pdf is False

    def test_document_is_image_jpg(self):
        """is_image should be True for JPG files."""
        doc = self._create_document(filename='photo.jpg', content=b'\xff\xd8\xff')
        assert doc.is_image is True

    def test_document_is_image_jpeg(self):
        """is_image should be True for JPEG files."""
        doc = self._create_document(filename='photo.jpeg', content=b'\xff\xd8\xff')
        assert doc.is_image is True

    def test_document_is_image_png(self):
        """is_image should be True for PNG files."""
        doc = self._create_document(filename='screenshot.png', content=b'\x89PNG')
        assert doc.is_image is True

    def test_document_is_image_gif(self):
        """is_image should be True for GIF files."""
        doc = self._create_document(filename='animation.gif', content=b'GIF89a')
        assert doc.is_image is True

    def test_document_is_image_webp(self):
        """is_image should be True for WebP files."""
        doc = self._create_document(filename='modern.webp', content=b'RIFF')
        assert doc.is_image is True

    def test_document_is_image_false(self):
        """is_image should be False for non-image files."""
        doc = self._create_document(filename='report.pdf')
        assert doc.is_image is False

    def test_document_save_auto_type(self):
        """save() should auto-detect file_type from the file extension."""
        doc = self._create_document(filename='proposal.docx', content=b'docx fake')

        assert doc.file_type == 'docx'

    def test_document_save_auto_type_uppercase(self):
        """save() should normalize file_type to lowercase."""
        doc = self._create_document(filename='REPORT.PDF')

        assert doc.file_type == 'pdf'

    def test_document_save_preserves_existing_file_type(self):
        """save() should not overwrite an explicitly set file_type."""
        uploaded_file = SimpleUploadedFile('doc.txt', b'text content')
        doc = Document.objects.create(
            title='Explicit Type',
            file=uploaded_file,
            file_type='custom',
        )

        # file_type was explicitly set, so save() should keep it
        assert doc.file_type == 'custom'

    def test_document_save_auto_file_size(self):
        """save() should auto-detect file_size from the file."""
        content = b'x' * 1024
        doc = self._create_document(filename='sized.bin', content=content)

        assert doc.file_size == 1024

    def test_document_type_choices(self):
        """All document types should be valid."""
        for type_value, _ in Document.TYPE_CHOICES:
            doc = self._create_document(
                document_type=type_value,
                filename=f'{type_value}.pdf',
            )
            assert doc.document_type == type_value

    def test_document_processing_status_choices(self):
        """All processing statuses should be valid."""
        for status_value, _ in Document.PROCESSING_STATUS_CHOICES:
            doc = self._create_document(
                processing_status=status_value,
                filename=f'{status_value}.pdf',
            )
            assert doc.processing_status == status_value

    def test_document_with_tags(self):
        """Document should store JSON tags correctly."""
        doc = self._create_document(tags=['urgent', 'signed', 'v2'])
        doc.refresh_from_db()
        assert doc.tags == ['urgent', 'signed', 'v2']

    def test_document_with_metadata(self):
        """Document should store JSON metadata correctly."""
        meta = {'version': 3, 'source': 'upload', 'pages': 10}
        doc = self._create_document(metadata=meta)
        doc.refresh_from_db()
        assert doc.metadata == meta

    def test_document_relationships(self, admin_user, client_company, contract_fixed):
        """Document should link to user, client, and contract."""
        doc = self._create_document(
            uploaded_by=admin_user,
            client=client_company,
            contract=contract_fixed,
        )
        doc.refresh_from_db()

        assert doc.uploaded_by == admin_user
        assert doc.client == client_company
        assert doc.contract == contract_fixed

    def test_document_ordering(self):
        """Documents should be ordered by -created_at (newest first)."""
        doc1 = self._create_document(title='First', filename='first.pdf')
        doc2 = self._create_document(title='Second', filename='second.pdf')

        docs = list(Document.objects.all())
        assert docs[0].title == 'Second'
        assert docs[1].title == 'First'

    def test_document_public_flag(self):
        """is_public flag should be settable."""
        doc = self._create_document(is_public=True)
        assert doc.is_public is True

        doc_private = self._create_document(is_public=False, filename='private.pdf')
        assert doc_private.is_public is False

    def test_document_save_file_size_exception_handled(self):
        """save() should handle exception when file.size raises (line 121)."""
        # First create a document with a file normally
        uploaded_file = SimpleUploadedFile('broken_size.pdf', b'%PDF-1.4 test')
        doc = self._create_document(filename='broken_size.pdf')
        doc_id = doc.id

        # Now re-fetch and clear file_size, then save with a broken .size
        doc = Document.objects.get(id=doc_id)
        # Clear file_size and file_type so save() tries to re-detect them
        Document.objects.filter(id=doc_id).update(file_size=0, file_type='')
        doc.refresh_from_db()
        assert doc.file_size == 0
        assert doc.file_type == ''

        # Patch file.size to raise an exception
        original_file = doc.file
        with patch.object(
            type(original_file), 'size',
            new_callable=PropertyMock,
            side_effect=Exception('Size unavailable'),
        ):
            # This should exercise lines 119-122 (try/except)
            doc.save()

        doc.refresh_from_db()
        # file_type was set from the name, but file_size remains 0 because .size raised
        assert doc.file_type == 'pdf'
        assert doc.file_size == 0

    def test_document_file_extension_no_file(self):
        """file_extension should return empty string when no file is attached (line 130)."""
        doc = Document.objects.create(
            title='No File Extension',
            document_type=Document.OTHER,
        )
        assert doc.file_extension == ''
