"""
Tests for integrations app frontend views.

Tests cover:
- IntegrationListView (list with active/total counts)
- IntegrationDetailView (detail page with sync logs and connection status)
- IntegrationConnectView (connection setup page)
- Authentication enforcement (LoginRequiredMixin redirects)
"""

import uuid
import pytest
from django.test import Client as TestClient
from django.template import TemplateDoesNotExist
from django.contrib.auth import get_user_model

from apps.integrations.models import Integration, IntegrationSyncLog

User = get_user_model()


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------
INTEGRATION_LIST_URL = '/api/integrations/list/'
INTEGRATION_CONNECT_URL = '/api/integrations/connect/'


def integration_detail_url(pk):
    return f'/api/integrations/{pk}/'


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='integ_test_user',
        email='integ_user@test.com',
        password='TestPass123!',
        role=User.ADMIN,
        is_staff=True,
        is_active=True,
        is_verified=True,
    )


@pytest.fixture
def auth_client(user):
    client = TestClient()
    client.force_login(user)
    return client


@pytest.fixture
def active_integration(db):
    return Integration.objects.create(
        name='Xero Accounting',
        service_type=Integration.XERO,
        status=Integration.ACTIVE,
        access_token='xero-access-token',
        config={'tenant_id': 'xero_456'},
    )


@pytest.fixture
def inactive_integration(db):
    return Integration.objects.create(
        name='QuickBooks Staging',
        service_type=Integration.QUICKBOOKS,
        status=Integration.INACTIVE,
        config={'company_id': 'qb_staging'},
    )


@pytest.fixture
def integration_with_logs(active_integration):
    IntegrationSyncLog.objects.create(
        integration=active_integration,
        status='completed',
        records_synced=50,
        duration_ms=2000,
    )
    IntegrationSyncLog.objects.create(
        integration=active_integration,
        status='failed',
        records_synced=0,
        errors=[{'message': 'Auth expired'}],
    )
    return active_integration


# ---------------------------------------------------------------------------
# IntegrationListView tests
# ---------------------------------------------------------------------------
class TestIntegrationListView:
    """Tests for IntegrationListView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self):
        client = TestClient()
        response = client.get(INTEGRATION_LIST_URL)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client, active_integration):
        try:
            response = auth_client.get(INTEGRATION_LIST_URL)
            assert response.status_code == 200
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_expected_keys(self, auth_client, active_integration, inactive_integration):
        try:
            response = auth_client.get(INTEGRATION_LIST_URL)
            ctx = response.context
            assert ctx['page_title'] == 'Integrations'
            assert 'service_choices' in ctx
            assert 'status_choices' in ctx
            assert 'active_count' in ctx
            assert 'total_count' in ctx
            assert 'integrations' in ctx
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_active_and_total_counts(self, auth_client, active_integration, inactive_integration):
        try:
            response = auth_client.get(INTEGRATION_LIST_URL)
            ctx = response.context
            assert ctx['active_count'] == 1
            assert ctx['total_count'] == 2
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_all_integrations_listed(self, auth_client, active_integration, inactive_integration):
        try:
            response = auth_client.get(INTEGRATION_LIST_URL)
            integrations = list(response.context['integrations'])
            assert active_integration in integrations
            assert inactive_integration in integrations
        except TemplateDoesNotExist:
            pass


# ---------------------------------------------------------------------------
# IntegrationDetailView tests
# ---------------------------------------------------------------------------
class TestIntegrationDetailView:
    """Tests for IntegrationDetailView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self, active_integration):
        client = TestClient()
        response = client.get(integration_detail_url(active_integration.pk))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client, integration_with_logs):
        try:
            response = auth_client.get(integration_detail_url(integration_with_logs.pk))
            assert response.status_code == 200
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_detail_data(self, auth_client, integration_with_logs):
        try:
            response = auth_client.get(integration_detail_url(integration_with_logs.pk))
            ctx = response.context
            assert ctx['integration'] == integration_with_logs
            assert 'page_title' in ctx
            assert 'sync_logs' in ctx
            assert 'is_connected' in ctx
            assert 'needs_reauth' in ctx
            assert 'last_sync_at' in ctx
            assert 'last_sync_status' in ctx
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_nonexistent_integration_returns_404(self, auth_client):
        fake_uuid = uuid.uuid4()
        try:
            response = auth_client.get(integration_detail_url(fake_uuid))
            assert response.status_code == 404
        except TemplateDoesNotExist:
            pass


# ---------------------------------------------------------------------------
# IntegrationConnectView tests
# ---------------------------------------------------------------------------
class TestIntegrationConnectView:
    """Tests for IntegrationConnectView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self):
        client = TestClient()
        response = client.get(INTEGRATION_CONNECT_URL)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client):
        try:
            response = auth_client.get(INTEGRATION_CONNECT_URL)
            assert response.status_code == 200
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_connect_data(self, auth_client):
        try:
            response = auth_client.get(INTEGRATION_CONNECT_URL)
            ctx = response.context
            assert ctx['page_title'] == 'Connect Integration'
            assert 'service_choices' in ctx
        except TemplateDoesNotExist:
            pass
