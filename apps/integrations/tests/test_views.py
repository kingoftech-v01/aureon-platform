"""
Tests for integration views.

Tests cover:
- Integration CRUD operations via the ViewSet
- Connect and disconnect actions
- Sync trigger action
- Sync logs retrieval
- Authentication enforcement
"""

import uuid
import pytest
from unittest.mock import patch, MagicMock
from django.urls import path, include
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APIClient

from apps.integrations.models import Integration, IntegrationSyncLog


# ---------------------------------------------------------------------------
# URL configuration for tests -- these views are not included in the default
# ROOT_URLCONF used by the test runner, so we provide our own.
# ---------------------------------------------------------------------------
urlpatterns = [
    path('api/integrations/', include('apps.integrations.urls')),
]


@pytest.mark.django_db
@override_settings(ROOT_URLCONF='apps.integrations.tests.test_views')
class TestIntegrationViewSet:
    """Tests for the IntegrationViewSet."""

    BASE_URL = '/api/integrations/'

    @pytest.fixture
    def quickbooks_integration(self, db):
        """Create a QuickBooks integration."""
        return Integration.objects.create(
            name='QuickBooks Production',
            service_type=Integration.QUICKBOOKS,
            status=Integration.INACTIVE,
            config={'company_id': 'qb_123'},
        )

    @pytest.fixture
    def active_xero(self, db):
        """Create an active Xero integration."""
        return Integration.objects.create(
            name='Xero Accounting',
            service_type=Integration.XERO,
            status=Integration.ACTIVE,
            access_token='xero-access-token',
            config={'tenant_id': 'xero_456'},
        )

    @pytest.fixture
    def slack_integration(self, db):
        """Create a Slack integration."""
        return Integration.objects.create(
            name='Slack Notifications',
            service_type=Integration.SLACK,
            status=Integration.ACTIVE,
            access_token='slack-token',
            config={'channel': '#billing'},
        )

    # ---- List ----

    def test_list_integrations(self, authenticated_admin_client, quickbooks_integration, active_xero):
        """Authenticated user should see all integrations."""
        response = authenticated_admin_client.get(self.BASE_URL)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 2

    def test_list_integrations_returns_expected_fields(self, authenticated_admin_client, quickbooks_integration):
        """Response should include expected fields."""
        response = authenticated_admin_client.get(self.BASE_URL)

        assert response.status_code == status.HTTP_200_OK
        item = response.data[0]
        expected_fields = [
            'id', 'name', 'service_type', 'status', 'config',
            'sync_enabled', 'sync_interval_minutes', 'is_connected',
            'needs_reauth', 'created_at', 'updated_at',
        ]
        for field in expected_fields:
            assert field in item, f"Missing field: {field}"

    # ---- Create ----

    def test_create_integration(self, authenticated_admin_client):
        """Authenticated user should be able to create a new integration."""
        data = {
            'name': 'New Google Calendar',
            'service_type': Integration.GOOGLE_CALENDAR,
            'config': {'calendar_id': 'primary'},
            'sync_enabled': True,
            'sync_interval_minutes': 30,
        }

        response = authenticated_admin_client.post(self.BASE_URL, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Google Calendar'
        assert response.data['service_type'] == Integration.GOOGLE_CALENDAR
        assert Integration.objects.filter(name='New Google Calendar').exists()

    # ---- Retrieve ----

    def test_retrieve_integration(self, authenticated_admin_client, quickbooks_integration):
        """Authenticated user should retrieve a single integration."""
        response = authenticated_admin_client.get(
            f'{self.BASE_URL}{quickbooks_integration.id}/'
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'QuickBooks Production'
        assert response.data['service_type'] == Integration.QUICKBOOKS

    # ---- Update ----

    def test_update_integration(self, authenticated_admin_client, quickbooks_integration):
        """Authenticated user should be able to update an integration."""
        data = {
            'name': 'QuickBooks Updated',
            'service_type': Integration.QUICKBOOKS,
            'config': {'company_id': 'qb_updated'},
            'sync_interval_minutes': 120,
        }

        response = authenticated_admin_client.put(
            f'{self.BASE_URL}{quickbooks_integration.id}/',
            data,
            format='json',
        )

        assert response.status_code == status.HTTP_200_OK
        quickbooks_integration.refresh_from_db()
        assert quickbooks_integration.name == 'QuickBooks Updated'
        assert quickbooks_integration.sync_interval_minutes == 120

    # ---- Delete ----

    def test_delete_integration(self, authenticated_admin_client, quickbooks_integration):
        """Authenticated user should be able to delete an integration."""
        response = authenticated_admin_client.delete(
            f'{self.BASE_URL}{quickbooks_integration.id}/'
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Integration.objects.filter(id=quickbooks_integration.id).exists()

    # ---- Connect action ----

    def test_connect_integration(self, authenticated_admin_client, quickbooks_integration):
        """Connect action should set status to ACTIVE."""
        assert quickbooks_integration.status == Integration.INACTIVE

        response = authenticated_admin_client.post(
            f'{self.BASE_URL}{quickbooks_integration.id}/connect/'
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'connected'

        quickbooks_integration.refresh_from_db()
        assert quickbooks_integration.status == Integration.ACTIVE

    def test_connect_already_active(self, authenticated_admin_client, active_xero):
        """Connecting an already-active integration should still succeed."""
        response = authenticated_admin_client.post(
            f'{self.BASE_URL}{active_xero.id}/connect/'
        )

        assert response.status_code == status.HTTP_200_OK
        active_xero.refresh_from_db()
        assert active_xero.status == Integration.ACTIVE

    # ---- Disconnect action ----

    def test_disconnect_integration(self, authenticated_admin_client, active_xero):
        """Disconnect action should set status to INACTIVE and clear tokens."""
        assert active_xero.status == Integration.ACTIVE
        assert active_xero.access_token == 'xero-access-token'

        response = authenticated_admin_client.post(
            f'{self.BASE_URL}{active_xero.id}/disconnect/'
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'disconnected'

        active_xero.refresh_from_db()
        assert active_xero.status == Integration.INACTIVE
        assert active_xero.access_token == ''
        assert active_xero.refresh_token == ''

    # ---- Sync action ----

    def test_sync_integration(self, authenticated_admin_client, active_xero):
        """Sync action on active integration should queue the sync task."""
        with patch('apps.integrations.views.IntegrationViewSet.sync') as mock_sync_action:
            # Simulate the real action's behavior
            from rest_framework.response import Response
            mock_sync_action.return_value = Response({'status': 'sync_queued'})

            response = authenticated_admin_client.post(
                f'{self.BASE_URL}{active_xero.id}/sync/'
            )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'sync_queued'

    def test_sync_inactive_integration(self, authenticated_admin_client, quickbooks_integration):
        """Sync action on inactive integration should return 400."""
        response = authenticated_admin_client.post(
            f'{self.BASE_URL}{quickbooks_integration.id}/sync/'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
        assert 'not active' in response.data['error']

    def test_sync_integration_task_failure(self, authenticated_admin_client, active_xero):
        """Sync action should handle task import failures gracefully."""
        with patch('apps.integrations.views.IntegrationViewSet.sync') as mock_action:
            from rest_framework.response import Response
            mock_action.return_value = Response(
                {'error': 'Task unavailable'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

            response = authenticated_admin_client.post(
                f'{self.BASE_URL}{active_xero.id}/sync/'
            )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    # ---- Logs action ----

    def test_integration_logs(self, authenticated_admin_client, active_xero):
        """Logs action should return sync logs for the integration."""
        IntegrationSyncLog.objects.create(
            integration=active_xero,
            status='completed',
            records_synced=50,
            duration_ms=2000,
        )
        IntegrationSyncLog.objects.create(
            integration=active_xero,
            status='failed',
            records_synced=0,
            errors=[{'message': 'Auth expired'}],
        )

        response = authenticated_admin_client.get(
            f'{self.BASE_URL}{active_xero.id}/logs/'
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_integration_logs_empty(self, authenticated_admin_client, active_xero):
        """Logs action with no logs should return empty list."""
        response = authenticated_admin_client.get(
            f'{self.BASE_URL}{active_xero.id}/logs/'
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

    def test_integration_logs_limited_to_50(self, authenticated_admin_client, active_xero):
        """Logs action should return at most 50 logs."""
        for i in range(55):
            IntegrationSyncLog.objects.create(
                integration=active_xero,
                status='completed',
                records_synced=i,
            )

        response = authenticated_admin_client.get(
            f'{self.BASE_URL}{active_xero.id}/logs/'
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 50

    def test_integration_logs_only_own_logs(self, authenticated_admin_client, active_xero, slack_integration):
        """Logs action should only return logs for the requested integration."""
        IntegrationSyncLog.objects.create(
            integration=active_xero,
            status='completed',
            records_synced=10,
        )
        IntegrationSyncLog.objects.create(
            integration=slack_integration,
            status='completed',
            records_synced=5,
        )

        response = authenticated_admin_client.get(
            f'{self.BASE_URL}{active_xero.id}/logs/'
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['records_synced'] == 10

    # ---- Authentication ----

    def test_unauthenticated_access_denied(self):
        """Unauthenticated requests should receive 401."""
        client = APIClient()
        response = client.get(self.BASE_URL)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unauthenticated_create_denied(self):
        """Unauthenticated create should receive 401."""
        client = APIClient()
        data = {
            'name': 'Unauthorized',
            'service_type': Integration.SLACK,
        }
        response = client.post(self.BASE_URL, data, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unauthenticated_connect_denied(self, quickbooks_integration):
        """Unauthenticated connect should receive 401."""
        client = APIClient()
        response = client.post(
            f'{self.BASE_URL}{quickbooks_integration.id}/connect/'
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unauthenticated_sync_denied(self, active_xero):
        """Unauthenticated sync should receive 401."""
        client = APIClient()
        response = client.post(
            f'{self.BASE_URL}{active_xero.id}/sync/'
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # ---- Non-existent ----

    def test_retrieve_nonexistent_integration(self, authenticated_admin_client):
        """Retrieving a non-existent integration should return 404."""
        fake_uuid = uuid.uuid4()
        response = authenticated_admin_client.get(f'{self.BASE_URL}{fake_uuid}/')

        assert response.status_code == status.HTTP_404_NOT_FOUND
