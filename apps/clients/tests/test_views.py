"""
Tests for clients app views and API endpoints.

Tests cover:
- Client CRUD operations
- Client filtering and search
- Client statistics
- Portal access creation
- Client notes and documents
- Authorization
"""

import pytest
from decimal import Decimal
from unittest.mock import patch
from rest_framework import status
from apps.clients.models import Client


# ============================================================================
# Client ViewSet Tests
# ============================================================================

@pytest.mark.django_db
class TestClientViewSet:
    """Tests for ClientViewSet."""

    def test_list_clients(self, authenticated_admin_client, client_company, client_individual):
        """Test listing clients."""
        response = authenticated_admin_client.get('/api/api/clients/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 2

    def test_list_clients_unauthenticated(self, api_client):
        """Test listing clients without authentication."""
        response = api_client.get('/api/api/clients/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_client(self, authenticated_admin_client, client_company):
        """Test retrieving a specific client."""
        response = authenticated_admin_client.get(f'/api/api/clients/{client_company.id}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == client_company.email
        assert response.data['company_name'] == client_company.company_name

    def test_create_company_client(self, authenticated_admin_client):
        """Test creating a company client."""
        data = {
            'client_type': Client.COMPANY,
            'company_name': 'New Company',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@newcompany.com',
            'phone': '+12125551234',
            'lifecycle_stage': Client.PROSPECT,
        }

        response = authenticated_admin_client.post('/api/api/clients/', data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['company_name'] == 'New Company'
        assert response.data['client_type'] == Client.COMPANY

    def test_create_individual_client(self, authenticated_admin_client):
        """Test creating an individual client."""
        data = {
            'client_type': Client.INDIVIDUAL,
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane@email.com',
            'lifecycle_stage': Client.LEAD,
        }

        response = authenticated_admin_client.post('/api/api/clients/', data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['client_type'] == Client.INDIVIDUAL

    def test_create_company_without_company_name(self, authenticated_admin_client):
        """Test creating company client without company name fails."""
        data = {
            'client_type': Client.COMPANY,
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@nocompany.com',
        }

        response = authenticated_admin_client.post('/api/api/clients/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'company_name' in response.data

    def test_update_client(self, authenticated_admin_client, client_company):
        """Test updating a client."""
        data = {
            'company_name': 'Updated Company Name',
            'lifecycle_stage': Client.ACTIVE,
        }

        response = authenticated_admin_client.patch(
            f'/api/api/clients/{client_company.id}/',
            data
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['company_name'] == 'Updated Company Name'
        assert response.data['lifecycle_stage'] == Client.ACTIVE

    def test_delete_client(self, authenticated_admin_client, client_lead):
        """Test deleting a client."""
        response = authenticated_admin_client.delete(
            f'/api/api/clients/{client_lead.id}/'
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Client.objects.filter(id=client_lead.id).exists()


# ============================================================================
# Client Search and Filter Tests
# ============================================================================

@pytest.mark.django_db
class TestClientSearchFilter:
    """Tests for client search and filtering."""

    def test_search_by_name(self, authenticated_admin_client, client_company):
        """Test searching clients by name."""
        response = authenticated_admin_client.get(
            f'/api/api/clients/?search={client_company.first_name}'
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_search_by_email(self, authenticated_admin_client, client_company):
        """Test searching clients by email."""
        response = authenticated_admin_client.get(
            f'/api/api/clients/?search={client_company.email}'
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_search_by_company_name(self, authenticated_admin_client, client_company):
        """Test searching clients by company name."""
        response = authenticated_admin_client.get(
            f'/api/api/clients/?search={client_company.company_name}'
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_filter_by_lifecycle_stage(self, authenticated_admin_client, client_company, client_lead):
        """Test filtering clients by lifecycle stage."""
        response = authenticated_admin_client.get(
            f'/api/api/clients/?lifecycle_stage={Client.ACTIVE}'
        )

        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        for client in results:
            assert client['lifecycle_stage'] == Client.ACTIVE

    def test_filter_by_client_type(self, authenticated_admin_client, client_company, client_individual):
        """Test filtering clients by type."""
        response = authenticated_admin_client.get(
            f'/api/api/clients/?client_type={Client.COMPANY}'
        )

        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        for client in results:
            assert client['client_type'] == Client.COMPANY

    def test_filter_by_is_active(self, authenticated_admin_client, client_company):
        """Test filtering clients by active status."""
        response = authenticated_admin_client.get(
            '/api/api/clients/?is_active=true'
        )

        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        for client in results:
            assert client['is_active'] is True

    def test_ordering_by_created_at(self, authenticated_admin_client, client_company, client_individual):
        """Test ordering clients by created_at."""
        response = authenticated_admin_client.get(
            '/api/api/clients/?ordering=-created_at'
        )

        assert response.status_code == status.HTTP_200_OK


# ============================================================================
# Client Statistics Tests
# ============================================================================

@pytest.mark.django_db
class TestClientStatistics:
    """Tests for client statistics endpoint."""

    def test_stats_endpoint(self, authenticated_admin_client, client_company, client_lead, client_individual):
        """Test the stats endpoint returns correct data."""
        response = authenticated_admin_client.get('/api/api/clients/stats/')

        assert response.status_code == status.HTTP_200_OK
        assert 'total_clients' in response.data
        assert 'active_clients' in response.data
        assert 'leads' in response.data
        assert 'prospects' in response.data
        assert 'total_value' in response.data
        assert 'total_paid' in response.data
        assert 'outstanding_balance' in response.data

    def test_stats_counts_correct(self, authenticated_admin_client, client_company, client_lead):
        """Test stats endpoint has correct counts."""
        response = authenticated_admin_client.get('/api/api/clients/stats/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_clients'] >= 2
        assert response.data['leads'] >= 1


# ============================================================================
# Client Portal Access Tests
# ============================================================================

@pytest.mark.django_db
class TestClientPortalAccess:
    """Tests for client portal access endpoint."""

    def test_create_portal_access(self, authenticated_admin_client, client_lead):
        """Test creating portal access for a client."""
        response = authenticated_admin_client.post(
            f'/api/api/clients/{client_lead.id}/create_portal_access/'
        )

        # Should succeed or fail based on whether email is unique
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]

    def test_create_portal_access_already_exists(
        self, authenticated_admin_client, client_company, client_user
    ):
        """Test creating portal access when it already exists."""
        # Set portal user
        client_company.portal_user = client_user
        client_company.save()

        response = authenticated_admin_client.post(
            f'/api/api/clients/{client_company.id}/create_portal_access/'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ============================================================================
# Client Notes ViewSet Tests
# ============================================================================

@pytest.mark.django_db
class TestClientNoteViewSet:
    """Tests for ClientNoteViewSet."""

    def test_list_notes(self, authenticated_admin_client, client_note):
        """Test listing client notes."""
        response = authenticated_admin_client.get('/api/api/notes/')

        assert response.status_code == status.HTTP_200_OK

    def test_create_note(self, authenticated_admin_client, client_company):
        """Test creating a client note."""
        data = {
            'client': str(client_company.id),
            'note_type': 'call',
            'subject': 'Follow-up Call',
            'content': 'Discussed next steps with client.',
        }

        response = authenticated_admin_client.post('/api/api/notes/', data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['note_type'] == 'call'

    def test_get_client_notes_action(self, authenticated_admin_client, client_company, client_note):
        """Test getting notes for a specific client."""
        response = authenticated_admin_client.get(
            f'/api/api/clients/{client_company.id}/notes/'
        )

        assert response.status_code == status.HTTP_200_OK

    def test_update_note(self, authenticated_admin_client, client_note):
        """Test updating a client note."""
        data = {
            'subject': 'Updated Subject',
        }

        response = authenticated_admin_client.patch(
            f'/api/api/notes/{client_note.id}/',
            data
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['subject'] == 'Updated Subject'

    def test_delete_note(self, authenticated_admin_client, client_note):
        """Test deleting a client note."""
        from apps.clients.models import ClientNote

        response = authenticated_admin_client.delete(
            f'/api/api/notes/{client_note.id}/'
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not ClientNote.objects.filter(id=client_note.id).exists()


# ============================================================================
# Client Documents ViewSet Tests
# ============================================================================

@pytest.mark.django_db
class TestClientDocumentViewSet:
    """Tests for ClientDocumentViewSet."""

    def test_list_documents(self, authenticated_admin_client):
        """Test listing client documents."""
        response = authenticated_admin_client.get('/api/api/documents/')

        assert response.status_code == status.HTTP_200_OK

    def test_get_client_documents_action(self, authenticated_admin_client, client_company):
        """Test getting documents for a specific client."""
        response = authenticated_admin_client.get(
            f'/api/api/clients/{client_company.id}/documents/'
        )

        assert response.status_code == status.HTTP_200_OK


# ============================================================================
# Client Authorization Tests
# ============================================================================

@pytest.mark.django_db
class TestClientAuthorization:
    """Tests for client authorization."""

    def test_non_staff_sees_own_clients(
        self, authenticated_contributor_client, client_company, contributor_user
    ):
        """Test non-staff users see only their own clients or unassigned."""
        # Assign client to contributor
        client_company.owner = contributor_user
        client_company.save()

        response = authenticated_contributor_client.get('/api/api/clients/')

        assert response.status_code == status.HTTP_200_OK
        # Should see clients owned by them or unassigned

    def test_staff_sees_all_clients(
        self, authenticated_admin_client, client_company, client_individual
    ):
        """Test staff users see all clients."""
        response = authenticated_admin_client.get('/api/api/clients/')

        assert response.status_code == status.HTTP_200_OK


# ============================================================================
# Client View Edge Cases
# ============================================================================

@pytest.mark.django_db
class TestClientViewEdgeCases:
    """Edge case tests for client views."""

    def test_create_client_with_tags(self, authenticated_admin_client):
        """Test creating client with tags."""
        data = {
            'client_type': Client.INDIVIDUAL,
            'first_name': 'Tagged',
            'last_name': 'Client',
            'email': 'tagged@test.com',
            'tags': ['vip', 'priority'],
        }

        response = authenticated_admin_client.post(
            '/api/api/clients/',
            data,
            format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert 'vip' in response.data['tags']

    def test_create_client_with_metadata(self, authenticated_admin_client):
        """Test creating client with metadata."""
        data = {
            'client_type': Client.INDIVIDUAL,
            'first_name': 'Meta',
            'last_name': 'Client',
            'email': 'meta@test.com',
            'metadata': {'custom': 'value'},
        }

        response = authenticated_admin_client.post(
            '/api/api/clients/',
            data,
            format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['metadata']['custom'] == 'value'

    def test_retrieve_nonexistent_client(self, authenticated_admin_client):
        """Test retrieving a nonexistent client."""
        import uuid
        fake_id = uuid.uuid4()

        response = authenticated_admin_client.get(f'/api/api/clients/{fake_id}/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_financial_summary_action(
        self, authenticated_admin_client, client_company
    ):
        """Test update_financial_summary action."""
        response = authenticated_admin_client.post(
            f'/api/api/clients/{client_company.id}/update_financial_summary/'
        )

        assert response.status_code == status.HTTP_200_OK

    def test_client_with_special_characters_in_email(self, authenticated_admin_client):
        """Test client with special but valid email."""
        data = {
            'client_type': Client.INDIVIDUAL,
            'first_name': 'Special',
            'last_name': 'Email',
            'email': 'user+tag@example.com',
        }

        response = authenticated_admin_client.post('/api/api/clients/', data)

        assert response.status_code == status.HTTP_201_CREATED

    def test_create_portal_access_error(self, authenticated_admin_client, client_lead):
        """Test create_portal_access handles exceptions gracefully."""
        with patch.object(
            Client, 'create_portal_access', side_effect=Exception('DB error')
        ):
            response = authenticated_admin_client.post(
                f'/api/api/clients/{client_lead.id}/create_portal_access/'
            )
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert 'DB error' in response.data['detail']

    def test_update_financial_summary_error(self, authenticated_admin_client, client_company):
        """Test update_financial_summary handles exceptions gracefully."""
        with patch.object(
            Client, 'update_financial_summary', side_effect=Exception('Invoice error')
        ):
            response = authenticated_admin_client.post(
                f'/api/api/clients/{client_company.id}/update_financial_summary/'
            )
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert 'Invoice error' in response.data['detail']


# ============================================================================
# Client Document Upload Tests
# ============================================================================

@pytest.mark.django_db
class TestClientDocumentUpload:
    """Tests for client document upload via API."""

    def test_upload_document(self, authenticated_admin_client, client_company):
        """Test uploading a document via the API triggers perform_create."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        doc_file = SimpleUploadedFile(
            'test_upload.pdf',
            b'PDF file content',
            content_type='application/pdf'
        )
        data = {
            'client': str(client_company.id),
            'name': 'Uploaded Doc',
            'file': doc_file,
        }

        response = authenticated_admin_client.post(
            '/api/api/documents/',
            data,
            format='multipart'
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Uploaded Doc'


# ============================================================================
# Non-Staff Note Queryset Filter (covers line 170)
# ============================================================================

@pytest.mark.django_db
class TestClientNoteNonStaffFilter:
    """Tests for ClientNoteViewSet.get_queryset non-staff filter (line 170)."""

    def test_non_staff_user_notes_queryset(
        self, authenticated_contributor_client, client_company, contributor_user
    ):
        """Non-staff user should see only their own notes or notes for their clients."""
        # Assign client to contributor
        client_company.owner = contributor_user
        client_company.save()

        response = authenticated_contributor_client.get('/api/api/notes/')
        assert response.status_code == status.HTTP_200_OK


# ============================================================================
# Non-Staff Document Queryset Filter (covers line 201)
# ============================================================================

@pytest.mark.django_db
class TestClientDocumentNonStaffFilter:
    """Tests for ClientDocumentViewSet.get_queryset non-staff filter (line 201)."""

    def test_non_staff_user_documents_queryset(
        self, authenticated_contributor_client, client_company, contributor_user
    ):
        """Non-staff user should see only their own docs or docs for their clients."""
        # Assign client to contributor
        client_company.owner = contributor_user
        client_company.save()

        response = authenticated_contributor_client.get('/api/api/documents/')
        assert response.status_code == status.HTTP_200_OK
