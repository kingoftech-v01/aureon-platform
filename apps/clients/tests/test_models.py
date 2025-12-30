"""
Tests for clients app models.

Tests cover:
- Client model creation and validation
- Client properties and methods
- ClientNote model
- ClientDocument model
"""

import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from apps.clients.models import Client, ClientNote, ClientDocument


# ============================================================================
# Client Model Tests
# ============================================================================

@pytest.mark.django_db
class TestClientModel:
    """Tests for the Client model."""

    def test_create_company_client(self, admin_user):
        """Test creating a company client."""
        client = Client.objects.create(
            client_type=Client.COMPANY,
            company_name='Test Company Inc.',
            first_name='John',
            last_name='Doe',
            email='john@testcompany.com',
            owner=admin_user,
        )

        assert client.client_type == Client.COMPANY
        assert client.company_name == 'Test Company Inc.'
        assert client.is_company is True

    def test_create_individual_client(self, admin_user):
        """Test creating an individual client."""
        client = Client.objects.create(
            client_type=Client.INDIVIDUAL,
            first_name='Jane',
            last_name='Smith',
            email='jane@email.com',
            owner=admin_user,
        )

        assert client.client_type == Client.INDIVIDUAL
        assert client.is_company is False

    def test_client_string_representation_company(self, client_company):
        """Test company client string representation."""
        expected = f"{client_company.company_name} ({client_company.get_full_name()})"
        assert str(client_company) == expected

    def test_client_string_representation_individual(self, client_individual):
        """Test individual client string representation."""
        assert str(client_individual) == client_individual.get_full_name()

    def test_get_full_name(self, client_company):
        """Test get_full_name method."""
        expected = f"{client_company.first_name} {client_company.last_name}"
        assert client_company.get_full_name() == expected

    def test_get_display_name_company(self, client_company):
        """Test get_display_name for company client."""
        assert client_company.get_display_name() == client_company.company_name

    def test_get_display_name_individual(self, client_individual):
        """Test get_display_name for individual client."""
        assert client_individual.get_display_name() == client_individual.get_full_name()

    def test_client_uuid_primary_key(self, client_company):
        """Test that client has UUID primary key."""
        import uuid
        assert isinstance(client_company.id, uuid.UUID)

    def test_client_lifecycle_stages(self):
        """Test all lifecycle stages are valid."""
        valid_stages = [
            Client.LEAD,
            Client.PROSPECT,
            Client.ACTIVE,
            Client.INACTIVE,
            Client.CHURNED,
        ]
        for stage in valid_stages:
            assert stage in dict(Client.STAGE_CHOICES)

    def test_client_types(self):
        """Test all client types are valid."""
        valid_types = [Client.INDIVIDUAL, Client.COMPANY]
        for client_type in valid_types:
            assert client_type in dict(Client.TYPE_CHOICES)


# ============================================================================
# Client Payment Status Tests
# ============================================================================

@pytest.mark.django_db
class TestClientPaymentStatus:
    """Tests for client payment status property."""

    def test_payment_status_outstanding(self, client_company):
        """Test payment status when there's outstanding balance."""
        client_company.outstanding_balance = Decimal('1000.00')
        client_company.save()

        assert client_company.payment_status == 'outstanding'

    def test_payment_status_paid_up(self, client_company):
        """Test payment status when client is paid up."""
        client_company.outstanding_balance = Decimal('0.00')
        client_company.total_paid = Decimal('5000.00')
        client_company.save()

        assert client_company.payment_status == 'paid_up'

    def test_payment_status_no_transactions(self, client_lead):
        """Test payment status with no transactions."""
        assert client_lead.outstanding_balance == Decimal('0.00')
        assert client_lead.total_paid == Decimal('0.00')
        assert client_lead.payment_status == 'no_transactions'


# ============================================================================
# Client Financial Summary Tests
# ============================================================================

@pytest.mark.django_db
class TestClientFinancialSummary:
    """Tests for client financial summary fields."""

    def test_total_value_default(self, client_lead):
        """Test total_value default is 0."""
        assert client_lead.total_value == Decimal('0')

    def test_total_paid_default(self, client_lead):
        """Test total_paid default is 0."""
        assert client_lead.total_paid == Decimal('0')

    def test_outstanding_balance_default(self, client_lead):
        """Test outstanding_balance default is 0."""
        assert client_lead.outstanding_balance == Decimal('0')

    def test_financial_summary_update(self, client_company):
        """Test updating financial summary."""
        client_company.total_value = Decimal('10000.00')
        client_company.total_paid = Decimal('7500.00')
        client_company.outstanding_balance = Decimal('2500.00')
        client_company.save()

        client_company.refresh_from_db()
        assert client_company.total_value == Decimal('10000.00')
        assert client_company.total_paid == Decimal('7500.00')
        assert client_company.outstanding_balance == Decimal('2500.00')


# ============================================================================
# Client Portal Access Tests
# ============================================================================

@pytest.mark.django_db
class TestClientPortalAccess:
    """Tests for client portal access."""

    def test_portal_access_enabled_default(self, client_company):
        """Test portal_access_enabled is True by default."""
        assert client_company.portal_access_enabled is True

    def test_portal_user_null_by_default(self, client_lead):
        """Test portal_user is null by default."""
        assert client_lead.portal_user is None

    def test_create_portal_access(self, client_lead):
        """Test creating portal access for client."""
        # Skip if user with this email already exists
        from django.contrib.auth import get_user_model
        User = get_user_model()

        if not User.objects.filter(email=client_lead.email).exists():
            user = client_lead.create_portal_access()

            assert user is not None
            assert user.email == client_lead.email
            assert user.role == User.CLIENT
            assert client_lead.portal_user == user

    def test_create_portal_access_returns_existing(self, client_company, client_user):
        """Test create_portal_access returns existing user."""
        client_company.portal_user = client_user
        client_company.save()

        result = client_company.create_portal_access()

        assert result == client_user


# ============================================================================
# Client Tags Tests
# ============================================================================

@pytest.mark.django_db
class TestClientTags:
    """Tests for client tags field."""

    def test_tags_default_empty_list(self, admin_user):
        """Test tags default to empty list."""
        client = Client.objects.create(
            client_type=Client.INDIVIDUAL,
            first_name='Test',
            last_name='User',
            email='testtags@email.com',
            owner=admin_user,
        )
        assert client.tags == []

    def test_tags_array_field(self, client_company):
        """Test tags as array field."""
        assert isinstance(client_company.tags, list)
        assert 'enterprise' in client_company.tags
        assert 'priority' in client_company.tags

    def test_add_tags(self, client_individual):
        """Test adding tags to client."""
        client_individual.tags = ['new-tag', 'vip']
        client_individual.save()

        client_individual.refresh_from_db()
        assert 'new-tag' in client_individual.tags
        assert 'vip' in client_individual.tags


# ============================================================================
# Client Metadata Tests
# ============================================================================

@pytest.mark.django_db
class TestClientMetadata:
    """Tests for client metadata JSON field."""

    def test_metadata_default_empty_dict(self, admin_user):
        """Test metadata defaults to empty dict."""
        client = Client.objects.create(
            client_type=Client.INDIVIDUAL,
            first_name='Test',
            last_name='Meta',
            email='testmeta@email.com',
            owner=admin_user,
        )
        assert client.metadata == {}

    def test_metadata_stores_json(self, client_company):
        """Test metadata can store JSON data."""
        client_company.metadata = {
            'custom_field': 'value',
            'nested': {'key': 'nested_value'},
            'numbers': [1, 2, 3],
        }
        client_company.save()

        client_company.refresh_from_db()
        assert client_company.metadata['custom_field'] == 'value'
        assert client_company.metadata['nested']['key'] == 'nested_value'


# ============================================================================
# ClientNote Model Tests
# ============================================================================

@pytest.mark.django_db
class TestClientNoteModel:
    """Tests for the ClientNote model."""

    def test_create_client_note(self, client_company, admin_user):
        """Test creating a client note."""
        note = ClientNote.objects.create(
            client=client_company,
            author=admin_user,
            note_type='general',
            subject='Test Note',
            content='This is a test note content.',
        )

        assert note.client == client_company
        assert note.author == admin_user
        assert note.note_type == 'general'

    def test_note_string_representation(self, client_note):
        """Test note string representation."""
        assert str(client_note).startswith(f"Note for {client_note.client}")

    def test_note_types(self, client_company, admin_user):
        """Test all note types are valid."""
        valid_types = ['general', 'call', 'meeting', 'email', 'task']

        for note_type in valid_types:
            note = ClientNote.objects.create(
                client=client_company,
                author=admin_user,
                note_type=note_type,
                content=f'Content for {note_type}',
            )
            assert note.note_type == note_type

    def test_note_timestamps(self, client_note):
        """Test note has created_at and updated_at."""
        assert client_note.created_at is not None
        assert client_note.updated_at is not None

    def test_note_uuid_primary_key(self, client_note):
        """Test note has UUID primary key."""
        import uuid
        assert isinstance(client_note.id, uuid.UUID)


# ============================================================================
# ClientDocument Model Tests
# ============================================================================

@pytest.mark.django_db
class TestClientDocumentModel:
    """Tests for the ClientDocument model."""

    def test_create_client_document(self, client_company, admin_user):
        """Test creating a client document."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        file = SimpleUploadedFile(
            'test.pdf',
            b'PDF content here',
            content_type='application/pdf'
        )

        doc = ClientDocument.objects.create(
            client=client_company,
            name='Test Document',
            file=file,
            file_type='application/pdf',
            description='A test document',
            uploaded_by=admin_user,
        )

        assert doc.client == client_company
        assert doc.name == 'Test Document'
        assert doc.uploaded_by == admin_user

    def test_document_string_representation(self, client_company, admin_user):
        """Test document string representation."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        file = SimpleUploadedFile('doc.pdf', b'content')
        doc = ClientDocument.objects.create(
            client=client_company,
            name='My Doc',
            file=file,
            uploaded_by=admin_user,
        )

        assert str(doc) == f"My Doc - {client_company}"

    def test_document_file_size_auto_set(self, client_company, admin_user):
        """Test file size is auto-set on save."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        content = b'PDF content here - testing file size'
        file = SimpleUploadedFile('size.pdf', content)

        doc = ClientDocument.objects.create(
            client=client_company,
            name='Size Test',
            file=file,
            uploaded_by=admin_user,
        )

        assert doc.file_size == len(content)


# ============================================================================
# Client Model Edge Cases
# ============================================================================

@pytest.mark.django_db
class TestClientModelEdgeCases:
    """Edge case tests for Client model."""

    def test_client_without_owner(self):
        """Test client can be created without owner."""
        client = Client.objects.create(
            client_type=Client.INDIVIDUAL,
            first_name='No',
            last_name='Owner',
            email='noowner@test.com',
        )

        assert client.owner is None

    def test_client_with_all_address_fields(self, admin_user):
        """Test client with complete address."""
        client = Client.objects.create(
            client_type=Client.COMPANY,
            company_name='Full Address Inc.',
            first_name='Address',
            last_name='Test',
            email='address@test.com',
            address_line1='123 Main St',
            address_line2='Suite 100',
            city='San Francisco',
            state='California',
            postal_code='94102',
            country='United States',
            owner=admin_user,
        )

        assert client.address_line1 == '123 Main St'
        assert client.city == 'San Francisco'

    def test_client_with_secondary_contacts(self, admin_user):
        """Test client with secondary email and phone."""
        client = Client.objects.create(
            client_type=Client.COMPANY,
            company_name='Secondary Contact Inc.',
            first_name='Primary',
            last_name='Contact',
            email='primary@company.com',
            secondary_email='secondary@company.com',
            owner=admin_user,
        )

        assert client.secondary_email == 'secondary@company.com'

    def test_client_annual_revenue(self, client_company):
        """Test client annual revenue field."""
        client_company.annual_revenue = Decimal('1000000.00')
        client_company.save()

        client_company.refresh_from_db()
        assert client_company.annual_revenue == Decimal('1000000.00')

    def test_client_tax_id(self, client_company):
        """Test client tax ID field."""
        client_company.tax_id = 'US123456789'
        client_company.save()

        client_company.refresh_from_db()
        assert client_company.tax_id == 'US123456789'

    def test_client_source_field(self, client_company):
        """Test client source/lead source field."""
        assert client_company.source == 'Website'

    def test_client_industry_field(self, client_company):
        """Test client industry field."""
        assert client_company.industry == 'Technology'

    def test_client_company_size_field(self, client_company):
        """Test client company_size field."""
        assert client_company.company_size == '11-50'

    def test_client_notes_field(self, admin_user):
        """Test client notes text field."""
        client = Client.objects.create(
            client_type=Client.INDIVIDUAL,
            first_name='Notes',
            last_name='Test',
            email='notes@test.com',
            notes='This is an important client. Handle with care.',
            owner=admin_user,
        )

        assert 'important client' in client.notes

    def test_inactive_client(self, client_company):
        """Test marking client as inactive."""
        client_company.is_active = False
        client_company.save()

        client_company.refresh_from_db()
        assert client_company.is_active is False
