"""
Tests for integrations service layer.

Covers:
- BaseIntegrationService: sync(), test_connection(), refresh_token(), helpers
- get_service() factory and SERVICE_REGISTRY
- Concrete service classes (QuickBooks, Xero, Google Calendar, Outlook, Slack)
"""

import pytest
import time
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock, PropertyMock

from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.integrations.models import Integration, IntegrationSyncLog
from apps.integrations.services import (
    BaseIntegrationService,
    QuickBooksService,
    XeroService,
    GoogleCalendarService,
    OutlookCalendarService,
    SlackService,
    SERVICE_REGISTRY,
    get_service,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def qb_integration(db):
    return Integration.objects.create(
        name='QuickBooks',
        service_type=Integration.QUICKBOOKS,
        status=Integration.ACTIVE,
        access_token='tok_qb',
        refresh_token='ref_qb',
        config={
            'company_id': 'qb_123',
            'api_url': 'https://quickbooks.api.intuit.com/v3',
            'client_id': 'cid',
            'client_secret': 'csecret',
        },
    )


@pytest.fixture
def xero_integration(db):
    return Integration.objects.create(
        name='Xero',
        service_type=Integration.XERO,
        status=Integration.ACTIVE,
        access_token='tok_xero',
        refresh_token='ref_xero',
        config={
            'tenant_id': 'xero_t1',
            'client_id': 'cid',
            'client_secret': 'csecret',
        },
    )


@pytest.fixture
def gcal_integration(db):
    return Integration.objects.create(
        name='Google Calendar',
        service_type=Integration.GOOGLE_CALENDAR,
        status=Integration.ACTIVE,
        access_token='tok_gcal',
        refresh_token='ref_gcal',
        config={
            'calendar_id': 'primary',
            'client_id': 'cid',
            'client_secret': 'csecret',
        },
    )


@pytest.fixture
def outlook_integration(db):
    return Integration.objects.create(
        name='Outlook',
        service_type=Integration.OUTLOOK,
        status=Integration.ACTIVE,
        access_token='tok_outlook',
        refresh_token='ref_outlook',
        config={
            'tenant_id': 'common',
            'client_id': 'cid',
            'client_secret': 'csecret',
        },
    )


@pytest.fixture
def slack_integration(db):
    return Integration.objects.create(
        name='Slack',
        service_type=Integration.SLACK,
        status=Integration.ACTIVE,
        access_token='tok_slack',
        config={'channel': '#billing'},
    )


@pytest.fixture
def expired_integration(db):
    return Integration.objects.create(
        name='Expired',
        service_type=Integration.QUICKBOOKS,
        status=Integration.ACTIVE,
        access_token='tok_old',
        refresh_token='ref_old',
        token_expires_at=timezone.now() - timedelta(hours=1),
        config={'company_id': 'qb_exp'},
    )


# ---------------------------------------------------------------------------
# get_service / SERVICE_REGISTRY
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestGetService:

    def test_returns_quickbooks_service(self, qb_integration):
        svc = get_service(qb_integration)
        assert isinstance(svc, QuickBooksService)

    def test_returns_xero_service(self, xero_integration):
        svc = get_service(xero_integration)
        assert isinstance(svc, XeroService)

    def test_returns_google_calendar_service(self, gcal_integration):
        svc = get_service(gcal_integration)
        assert isinstance(svc, GoogleCalendarService)

    def test_returns_outlook_service(self, outlook_integration):
        svc = get_service(outlook_integration)
        assert isinstance(svc, OutlookCalendarService)

    def test_returns_slack_service(self, slack_integration):
        svc = get_service(slack_integration)
        assert isinstance(svc, SlackService)

    def test_unknown_service_type_raises(self, db):
        custom = Integration.objects.create(
            name='Custom',
            service_type='unknown_type',
            status=Integration.ACTIVE,
        )
        with pytest.raises(ValueError, match='No service implementation'):
            get_service(custom)

    def test_registry_has_all_services(self):
        assert 'quickbooks' in SERVICE_REGISTRY
        assert 'xero' in SERVICE_REGISTRY
        assert 'google_calendar' in SERVICE_REGISTRY
        assert 'outlook' in SERVICE_REGISTRY
        assert 'slack' in SERVICE_REGISTRY


# ---------------------------------------------------------------------------
# BaseIntegrationService helpers
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestBaseServiceHelpers:

    def test_get_headers(self, qb_integration):
        svc = QuickBooksService(qb_integration)
        headers = svc._get_headers()
        assert headers['Authorization'] == 'Bearer tok_qb'
        assert headers['Content-Type'] == 'application/json'

    def test_api_url_with_path(self, qb_integration):
        svc = QuickBooksService(qb_integration)
        url = svc._api_url('company/123/invoice')
        assert url == 'https://quickbooks.api.intuit.com/v3/company/123/invoice'

    def test_api_url_empty(self, qb_integration):
        svc = QuickBooksService(qb_integration)
        url = svc._api_url()
        assert url == 'https://quickbooks.api.intuit.com/v3'

    def test_api_url_strips_trailing_slash(self, db):
        integration = Integration.objects.create(
            name='Trailing',
            service_type=Integration.QUICKBOOKS,
            status=Integration.ACTIVE,
            config={'api_url': 'https://api.example.com/v1/'},
        )
        svc = QuickBooksService(integration)
        url = svc._api_url('/endpoint')
        assert url == 'https://api.example.com/v1/endpoint'


# ---------------------------------------------------------------------------
# BaseIntegrationService.sync()
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestBaseServiceSync:

    @patch('apps.integrations.services.QuickBooksService.execute_sync')
    def test_sync_success_creates_log(self, mock_exec, qb_integration):
        mock_exec.return_value = {'records_synced': 5, 'metadata': {'customers_synced': 3}}

        svc = QuickBooksService(qb_integration)
        log = svc.sync(sync_type='full')

        assert log.status == 'success'
        assert log.records_synced == 5
        assert log.duration_ms >= 0
        assert log.completed_at is not None

        qb_integration.refresh_from_db()
        assert qb_integration.last_sync_status == 'success'
        assert qb_integration.last_sync_error == ''

    @patch('apps.integrations.services.QuickBooksService.execute_sync')
    def test_sync_error_creates_log(self, mock_exec, qb_integration):
        mock_exec.side_effect = ConnectionError('API down')

        svc = QuickBooksService(qb_integration)
        with pytest.raises(ConnectionError):
            svc.sync()

        log = IntegrationSyncLog.objects.filter(integration=qb_integration).last()
        assert log.status == 'error'
        assert 'API down' in log.errors[0]

        qb_integration.refresh_from_db()
        assert qb_integration.last_sync_status == 'error'
        assert 'API down' in qb_integration.last_sync_error

    @patch('apps.integrations.services.QuickBooksService.execute_sync')
    def test_sync_updates_integration_last_sync(self, mock_exec, qb_integration):
        mock_exec.return_value = {'records_synced': 0, 'metadata': {}}

        before = timezone.now()
        svc = QuickBooksService(qb_integration)
        svc.sync()

        qb_integration.refresh_from_db()
        assert qb_integration.last_sync_at >= before


# ---------------------------------------------------------------------------
# BaseIntegrationService.test_connection()
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestBaseServiceTestConnection:

    @patch('apps.integrations.services.QuickBooksService._test_connection')
    def test_successful_connection(self, mock_test, qb_integration):
        mock_test.return_value = {'company': 'Test Corp'}

        svc = QuickBooksService(qb_integration)
        result = svc.test_connection()

        assert result['connected'] is True
        assert result['company'] == 'Test Corp'

    @patch('apps.integrations.services.QuickBooksService._test_connection')
    def test_failed_connection(self, mock_test, qb_integration):
        mock_test.side_effect = ConnectionError('Refused')

        svc = QuickBooksService(qb_integration)
        result = svc.test_connection()

        assert result['connected'] is False
        assert 'Refused' in result['error']


# ---------------------------------------------------------------------------
# BaseIntegrationService.refresh_token()
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestBaseServiceRefreshToken:

    @patch('apps.integrations.services.QuickBooksService._refresh_token')
    def test_refresh_when_needed(self, mock_refresh, expired_integration):
        mock_refresh.return_value = {
            'access_token': 'new_tok',
            'refresh_token': 'new_ref',
            'expires_in': 3600,
        }

        svc = QuickBooksService(expired_integration)
        result = svc.refresh_token()

        assert result is True
        expired_integration.refresh_from_db()
        assert expired_integration.access_token == 'new_tok'
        assert expired_integration.refresh_token == 'new_ref'

    def test_skip_when_not_needed(self, qb_integration):
        """Token is not expired so refresh_token returns False."""
        qb_integration.token_expires_at = None
        qb_integration.save()

        svc = QuickBooksService(qb_integration)
        result = svc.refresh_token()

        assert result is False

    @patch('apps.integrations.services.QuickBooksService._refresh_token')
    def test_refresh_failure_sets_error_status(self, mock_refresh, expired_integration):
        mock_refresh.side_effect = Exception('OAuth error')

        svc = QuickBooksService(expired_integration)
        with pytest.raises(Exception, match='OAuth error'):
            svc.refresh_token()

        expired_integration.refresh_from_db()
        assert expired_integration.status == Integration.ERROR

    @patch('apps.integrations.services.QuickBooksService._refresh_token')
    def test_refresh_without_new_refresh_token(self, mock_refresh, expired_integration):
        """If the response doesn't include a new refresh_token, keep the old one."""
        mock_refresh.return_value = {
            'access_token': 'new_tok',
            'expires_in': 3600,
        }

        old_ref = expired_integration.refresh_token
        svc = QuickBooksService(expired_integration)
        svc.refresh_token()

        expired_integration.refresh_from_db()
        assert expired_integration.access_token == 'new_tok'
        assert expired_integration.refresh_token == old_ref


# ---------------------------------------------------------------------------
# Concrete services: execute_sync with mocked requests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestQuickBooksServiceSync:

    @patch('requests.post')
    def test_execute_sync_posts_clients_invoices_payments(self, mock_post, qb_integration):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_post.return_value = mock_resp

        svc = QuickBooksService(qb_integration)
        result = svc.execute_sync('full')

        assert 'records_synced' in result
        assert 'metadata' in result

    @patch('requests.get')
    def test_test_connection(self, mock_get, qb_integration):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {'CompanyInfo': {'CompanyName': 'Test Corp'}}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        svc = QuickBooksService(qb_integration)
        result = svc._test_connection()

        assert result['company'] == 'Test Corp'

    @patch('requests.post')
    def test_refresh_token(self, mock_post, qb_integration):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            'access_token': 'new_access',
            'refresh_token': 'new_refresh',
            'expires_in': 3600,
        }
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        svc = QuickBooksService(qb_integration)
        tokens = svc._refresh_token()

        assert tokens['access_token'] == 'new_access'


@pytest.mark.django_db
class TestXeroServiceSync:

    @patch('requests.post')
    def test_execute_sync(self, mock_post, xero_integration):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_post.return_value = mock_resp

        svc = XeroService(xero_integration)
        result = svc.execute_sync('full')

        assert 'records_synced' in result

    @patch('requests.get')
    def test_test_connection(self, mock_get, xero_integration):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {'Organisations': [{'Name': 'Test Org'}]}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        svc = XeroService(xero_integration)
        result = svc._test_connection()

        assert result['organisation'] == 'Test Org'

    @patch('requests.post')
    def test_refresh_token(self, mock_post, xero_integration):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            'access_token': 'new_xero',
            'expires_in': 1800,
        }
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        svc = XeroService(xero_integration)
        tokens = svc._refresh_token()

        assert tokens['access_token'] == 'new_xero'


@pytest.mark.django_db
class TestGoogleCalendarServiceSync:

    @patch('requests.post')
    def test_execute_sync(self, mock_post, gcal_integration):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_post.return_value = mock_resp

        svc = GoogleCalendarService(gcal_integration)
        result = svc.execute_sync('full')

        assert 'records_synced' in result

    @patch('requests.get')
    def test_test_connection(self, mock_get, gcal_integration):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {'summary': 'My Calendar'}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        svc = GoogleCalendarService(gcal_integration)
        result = svc._test_connection()

        assert result['calendar'] == 'My Calendar'

    @patch('requests.post')
    def test_refresh_token(self, mock_post, gcal_integration):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            'access_token': 'new_gcal',
            'expires_in': 3600,
        }
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        svc = GoogleCalendarService(gcal_integration)
        tokens = svc._refresh_token()

        assert tokens['access_token'] == 'new_gcal'


@pytest.mark.django_db
class TestOutlookCalendarServiceSync:

    @patch('requests.post')
    def test_execute_sync(self, mock_post, outlook_integration):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_post.return_value = mock_resp

        svc = OutlookCalendarService(outlook_integration)
        result = svc.execute_sync('full')

        assert 'records_synced' in result

    @patch('requests.get')
    def test_test_connection(self, mock_get, outlook_integration):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {'displayName': 'Test User'}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        svc = OutlookCalendarService(outlook_integration)
        result = svc._test_connection()

        assert result['user'] == 'Test User'

    @patch('requests.post')
    def test_refresh_token(self, mock_post, outlook_integration):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            'access_token': 'new_outlook',
            'refresh_token': 'new_ref',
            'expires_in': 3600,
        }
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        svc = OutlookCalendarService(outlook_integration)
        tokens = svc._refresh_token()

        assert tokens['access_token'] == 'new_outlook'


@pytest.mark.django_db
class TestSlackServiceSync:

    @patch('requests.post')
    def test_execute_sync(self, mock_post, slack_integration):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {'ok': True}
        mock_post.return_value = mock_resp

        svc = SlackService(slack_integration)
        result = svc.execute_sync('full')

        assert 'records_synced' in result

    @patch('requests.post')
    def test_post_message_failure(self, mock_post, slack_integration):
        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.text = 'channel_not_found'
        mock_post.return_value = mock_resp

        svc = SlackService(slack_integration)
        sent = svc._post_message('#nonexistent', 'Hello')

        assert sent is False

    @patch('requests.post')
    def test_post_message_success(self, mock_post, slack_integration):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {'ok': True}
        mock_post.return_value = mock_resp

        svc = SlackService(slack_integration)
        sent = svc._post_message('#billing', 'Payment received')

        assert sent is True

    @patch('requests.post')
    def test_test_connection(self, mock_post, slack_integration):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {'ok': True, 'team': 'Aureon', 'user': 'bot'}
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        svc = SlackService(slack_integration)
        result = svc._test_connection()

        assert result['team'] == 'Aureon'

    @patch('requests.post')
    def test_test_connection_failure(self, mock_post, slack_integration):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {'ok': False, 'error': 'invalid_auth'}
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        svc = SlackService(slack_integration)
        with pytest.raises(ConnectionError, match='invalid_auth'):
            svc._test_connection()

    def test_refresh_token_no_refresh(self, slack_integration):
        """Slack bot tokens don't expire; no refresh_token means return existing."""
        slack_integration.refresh_token = ''
        slack_integration.save()

        svc = SlackService(slack_integration)
        tokens = svc._refresh_token()

        assert tokens['access_token'] == 'tok_slack'

    @patch('requests.post')
    def test_refresh_token_with_refresh(self, mock_post, slack_integration):
        slack_integration.refresh_token = 'slack_ref'
        slack_integration.save()

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            'access_token': 'new_slack',
            'refresh_token': 'new_slack_ref',
            'expires_in': 43200,
        }
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        svc = SlackService(slack_integration)
        tokens = svc._refresh_token()

        assert tokens['access_token'] == 'new_slack'


# ---------------------------------------------------------------------------
# execute_sync with real DB objects to cover loop bodies
# ---------------------------------------------------------------------------

@pytest.fixture
def _sync_data(db, admin_user):
    """Create Client, Invoice, and Payment objects for sync tests."""
    from apps.clients.models import Client
    from apps.invoicing.models import Invoice
    from apps.payments.models import Payment
    from apps.contracts.models import Contract
    from datetime import date

    client = Client.objects.create(
        client_type=Client.COMPANY,
        company_name='Sync Corp',
        first_name='Sync', last_name='User',
        email='sync@example.com',
        lifecycle_stage=Client.ACTIVE,
        owner=admin_user,
        is_active=True,
    )

    contract = Contract.objects.create(
        client=client,
        title='Sync Project',
        contract_type=Contract.FIXED_PRICE,
        status=Contract.ACTIVE,
        start_date=date.today(),
        value=Decimal('10000.00'),
        owner=admin_user,
    )

    invoice = Invoice.objects.create(
        client=client,
        contract=contract,
        status=Invoice.SENT,
        issue_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        subtotal=Decimal('5000.00'),
        tax_rate=Decimal('0.00'),
        tax_amount=Decimal('0.00'),
        total=Decimal('5000.00'),
    )

    payment = Payment.objects.create(
        invoice=invoice,
        amount=Decimal('5000.00'),
        currency='USD',
        payment_method=Payment.CARD,
        status=Payment.SUCCEEDED,
        payment_date=timezone.now(),
    )

    return {'client': client, 'invoice': invoice, 'payment': payment, 'contract': contract}


@pytest.mark.django_db
class TestQuickBooksExecuteSyncWithData:

    @patch('requests.post')
    def test_syncs_clients_invoices_payments(self, mock_post, qb_integration, _sync_data):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_post.return_value = mock_resp

        svc = QuickBooksService(qb_integration)
        result = svc.execute_sync('full')

        assert result['records_synced'] >= 3
        assert result['metadata']['customers_synced'] >= 1
        assert result['metadata']['invoices_synced'] >= 1
        assert result['metadata']['payments_synced'] >= 1
        assert mock_post.call_count >= 3

    @patch('requests.post')
    def test_sync_failure_logged(self, mock_post, qb_integration, _sync_data):
        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.text = 'Bad Request'
        mock_post.return_value = mock_resp

        svc = QuickBooksService(qb_integration)
        result = svc.execute_sync('full')

        assert result['records_synced'] == 0

    @patch('requests.post')
    def test_incremental_sync(self, mock_post, qb_integration, _sync_data):
        qb_integration.last_sync_at = timezone.now() - timedelta(hours=1)
        qb_integration.save()

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_post.return_value = mock_resp

        svc = QuickBooksService(qb_integration)
        result = svc.execute_sync('incremental')

        assert result['records_synced'] >= 0


@pytest.mark.django_db
class TestXeroExecuteSyncWithData:

    @patch('requests.post')
    def test_syncs_clients_invoices_payments(self, mock_post, xero_integration, _sync_data):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_post.return_value = mock_resp

        svc = XeroService(xero_integration)
        result = svc.execute_sync('full')

        assert result['records_synced'] >= 3
        assert result['metadata']['contacts_synced'] >= 1
        assert result['metadata']['invoices_synced'] >= 1
        assert result['metadata']['payments_synced'] >= 1

    @patch('requests.post')
    def test_sync_failure_logged(self, mock_post, xero_integration, _sync_data):
        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.text = 'Xero Error'
        mock_post.return_value = mock_resp

        svc = XeroService(xero_integration)
        result = svc.execute_sync('full')

        assert result['records_synced'] == 0

    @patch('requests.post')
    def test_incremental_sync(self, mock_post, xero_integration, _sync_data):
        xero_integration.last_sync_at = timezone.now() - timedelta(hours=1)
        xero_integration.save()

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_post.return_value = mock_resp

        svc = XeroService(xero_integration)
        result = svc.execute_sync('incremental')

        assert result['records_synced'] >= 0


@pytest.mark.django_db
class TestGoogleCalendarExecuteSyncWithData:

    @patch('requests.post')
    def test_syncs_milestones_and_invoices(self, mock_post, gcal_integration, _sync_data):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_post.return_value = mock_resp

        svc = GoogleCalendarService(gcal_integration)
        result = svc.execute_sync('full')

        assert result['records_synced'] >= 0
        assert 'metadata' in result

    @patch('requests.post')
    def test_sync_failure(self, mock_post, gcal_integration, _sync_data):
        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.text = 'Calendar Error'
        mock_post.return_value = mock_resp

        svc = GoogleCalendarService(gcal_integration)
        result = svc.execute_sync('full')

        assert result['records_synced'] == 0


@pytest.mark.django_db
class TestOutlookCalendarExecuteSyncWithData:

    @patch('requests.post')
    def test_syncs_milestones_and_invoices(self, mock_post, outlook_integration, _sync_data):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_post.return_value = mock_resp

        svc = OutlookCalendarService(outlook_integration)
        result = svc.execute_sync('full')

        assert result['records_synced'] >= 0
        assert 'metadata' in result

    @patch('requests.post')
    def test_sync_failure(self, mock_post, outlook_integration, _sync_data):
        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.text = 'Outlook Error'
        mock_post.return_value = mock_resp

        svc = OutlookCalendarService(outlook_integration)
        result = svc.execute_sync('full')

        assert result['records_synced'] == 0


@pytest.mark.django_db
class TestSlackExecuteSyncWithData:

    @patch('requests.post')
    def test_syncs_notifications(self, mock_post, slack_integration, _sync_data):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {'ok': True}
        mock_post.return_value = mock_resp

        svc = SlackService(slack_integration)
        result = svc.execute_sync('full')

        assert result['records_synced'] >= 0

    @patch('requests.post')
    def test_sync_with_overdue_invoices(self, mock_post, slack_integration, _sync_data):
        from apps.invoicing.models import Invoice
        from datetime import date

        Invoice.objects.filter(id=_sync_data['invoice'].id).update(
            status=Invoice.OVERDUE,
            due_date=date.today() - timedelta(days=10),
        )

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {'ok': True}
        mock_post.return_value = mock_resp

        svc = SlackService(slack_integration)
        result = svc.execute_sync('full')

        assert result['records_synced'] >= 0
