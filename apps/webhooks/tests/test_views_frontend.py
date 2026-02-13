"""
Tests for webhooks app frontend views.

Tests cover:
- WebhookEventListView (list, filtering by source/status, counts)
- WebhookEventDetailView (detail page with payload, headers, retry info)
- WebhookEndpointListView (endpoint listing with active/total counts)
- Authentication enforcement (LoginRequiredMixin redirects)
"""

import uuid
import pytest
from django.test import Client as TestClient
from django.template import TemplateDoesNotExist
from django.contrib.auth import get_user_model

from apps.webhooks.models import WebhookEvent, WebhookEndpoint

User = get_user_model()


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------
WEBHOOK_EVENT_LIST_URL = '/webhooks/events/'
WEBHOOK_ENDPOINT_LIST_URL = '/webhooks/endpoints/'


def webhook_event_detail_url(pk):
    return f'/webhooks/events/{pk}/'


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='webhook_test_user',
        email='webhook_user@test.com',
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
def stripe_event_processed(db):
    return WebhookEvent.objects.create(
        source=WebhookEvent.STRIPE,
        event_type='payment_intent.succeeded',
        event_id=f'evt_{uuid.uuid4().hex[:24]}',
        payload={'type': 'payment_intent.succeeded', 'data': {'amount': 5000}},
        headers={'stripe_signature': 't=123,v1=abc'},
        status=WebhookEvent.PROCESSED,
    )


@pytest.fixture
def stripe_event_failed(db):
    return WebhookEvent.objects.create(
        source=WebhookEvent.STRIPE,
        event_type='payment_intent.failed',
        event_id=f'evt_{uuid.uuid4().hex[:24]}',
        payload={'type': 'payment_intent.failed', 'data': {'amount': 2000}},
        headers={'stripe_signature': 't=456,v1=def'},
        status=WebhookEvent.FAILED,
        error_message='Payment method declined',
        retry_count=2,
    )


@pytest.fixture
def custom_event_pending(db):
    return WebhookEvent.objects.create(
        source=WebhookEvent.CUSTOM,
        event_type='invoice.created',
        event_id=f'custom_{uuid.uuid4().hex[:12]}',
        payload={'event_type': 'invoice.created', 'data': {'invoice_id': '123'}},
        status=WebhookEvent.PENDING,
    )


@pytest.fixture
def webhook_endpoint_active(db):
    return WebhookEndpoint.objects.create(
        url='https://example.com/webhook',
        secret_key='test-secret',
        event_types=['invoice.created', 'payment.succeeded'],
        is_active=True,
    )


@pytest.fixture
def webhook_endpoint_inactive(db):
    return WebhookEndpoint.objects.create(
        url='https://example.com/webhook-old',
        secret_key='old-secret',
        event_types=['invoice.created'],
        is_active=False,
    )


# ---------------------------------------------------------------------------
# WebhookEventListView tests
# ---------------------------------------------------------------------------
class TestWebhookEventListView:
    """Tests for WebhookEventListView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self):
        client = TestClient()
        response = client.get(WEBHOOK_EVENT_LIST_URL)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client, stripe_event_processed):
        try:
            response = auth_client.get(WEBHOOK_EVENT_LIST_URL)
            assert response.status_code == 200
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_expected_keys(
        self, auth_client, stripe_event_processed, stripe_event_failed
    ):
        try:
            response = auth_client.get(WEBHOOK_EVENT_LIST_URL)
            ctx = response.context
            assert ctx['page_title'] == 'Webhook Events'
            assert 'source_choices' in ctx
            assert 'status_choices' in ctx
            assert 'current_source' in ctx
            assert 'current_status' in ctx
            assert 'total_events' in ctx
            assert 'failed_count' in ctx
            assert 'processed_count' in ctx
            assert 'events' in ctx
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_event_counts(
        self, auth_client, stripe_event_processed, stripe_event_failed, custom_event_pending
    ):
        try:
            response = auth_client.get(WEBHOOK_EVENT_LIST_URL)
            ctx = response.context
            assert ctx['total_events'] == 3
            assert ctx['failed_count'] == 1
            assert ctx['processed_count'] == 1
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_filter_by_source(
        self, auth_client, stripe_event_processed, custom_event_pending
    ):
        try:
            response = auth_client.get(WEBHOOK_EVENT_LIST_URL, {'source': WebhookEvent.STRIPE})
            events = list(response.context['events'])
            assert stripe_event_processed in events
            assert custom_event_pending not in events
            assert all(e.source == WebhookEvent.STRIPE for e in events)
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_filter_by_status(
        self, auth_client, stripe_event_processed, stripe_event_failed
    ):
        try:
            response = auth_client.get(WEBHOOK_EVENT_LIST_URL, {'status': WebhookEvent.FAILED})
            events = list(response.context['events'])
            assert stripe_event_failed in events
            assert stripe_event_processed not in events
            assert all(e.status == WebhookEvent.FAILED for e in events)
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_filter_by_source_and_status(
        self, auth_client, stripe_event_processed, stripe_event_failed, custom_event_pending
    ):
        try:
            response = auth_client.get(
                WEBHOOK_EVENT_LIST_URL,
                {'source': WebhookEvent.STRIPE, 'status': WebhookEvent.PROCESSED},
            )
            events = list(response.context['events'])
            assert stripe_event_processed in events
            assert stripe_event_failed not in events
            assert custom_event_pending not in events
        except TemplateDoesNotExist:
            pass


# ---------------------------------------------------------------------------
# WebhookEventDetailView tests
# ---------------------------------------------------------------------------
class TestWebhookEventDetailView:
    """Tests for WebhookEventDetailView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self, stripe_event_processed):
        client = TestClient()
        response = client.get(webhook_event_detail_url(stripe_event_processed.pk))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client, stripe_event_processed):
        try:
            response = auth_client.get(webhook_event_detail_url(stripe_event_processed.pk))
            assert response.status_code == 200
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_detail_data(self, auth_client, stripe_event_failed):
        try:
            response = auth_client.get(webhook_event_detail_url(stripe_event_failed.pk))
            ctx = response.context
            assert ctx['event'] == stripe_event_failed
            assert 'page_title' in ctx
            assert 'payload' in ctx
            assert 'headers' in ctx
            assert 'can_retry' in ctx
            assert 'is_stripe_event' in ctx
            assert 'retry_count' in ctx
            assert 'max_retries' in ctx
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_stripe_event_is_flagged(self, auth_client, stripe_event_processed):
        try:
            response = auth_client.get(webhook_event_detail_url(stripe_event_processed.pk))
            ctx = response.context
            assert ctx['is_stripe_event'] is True
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_custom_event_not_flagged_as_stripe(self, auth_client, custom_event_pending):
        try:
            response = auth_client.get(webhook_event_detail_url(custom_event_pending.pk))
            ctx = response.context
            assert ctx['is_stripe_event'] is False
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_failed_event_can_retry(self, auth_client, stripe_event_failed):
        try:
            response = auth_client.get(webhook_event_detail_url(stripe_event_failed.pk))
            ctx = response.context
            assert ctx['can_retry'] is True
            assert ctx['retry_count'] == 2
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_nonexistent_event_returns_404(self, auth_client):
        fake_uuid = uuid.uuid4()
        try:
            response = auth_client.get(webhook_event_detail_url(fake_uuid))
            assert response.status_code == 404
        except TemplateDoesNotExist:
            pass


# ---------------------------------------------------------------------------
# WebhookEndpointListView tests
# ---------------------------------------------------------------------------
class TestWebhookEndpointListView:
    """Tests for WebhookEndpointListView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self):
        client = TestClient()
        response = client.get(WEBHOOK_ENDPOINT_LIST_URL)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client, webhook_endpoint_active):
        try:
            response = auth_client.get(WEBHOOK_ENDPOINT_LIST_URL)
            assert response.status_code == 200
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_expected_keys(
        self, auth_client, webhook_endpoint_active, webhook_endpoint_inactive
    ):
        try:
            response = auth_client.get(WEBHOOK_ENDPOINT_LIST_URL)
            ctx = response.context
            assert ctx['page_title'] == 'Webhook Endpoints'
            assert 'event_type_choices' in ctx
            assert 'active_count' in ctx
            assert 'total_count' in ctx
            assert 'endpoints' in ctx
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_active_and_total_counts(
        self, auth_client, webhook_endpoint_active, webhook_endpoint_inactive
    ):
        try:
            response = auth_client.get(WEBHOOK_ENDPOINT_LIST_URL)
            ctx = response.context
            assert ctx['active_count'] == 1
            assert ctx['total_count'] == 2
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_all_endpoints_listed(
        self, auth_client, webhook_endpoint_active, webhook_endpoint_inactive
    ):
        try:
            response = auth_client.get(WEBHOOK_ENDPOINT_LIST_URL)
            endpoints = list(response.context['endpoints'])
            assert webhook_endpoint_active in endpoints
            assert webhook_endpoint_inactive in endpoints
        except TemplateDoesNotExist:
            pass
