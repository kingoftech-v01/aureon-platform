"""
Tests for clients app URL configuration.
"""

import pytest
from django.urls import reverse, resolve
from apps.clients.views import ClientViewSet, ClientNoteViewSet, ClientDocumentViewSet


class TestClientURLs:
    """Tests for client URL resolution."""

    def test_client_list_url_resolves(self):
        """Test client-list URL resolves to ClientViewSet."""
        url = reverse('clients:client-list')
        assert url == '/api/clients/'
        resolver = resolve(url)
        assert resolver.func.cls == ClientViewSet

    def test_client_detail_url_resolves(self):
        """Test client-detail URL resolves correctly."""
        import uuid
        pk = uuid.uuid4()
        url = reverse('clients:client-detail', kwargs={'pk': pk})
        assert f'/api/clients/{pk}/' in url
        resolver = resolve(url)
        assert resolver.func.cls == ClientViewSet

    def test_client_stats_url_resolves(self):
        """Test client stats action URL resolves."""
        url = reverse('clients:client-stats')
        assert '/api/clients/stats/' in url
        resolver = resolve(url)
        assert resolver.func.cls == ClientViewSet

    def test_client_create_portal_access_url_resolves(self):
        """Test create_portal_access action URL resolves."""
        import uuid
        pk = uuid.uuid4()
        url = reverse('clients:client-create-portal-access', kwargs={'pk': pk})
        assert f'/api/clients/{pk}/create_portal_access/' in url

    def test_client_update_financial_summary_url_resolves(self):
        """Test update_financial_summary action URL resolves."""
        import uuid
        pk = uuid.uuid4()
        url = reverse('clients:client-update-financial-summary', kwargs={'pk': pk})
        assert f'/api/clients/{pk}/update_financial_summary/' in url

    def test_client_notes_url_resolves(self):
        """Test notes action URL resolves."""
        import uuid
        pk = uuid.uuid4()
        url = reverse('clients:client-notes', kwargs={'pk': pk})
        assert f'/api/clients/{pk}/notes/' in url

    def test_client_documents_url_resolves(self):
        """Test documents action URL resolves."""
        import uuid
        pk = uuid.uuid4()
        url = reverse('clients:client-documents', kwargs={'pk': pk})
        assert f'/api/clients/{pk}/documents/' in url

    def test_note_list_url_resolves(self):
        """Test client-note-list URL resolves to ClientNoteViewSet."""
        url = reverse('clients:client-note-list')
        assert '/api/notes/' in url
        resolver = resolve(url)
        assert resolver.func.cls == ClientNoteViewSet

    def test_note_detail_url_resolves(self):
        """Test client-note-detail URL resolves correctly."""
        import uuid
        pk = uuid.uuid4()
        url = reverse('clients:client-note-detail', kwargs={'pk': pk})
        resolver = resolve(url)
        assert resolver.func.cls == ClientNoteViewSet

    def test_document_list_url_resolves(self):
        """Test client-document-list URL resolves to ClientDocumentViewSet."""
        url = reverse('clients:client-document-list')
        assert '/api/documents/' in url
        resolver = resolve(url)
        assert resolver.func.cls == ClientDocumentViewSet

    def test_document_detail_url_resolves(self):
        """Test client-document-detail URL resolves correctly."""
        import uuid
        pk = uuid.uuid4()
        url = reverse('clients:client-document-detail', kwargs={'pk': pk})
        resolver = resolve(url)
        assert resolver.func.cls == ClientDocumentViewSet

    def test_app_name(self):
        """Test the app_name is set to 'clients'."""
        from apps.clients import urls
        assert urls.app_name == 'clients'
