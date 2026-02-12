"""
Tests for webhooks URL configuration.

Covers:
- stripe_webhook URL resolution
- generic_webhook URL resolution (with UUID)
- webhook_health URL resolution
- API router URL inclusion
- app_name namespace
"""

import uuid
from django.urls import resolve, reverse


class TestWebhookURLs:

    def test_stripe_webhook_url_resolves(self):
        url = reverse('webhooks:stripe_webhook')
        assert url == '/webhooks/stripe/'

    def test_stripe_webhook_resolves_to_view(self):
        match = resolve('/webhooks/stripe/')
        assert match.func.__name__ == 'stripe_webhook'
        assert match.namespace == 'webhooks'

    def test_generic_webhook_url_resolves(self):
        test_uuid = uuid.uuid4()
        url = reverse('webhooks:generic_webhook', kwargs={'endpoint_id': test_uuid})
        assert f'/webhooks/receive/{test_uuid}/' == url

    def test_generic_webhook_resolves_to_view(self):
        test_uuid = uuid.uuid4()
        match = resolve(f'/webhooks/receive/{test_uuid}/')
        assert match.func.__name__ == 'generic_webhook'

    def test_webhook_health_url_resolves(self):
        url = reverse('webhooks:webhook_health')
        assert url == '/webhooks/health/'

    def test_webhook_health_resolves_to_view(self):
        match = resolve('/webhooks/health/')
        assert match.func.__name__ == 'webhook_health'

    def test_app_name(self):
        """The app_name should be 'webhooks'."""
        from apps.webhooks import urls
        assert urls.app_name == 'webhooks'

    def test_api_prefix_exists(self):
        """API router URLs should be under /webhooks/api/."""
        # The router is empty but the path exists
        match = resolve('/webhooks/api/')
        assert match is not None
