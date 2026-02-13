"""
Tests for clients app serializers.
"""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, PropertyMock
from rest_framework.test import APIRequestFactory
from apps.clients.serializers import (
    ClientListSerializer,
    ClientDetailSerializer,
    ClientCreateUpdateSerializer,
    ClientNoteSerializer,
    ClientDocumentSerializer,
    ClientStatsSerializer,
)
from apps.clients.models import Client, ClientNote, ClientDocument


factory = APIRequestFactory()


# ============================================================================
# ClientListSerializer Tests
# ============================================================================

class TestClientListSerializer:
    """Tests for ClientListSerializer."""

    @pytest.mark.django_db
    def test_serializes_expected_fields(self, client_company):
        """Verify all expected fields are present in the serialized output."""
        serializer = ClientListSerializer(client_company)
        data = serializer.data
        expected_fields = [
            'id', 'client_type', 'company_name', 'first_name', 'last_name',
            'email', 'phone', 'lifecycle_stage', 'total_value', 'total_paid',
            'outstanding_balance', 'owner', 'owner_name', 'is_active',
            'created_at', 'updated_at',
        ]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"

    @pytest.mark.django_db
    def test_owner_name_with_owner(self, client_company):
        """Test get_owner_name returns full name when owner exists."""
        serializer = ClientListSerializer(client_company)
        assert serializer.data['owner_name'] == 'Admin User'

    @pytest.mark.django_db
    def test_owner_name_without_owner(self, client_lead):
        """Test get_owner_name returns None when no owner."""
        serializer = ClientListSerializer(client_lead)
        assert serializer.data['owner_name'] is None

    @pytest.mark.django_db
    def test_read_only_fields(self):
        """Verify read_only_fields are correctly set."""
        meta = ClientListSerializer.Meta
        assert 'id' in meta.read_only_fields
        assert 'created_at' in meta.read_only_fields
        assert 'updated_at' in meta.read_only_fields


# ============================================================================
# ClientDetailSerializer Tests
# ============================================================================

class TestClientDetailSerializer:
    """Tests for ClientDetailSerializer."""

    @pytest.mark.django_db
    def test_serializes_all_fields(self, client_company):
        """Verify detail serializer includes all model fields."""
        serializer = ClientDetailSerializer(client_company)
        data = serializer.data
        # Should include computed fields
        assert 'owner_name' in data
        assert 'portal_user_email' in data
        assert 'display_name' in data
        assert 'full_name' in data
        assert 'payment_status' in data

    @pytest.mark.django_db
    def test_owner_name_with_owner(self, client_company):
        """Test get_owner_name with owner."""
        serializer = ClientDetailSerializer(client_company)
        assert serializer.data['owner_name'] == 'Admin User'

    @pytest.mark.django_db
    def test_owner_name_without_owner(self, client_lead):
        """Test get_owner_name without owner returns None."""
        serializer = ClientDetailSerializer(client_lead)
        assert serializer.data['owner_name'] is None

    @pytest.mark.django_db
    def test_portal_user_email_with_portal_user(self, client_company, client_user):
        """Test get_portal_user_email returns email when portal user exists."""
        client_company.portal_user = client_user
        client_company.save()
        serializer = ClientDetailSerializer(client_company)
        assert serializer.data['portal_user_email'] == client_user.email

    @pytest.mark.django_db
    def test_portal_user_email_without_portal_user(self, client_company):
        """Test get_portal_user_email returns None when no portal user."""
        serializer = ClientDetailSerializer(client_company)
        assert serializer.data['portal_user_email'] is None

    @pytest.mark.django_db
    def test_display_name_company(self, client_company):
        """Test display name for company client returns company name."""
        serializer = ClientDetailSerializer(client_company)
        assert serializer.data['display_name'] == 'Test Company Inc.'

    @pytest.mark.django_db
    def test_display_name_individual(self, client_individual):
        """Test display name for individual returns full name."""
        serializer = ClientDetailSerializer(client_individual)
        assert serializer.data['display_name'] == 'Jane Smith'

    @pytest.mark.django_db
    def test_full_name(self, client_company):
        """Test full_name field."""
        serializer = ClientDetailSerializer(client_company)
        assert serializer.data['full_name'] == 'John Doe'

    @pytest.mark.django_db
    def test_payment_status_no_transactions(self, client_lead):
        """Test payment_status when there are no transactions."""
        serializer = ClientDetailSerializer(client_lead)
        assert serializer.data['payment_status'] == 'no_transactions'

    @pytest.mark.django_db
    def test_payment_status_outstanding(self, client_company):
        """Test payment_status when balance is outstanding."""
        client_company.outstanding_balance = Decimal('1000.00')
        client_company.save()
        serializer = ClientDetailSerializer(client_company)
        assert serializer.data['payment_status'] == 'outstanding'

    @pytest.mark.django_db
    def test_payment_status_paid_up(self, client_company):
        """Test payment_status when everything is paid."""
        client_company.total_paid = Decimal('5000.00')
        client_company.outstanding_balance = Decimal('0.00')
        client_company.save()
        serializer = ClientDetailSerializer(client_company)
        assert serializer.data['payment_status'] == 'paid_up'

    @pytest.mark.django_db
    def test_read_only_fields(self):
        """Verify read_only_fields are correctly configured."""
        meta = ClientDetailSerializer.Meta
        assert 'id' in meta.read_only_fields
        assert 'created_at' in meta.read_only_fields
        assert 'updated_at' in meta.read_only_fields
        assert 'total_value' in meta.read_only_fields
        assert 'total_paid' in meta.read_only_fields
        assert 'outstanding_balance' in meta.read_only_fields


# ============================================================================
# ClientCreateUpdateSerializer Tests
# ============================================================================

class TestClientCreateUpdateSerializer:
    """Tests for ClientCreateUpdateSerializer."""

    @pytest.mark.django_db
    def test_valid_individual_client_data(self, admin_user):
        """Test serializer validates valid individual client data."""
        data = {
            'client_type': Client.INDIVIDUAL,
            'first_name': 'Alice',
            'last_name': 'Wonderland',
            'email': 'alice@example.com',
            'lifecycle_stage': Client.LEAD,
        }
        serializer = ClientCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    @pytest.mark.django_db
    def test_valid_company_client_data(self, admin_user):
        """Test serializer validates valid company client data."""
        data = {
            'client_type': Client.COMPANY,
            'company_name': 'Acme Corp',
            'first_name': 'Bob',
            'last_name': 'Builder',
            'email': 'bob@acme.com',
            'lifecycle_stage': Client.ACTIVE,
        }
        serializer = ClientCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    @pytest.mark.django_db
    def test_company_type_without_company_name_is_invalid(self):
        """Test that company type requires company_name."""
        data = {
            'client_type': Client.COMPANY,
            'first_name': 'Missing',
            'last_name': 'CompanyName',
            'email': 'missing@company.com',
            'lifecycle_stage': Client.LEAD,
        }
        serializer = ClientCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'company_name' in serializer.errors

    @pytest.mark.django_db
    def test_company_type_with_empty_company_name_is_invalid(self):
        """Test that company type with empty company_name fails validation."""
        data = {
            'client_type': Client.COMPANY,
            'company_name': '',
            'first_name': 'Empty',
            'last_name': 'CompanyName',
            'email': 'empty@company.com',
            'lifecycle_stage': Client.LEAD,
        }
        serializer = ClientCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'company_name' in serializer.errors

    @pytest.mark.django_db
    def test_individual_type_without_company_name_is_valid(self):
        """Test individual type does not require company_name."""
        data = {
            'client_type': Client.INDIVIDUAL,
            'first_name': 'Solo',
            'last_name': 'Person',
            'email': 'solo@individual.com',
            'lifecycle_stage': Client.LEAD,
        }
        serializer = ClientCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    @pytest.mark.django_db
    def test_create_client(self, admin_user):
        """Test creating a client through serializer."""
        data = {
            'client_type': Client.INDIVIDUAL,
            'first_name': 'New',
            'last_name': 'Client',
            'email': 'new.client@example.com',
            'lifecycle_stage': Client.LEAD,
            'is_active': True,
        }
        serializer = ClientCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        client = serializer.save()
        assert client.pk is not None
        assert client.first_name == 'New'
        assert client.last_name == 'Client'

    @pytest.mark.django_db
    def test_update_client(self, client_individual):
        """Test updating a client through serializer."""
        data = {
            'client_type': Client.INDIVIDUAL,
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.com',
            'lifecycle_stage': Client.ACTIVE,
        }
        serializer = ClientCreateUpdateSerializer(client_individual, data=data)
        assert serializer.is_valid(), serializer.errors
        client = serializer.save()
        assert client.first_name == 'Updated'
        assert client.lifecycle_stage == Client.ACTIVE

    @pytest.mark.django_db
    def test_fields_are_correct(self):
        """Test that the serializer has all expected fields."""
        expected_fields = [
            'id', 'client_type', 'company_name', 'first_name', 'last_name',
            'email', 'phone', 'secondary_email', 'secondary_phone', 'website',
            'address_line1', 'address_line2', 'city', 'state', 'postal_code',
            'country', 'industry', 'company_size', 'annual_revenue', 'tax_id',
            'lifecycle_stage', 'source', 'tags', 'owner', 'portal_access_enabled',
            'notes', 'is_active', 'metadata',
        ]
        meta = ClientCreateUpdateSerializer.Meta
        assert meta.fields == expected_fields

    @pytest.mark.django_db
    def test_partial_update(self, client_company):
        """Test partial update only modifies provided fields."""
        data = {'first_name': 'PartiallyUpdated'}
        serializer = ClientCreateUpdateSerializer(
            client_company, data=data, partial=True
        )
        assert serializer.is_valid(), serializer.errors
        client = serializer.save()
        assert client.first_name == 'PartiallyUpdated'
        # Other fields remain unchanged
        assert client.company_name == 'Test Company Inc.'


# ============================================================================
# ClientNoteSerializer Tests
# ============================================================================

class TestClientNoteSerializer:
    """Tests for ClientNoteSerializer."""

    @pytest.mark.django_db
    def test_serializes_expected_fields(self, client_note):
        """Test serialization of client note."""
        serializer = ClientNoteSerializer(client_note)
        data = serializer.data
        assert 'id' in data
        assert 'client' in data
        assert 'author' in data
        assert 'author_name' in data
        assert 'note_type' in data
        assert 'subject' in data
        assert 'content' in data
        assert 'created_at' in data
        assert 'updated_at' in data

    @pytest.mark.django_db
    def test_author_name(self, client_note):
        """Test get_author_name returns correct name."""
        serializer = ClientNoteSerializer(client_note)
        assert serializer.data['author_name'] == 'Admin User'

    @pytest.mark.django_db
    def test_create_sets_author_from_context(self, client_company, admin_user):
        """Test that create sets the author from request context."""
        request = factory.post('/api/notes/')
        request.user = admin_user
        data = {
            'client': str(client_company.id),
            'note_type': 'general',
            'subject': 'Test Note',
            'content': 'This is a test note.',
        }
        serializer = ClientNoteSerializer(data=data, context={'request': request})
        assert serializer.is_valid(), serializer.errors
        note = serializer.save()
        assert note.author == admin_user

    @pytest.mark.django_db
    def test_read_only_fields(self):
        """Verify read_only_fields."""
        meta = ClientNoteSerializer.Meta
        assert 'id' in meta.read_only_fields
        assert 'author' in meta.read_only_fields
        assert 'created_at' in meta.read_only_fields
        assert 'updated_at' in meta.read_only_fields


# ============================================================================
# ClientDocumentSerializer Tests
# ============================================================================

class TestClientDocumentSerializer:
    """Tests for ClientDocumentSerializer."""

    @pytest.mark.django_db
    def test_serializes_expected_fields(self, client_company, admin_user):
        """Test serialization includes computed fields."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        test_file = SimpleUploadedFile(
            "test_doc.txt", b"file content here", content_type="text/plain"
        )
        doc = ClientDocument.objects.create(
            client=client_company,
            name='Test Document',
            file=test_file,
            file_type='text/plain',
            uploaded_by=admin_user,
        )
        serializer = ClientDocumentSerializer(doc)
        data = serializer.data
        assert 'uploaded_by_name' in data
        assert 'file_url' in data
        assert data['uploaded_by_name'] == 'Admin User'

    @pytest.mark.django_db
    def test_file_url_with_request_context(self, client_company, admin_user):
        """Test file_url uses request to build absolute URI."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        test_file = SimpleUploadedFile(
            "test_doc.txt", b"content", content_type="text/plain"
        )
        doc = ClientDocument.objects.create(
            client=client_company,
            name='Test Doc',
            file=test_file,
            file_type='text/plain',
            uploaded_by=admin_user,
        )
        request = factory.get('/api/documents/')
        serializer = ClientDocumentSerializer(doc, context={'request': request})
        data = serializer.data
        assert data['file_url'] is not None
        assert 'http' in data['file_url']

    @pytest.mark.django_db
    def test_file_url_without_request_context(self, client_company, admin_user):
        """Test file_url returns relative URL without request context."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        test_file = SimpleUploadedFile(
            "test_doc.txt", b"content", content_type="text/plain"
        )
        doc = ClientDocument.objects.create(
            client=client_company,
            name='Test Doc',
            file=test_file,
            file_type='text/plain',
            uploaded_by=admin_user,
        )
        serializer = ClientDocumentSerializer(doc)
        data = serializer.data
        assert data['file_url'] is not None

    @pytest.mark.django_db
    def test_file_url_without_file(self, client_company, admin_user):
        """Test file_url returns None when no file is attached."""
        doc = ClientDocument(
            client=client_company,
            name='Empty Doc',
            uploaded_by=admin_user,
        )
        # Don't save (file is required), just test serializer method directly
        serializer = ClientDocumentSerializer(doc)
        result = serializer.get_file_url(doc)
        assert result is None

    @pytest.mark.django_db
    def test_create_sets_uploaded_by_from_context(self, client_company, admin_user):
        """Test that create sets uploaded_by from request context."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        request = factory.post('/api/documents/')
        request.user = admin_user
        test_file = SimpleUploadedFile(
            "upload.txt", b"content", content_type="text/plain"
        )
        data = {
            'client': str(client_company.id),
            'name': 'Uploaded Document',
            'file': test_file,
            'file_type': 'text/plain',
        }
        serializer = ClientDocumentSerializer(data=data, context={'request': request})
        assert serializer.is_valid(), serializer.errors
        doc = serializer.save()
        assert doc.uploaded_by == admin_user

    @pytest.mark.django_db
    def test_read_only_fields(self):
        """Verify read_only_fields."""
        meta = ClientDocumentSerializer.Meta
        assert 'id' in meta.read_only_fields
        assert 'uploaded_by' in meta.read_only_fields
        assert 'file_size' in meta.read_only_fields
        assert 'file_type' in meta.read_only_fields
        assert 'created_at' in meta.read_only_fields


# ============================================================================
# ClientStatsSerializer Tests
# ============================================================================

class TestClientStatsSerializer:
    """Tests for ClientStatsSerializer."""

    def test_serializes_stats_data(self):
        """Test that stats data is serialized correctly."""
        stats = {
            'total_clients': 50,
            'active_clients': 30,
            'leads': 10,
            'prospects': 10,
            'total_value': Decimal('100000.00'),
            'total_paid': Decimal('75000.00'),
            'outstanding_balance': Decimal('25000.00'),
        }
        serializer = ClientStatsSerializer(stats)
        data = serializer.data
        assert data['total_clients'] == 50
        assert data['active_clients'] == 30
        assert data['leads'] == 10
        assert data['prospects'] == 10
        assert Decimal(data['total_value']) == Decimal('100000.00')
        assert Decimal(data['total_paid']) == Decimal('75000.00')
        assert Decimal(data['outstanding_balance']) == Decimal('25000.00')

    def test_validates_integer_fields(self):
        """Test that integer fields require integers."""
        stats = {
            'total_clients': 'not_a_number',
            'active_clients': 5,
            'leads': 3,
            'prospects': 2,
            'total_value': Decimal('1000.00'),
            'total_paid': Decimal('500.00'),
            'outstanding_balance': Decimal('500.00'),
        }
        serializer = ClientStatsSerializer(data=stats)
        assert not serializer.is_valid()
        assert 'total_clients' in serializer.errors

    def test_zero_values(self):
        """Test serialization with zero values."""
        stats = {
            'total_clients': 0,
            'active_clients': 0,
            'leads': 0,
            'prospects': 0,
            'total_value': Decimal('0.00'),
            'total_paid': Decimal('0.00'),
            'outstanding_balance': Decimal('0.00'),
        }
        serializer = ClientStatsSerializer(stats)
        data = serializer.data
        assert data['total_clients'] == 0
        assert Decimal(data['total_value']) == Decimal('0.00')
