"""
Tests for clients app frontend views.

Tests ClientListView, ClientDetailView, ClientCreateView, ClientEditView,
ClientPortalView, and PortalMessagesView.
"""

import pytest
from django.test import Client as TestClient, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.template import TemplateDoesNotExist

from apps.clients.views_frontend import (
    ClientListView,
    ClientDetailView,
    ClientCreateView,
    ClientEditView,
    ClientPortalView,
    PortalMessagesView,
)
from apps.clients.models import Client, PortalMessage

User = get_user_model()


@pytest.fixture
def rf():
    """Return a Django RequestFactory."""
    return RequestFactory()


@pytest.fixture
def user(db):
    """Create a standard test user."""
    return User.objects.create_user(
        username='clientviewuser',
        email='clientviewuser@test.com',
        password='TestPass123!',
        first_name='Client',
        last_name='ViewUser',
        role=User.ADMIN,
        is_active=True,
    )


@pytest.fixture
def client_obj(db, user):
    """Create a test client."""
    return Client.objects.create(
        client_type=Client.COMPANY,
        company_name='Test Company',
        first_name='John',
        last_name='Doe',
        email='john@testcompany.com',
        lifecycle_stage=Client.ACTIVE,
        owner=user,
        is_active=True,
    )


@pytest.fixture
def inactive_client(db, user):
    """Create an inactive client."""
    return Client.objects.create(
        client_type=Client.INDIVIDUAL,
        first_name='Inactive',
        last_name='Client',
        email='inactive@test.com',
        lifecycle_stage=Client.CHURNED,
        owner=user,
        is_active=False,
    )


@pytest.fixture
def portal_message(db, client_obj, user):
    """Create a portal message."""
    return PortalMessage.objects.create(
        client=client_obj,
        sender=user,
        subject='Test Message',
        content='This is a test message.',
        is_from_client=False,
        is_read=False,
    )


# ============================================================================
# ClientListView Tests
# ============================================================================

class TestClientListView:
    """Tests for the ClientListView."""

    @pytest.mark.django_db
    def test_redirects_unauthenticated(self, rf):
        """Unauthenticated users are redirected."""
        request = rf.get('/clients/')
        request.user = AnonymousUser()
        response = ClientListView.as_view()(request)
        assert response.status_code == 302

    @pytest.mark.django_db
    def test_queryset_returns_active_clients(self, rf, user, client_obj, inactive_client):
        """Queryset only returns active clients."""
        request = rf.get('/clients/')
        request.user = user
        view = ClientListView()
        view.request = request
        view.kwargs = {}
        view.setup(request)
        queryset = view.get_queryset()
        assert client_obj in queryset
        assert inactive_client not in queryset

    @pytest.mark.django_db
    def test_queryset_filters_by_stage(self, rf, user, client_obj):
        """Queryset filters by lifecycle stage when provided."""
        request = rf.get('/clients/', {'stage': 'active'})
        request.user = user
        view = ClientListView()
        view.request = request
        view.kwargs = {}
        view.setup(request)
        queryset = view.get_queryset()
        assert client_obj in queryset

    @pytest.mark.django_db
    def test_queryset_filters_by_search(self, rf, user, client_obj):
        """Queryset filters by search query."""
        request = rf.get('/clients/', {'q': 'Test Company'})
        request.user = user
        view = ClientListView()
        view.request = request
        view.kwargs = {}
        view.setup(request)
        queryset = view.get_queryset()
        assert client_obj in queryset

    @pytest.mark.django_db
    def test_queryset_search_no_match(self, rf, user, client_obj):
        """Queryset returns empty when search has no match."""
        request = rf.get('/clients/', {'q': 'NonExistentCompanyXYZ'})
        request.user = user
        view = ClientListView()
        view.request = request
        view.kwargs = {}
        view.setup(request)
        queryset = view.get_queryset()
        assert client_obj not in queryset

    @pytest.mark.django_db
    def test_context_data(self, rf, user, client_obj):
        """Context includes expected keys."""
        request = rf.get('/clients/')
        request.user = user
        view = ClientListView()
        view.request = request
        view.kwargs = {}
        view.setup(request)
        view.object_list = view.get_queryset()
        context = view.get_context_data()
        assert context['page_title'] == 'Clients'
        assert 'stage_choices' in context
        assert 'current_stage' in context
        assert 'search_query' in context
        assert 'total_clients' in context

    @pytest.mark.django_db
    def test_template_name(self):
        """ClientListView uses the correct template."""
        assert ClientListView.template_name == 'clients/client_list.html'


# ============================================================================
# ClientDetailView Tests
# ============================================================================

class TestClientDetailView:
    """Tests for the ClientDetailView."""

    @pytest.mark.django_db
    def test_redirects_unauthenticated(self, rf, client_obj):
        """Unauthenticated users are redirected."""
        request = rf.get(f'/clients/{client_obj.pk}/')
        request.user = AnonymousUser()
        response = ClientDetailView.as_view()(request, pk=client_obj.pk)
        assert response.status_code == 302

    @pytest.mark.django_db
    def test_context_data(self, rf, user, client_obj):
        """Context includes notes, documents, contracts, invoices, and messages."""
        request = rf.get(f'/clients/{client_obj.pk}/')
        request.user = user
        view = ClientDetailView()
        view.request = request
        view.kwargs = {'pk': str(client_obj.pk)}
        view.setup(request, pk=str(client_obj.pk))
        view.object = client_obj
        context = view.get_context_data()
        assert 'notes' in context
        assert 'documents' in context
        assert 'contracts' in context
        assert 'invoices' in context
        assert 'portal_messages' in context
        assert 'page_title' in context

    @pytest.mark.django_db
    def test_context_page_title(self, rf, user, client_obj):
        """Context page title includes client display name."""
        request = rf.get(f'/clients/{client_obj.pk}/')
        request.user = user
        view = ClientDetailView()
        view.request = request
        view.kwargs = {'pk': str(client_obj.pk)}
        view.setup(request, pk=str(client_obj.pk))
        view.object = client_obj
        context = view.get_context_data()
        assert client_obj.get_display_name() in context['page_title']

    @pytest.mark.django_db
    def test_template_name(self):
        """ClientDetailView uses the correct template."""
        assert ClientDetailView.template_name == 'clients/client_detail.html'

    @pytest.mark.django_db
    def test_model(self):
        """ClientDetailView uses the Client model."""
        assert ClientDetailView.model == Client


# ============================================================================
# ClientCreateView Tests
# ============================================================================

class TestClientCreateView:
    """Tests for the ClientCreateView."""

    @pytest.mark.django_db
    def test_redirects_unauthenticated(self, rf):
        """Unauthenticated users are redirected."""
        request = rf.get('/clients/create/')
        request.user = AnonymousUser()
        response = ClientCreateView.as_view()(request)
        assert response.status_code == 302

    @pytest.mark.django_db
    def test_context_data(self, rf, user):
        """Context includes page title and choice fields."""
        request = rf.get('/clients/create/')
        request.user = user
        view = ClientCreateView()
        view.request = request
        view.kwargs = {}
        view.setup(request)
        view.object = None
        context = view.get_context_data()
        assert context['page_title'] == 'Add New Client'
        assert 'type_choices' in context
        assert 'stage_choices' in context

    @pytest.mark.django_db
    def test_template_name(self):
        """ClientCreateView uses the correct template."""
        assert ClientCreateView.template_name == 'clients/client_create.html'

    @pytest.mark.django_db
    def test_fields(self):
        """ClientCreateView has the expected form fields."""
        assert 'email' in ClientCreateView.fields
        assert 'first_name' in ClientCreateView.fields
        assert 'last_name' in ClientCreateView.fields
        assert 'company_name' in ClientCreateView.fields

    @pytest.mark.django_db
    def test_model(self):
        """ClientCreateView uses the Client model."""
        assert ClientCreateView.model == Client


# ============================================================================
# ClientEditView Tests
# ============================================================================

class TestClientEditView:
    """Tests for the ClientEditView."""

    @pytest.mark.django_db
    def test_redirects_unauthenticated(self, rf, client_obj):
        """Unauthenticated users are redirected."""
        request = rf.get(f'/clients/{client_obj.pk}/edit/')
        request.user = AnonymousUser()
        response = ClientEditView.as_view()(request, pk=client_obj.pk)
        assert response.status_code == 302

    @pytest.mark.django_db
    def test_context_data(self, rf, user, client_obj):
        """Context includes client and choice fields."""
        request = rf.get(f'/clients/{client_obj.pk}/edit/')
        request.user = user
        view = ClientEditView()
        view.request = request
        view.kwargs = {'pk': str(client_obj.pk)}
        view.setup(request, pk=str(client_obj.pk))
        context = view.get_context_data()
        assert context['client'] == client_obj
        assert 'type_choices' in context
        assert 'stage_choices' in context
        assert client_obj.get_display_name() in context['page_title']

    @pytest.mark.django_db
    def test_template_name(self):
        """ClientEditView uses the correct template."""
        assert ClientEditView.template_name == 'clients/client_edit.html'


# ============================================================================
# ClientPortalView Tests
# ============================================================================

class TestClientPortalView:
    """Tests for the ClientPortalView."""

    @pytest.mark.django_db
    def test_redirects_unauthenticated(self, rf, client_obj):
        """Unauthenticated users are redirected."""
        request = rf.get(f'/clients/{client_obj.pk}/portal/')
        request.user = AnonymousUser()
        response = ClientPortalView.as_view()(request, pk=client_obj.pk)
        assert response.status_code == 302

    @pytest.mark.django_db
    def test_context_data(self, rf, user, client_obj):
        """Context includes client, contracts, invoices, documents, and messages."""
        request = rf.get(f'/clients/{client_obj.pk}/portal/')
        request.user = user
        view = ClientPortalView()
        view.request = request
        view.kwargs = {'pk': str(client_obj.pk)}
        view.setup(request, pk=str(client_obj.pk))
        context = view.get_context_data()
        assert context['client'] == client_obj
        assert 'contracts' in context
        assert 'invoices' in context
        assert 'documents' in context
        assert 'portal_messages' in context
        assert 'page_title' in context

    @pytest.mark.django_db
    def test_context_page_title(self, rf, user, client_obj):
        """Portal page title includes client name."""
        request = rf.get(f'/clients/{client_obj.pk}/portal/')
        request.user = user
        view = ClientPortalView()
        view.request = request
        view.kwargs = {'pk': str(client_obj.pk)}
        view.setup(request, pk=str(client_obj.pk))
        context = view.get_context_data()
        assert 'Portal:' in context['page_title']

    @pytest.mark.django_db
    def test_template_name(self):
        """ClientPortalView uses the correct template."""
        assert ClientPortalView.template_name == 'clients/client_portal.html'


# ============================================================================
# PortalMessagesView Tests
# ============================================================================

class TestPortalMessagesView:
    """Tests for the PortalMessagesView."""

    @pytest.mark.django_db
    def test_redirects_unauthenticated(self, rf, client_obj):
        """Unauthenticated users are redirected."""
        request = rf.get(f'/clients/{client_obj.pk}/messages/')
        request.user = AnonymousUser()
        response = PortalMessagesView.as_view()(request, pk=client_obj.pk)
        assert response.status_code == 302

    @pytest.mark.django_db
    def test_queryset_filters_by_client(self, rf, user, client_obj, portal_message):
        """Queryset returns messages for the specified client."""
        request = rf.get(f'/clients/{client_obj.pk}/messages/')
        request.user = user
        view = PortalMessagesView()
        view.request = request
        view.kwargs = {'pk': str(client_obj.pk)}
        view.setup(request, pk=str(client_obj.pk))
        queryset = view.get_queryset()
        assert portal_message in queryset

    @pytest.mark.django_db
    def test_context_data(self, rf, user, client_obj, portal_message):
        """Context includes client, page title, and unread count."""
        request = rf.get(f'/clients/{client_obj.pk}/messages/')
        request.user = user
        view = PortalMessagesView()
        view.request = request
        view.kwargs = {'pk': str(client_obj.pk)}
        view.setup(request, pk=str(client_obj.pk))
        view.object_list = view.get_queryset()
        context = view.get_context_data()
        assert context['client'] == client_obj
        assert 'page_title' in context
        assert 'unread_count' in context

    @pytest.mark.django_db
    def test_unread_count_tracks_client_messages(self, rf, user, client_obj):
        """Unread count only counts unread messages from the client."""
        PortalMessage.objects.create(
            client=client_obj,
            sender=user,
            subject='From client',
            content='Unread from client',
            is_from_client=True,
            is_read=False,
        )
        PortalMessage.objects.create(
            client=client_obj,
            sender=user,
            subject='From staff',
            content='Staff message',
            is_from_client=False,
            is_read=False,
        )
        request = rf.get(f'/clients/{client_obj.pk}/messages/')
        request.user = user
        view = PortalMessagesView()
        view.request = request
        view.kwargs = {'pk': str(client_obj.pk)}
        view.setup(request, pk=str(client_obj.pk))
        view.object_list = view.get_queryset()
        context = view.get_context_data()
        assert context['unread_count'] == 1

    @pytest.mark.django_db
    def test_template_name(self):
        """PortalMessagesView uses the correct template."""
        assert PortalMessagesView.template_name == 'clients/portal_messages.html'
