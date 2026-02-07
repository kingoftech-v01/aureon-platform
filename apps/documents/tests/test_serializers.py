"""
Tests for documents serializers.

Covers:
- DocumentSerializer: all fields, read-only fields, computed fields,
  get_uploaded_by_name method
- DocumentUploadSerializer: writable fields for upload
"""

import uuid
import pytest
from unittest.mock import MagicMock, PropertyMock, patch
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model

from apps.documents.models import Document
from apps.documents.serializers import DocumentSerializer, DocumentUploadSerializer

User = get_user_model()


@pytest.fixture
def user(db, tenant):
    return User.objects.create_user(
        username='docuser',
        email='docuser@example.com',
        password='SecurePass123!',
        first_name='Doc',
        last_name='Owner',
        tenant=tenant,
        is_active=True,
    )


@pytest.fixture
def document(db, user, client_company):
    doc = Document.objects.create(
        title='Test Document',
        description='A test document.',
        document_type=Document.CONTRACT,
        file=SimpleUploadedFile('contract.pdf', b'%PDF-1.4 content', content_type='application/pdf'),
        uploaded_by=user,
        client=client_company,
        is_public=False,
        tags=['important', 'legal'],
        metadata={'source': 'upload'},
    )
    return doc


@pytest.fixture
def document_no_uploader(db, client_company):
    doc = Document.objects.create(
        title='Orphan Document',
        description='No uploader.',
        document_type=Document.OTHER,
        file=SimpleUploadedFile('orphan.pdf', b'%PDF-1.4', content_type='application/pdf'),
        uploaded_by=None,
        client=client_company,
    )
    return doc


# ---------------------------------------------------------------------------
# DocumentSerializer
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestDocumentSerializer:

    def test_serializes_all_expected_fields(self, document):
        serializer = DocumentSerializer(document)
        data = serializer.data
        expected_fields = [
            'id', 'title', 'description', 'document_type', 'file', 'file_type',
            'file_size', 'uploaded_by', 'uploaded_by_name', 'client', 'contract',
            'invoice', 'processing_status', 'is_public', 'tags', 'metadata',
            'file_extension', 'is_pdf', 'is_image', 'created_at', 'updated_at',
        ]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"

    def test_read_only_fields(self, document):
        serializer = DocumentSerializer(document)
        meta = serializer.Meta
        assert 'id' in meta.read_only_fields
        assert 'file_type' in meta.read_only_fields
        assert 'file_size' in meta.read_only_fields
        assert 'processing_status' in meta.read_only_fields
        assert 'created_at' in meta.read_only_fields
        assert 'updated_at' in meta.read_only_fields

    def test_uploaded_by_name_with_full_name(self, document):
        serializer = DocumentSerializer(document)
        assert serializer.data['uploaded_by_name'] == 'Doc Owner'

    def test_uploaded_by_name_falls_back_to_email(self, document, user):
        user.first_name = ''
        user.last_name = ''
        user.save()
        serializer = DocumentSerializer(document)
        assert serializer.data['uploaded_by_name'] == user.email

    def test_uploaded_by_name_none_when_no_uploader(self, document_no_uploader):
        serializer = DocumentSerializer(document_no_uploader)
        assert serializer.data['uploaded_by_name'] is None

    def test_file_extension_field(self, document):
        serializer = DocumentSerializer(document)
        assert serializer.data['file_extension'] == 'pdf'

    def test_is_pdf_field(self, document):
        serializer = DocumentSerializer(document)
        assert serializer.data['is_pdf'] is True

    def test_is_image_field_false_for_pdf(self, document):
        serializer = DocumentSerializer(document)
        assert serializer.data['is_image'] is False

    def test_title_serialized(self, document):
        serializer = DocumentSerializer(document)
        assert serializer.data['title'] == 'Test Document'

    def test_tags_serialized(self, document):
        serializer = DocumentSerializer(document)
        assert serializer.data['tags'] == ['important', 'legal']

    def test_metadata_serialized(self, document):
        serializer = DocumentSerializer(document)
        assert serializer.data['metadata'] == {'source': 'upload'}


# ---------------------------------------------------------------------------
# DocumentUploadSerializer
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestDocumentUploadSerializer:

    def test_upload_fields(self):
        expected = ['title', 'description', 'document_type', 'file', 'client', 'contract', 'invoice', 'is_public', 'tags']
        assert DocumentUploadSerializer.Meta.fields == expected

    def test_valid_upload_data(self, client_company):
        file = SimpleUploadedFile('test.pdf', b'%PDF-1.4', content_type='application/pdf')
        data = {
            'title': 'Upload Test',
            'document_type': Document.INVOICE,
            'file': file,
            'client': client_company.pk,
        }
        serializer = DocumentUploadSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_title_required(self):
        serializer = DocumentUploadSerializer(data={})
        assert not serializer.is_valid()
        assert 'title' in serializer.errors

    def test_model_is_document(self):
        assert DocumentUploadSerializer.Meta.model is Document
