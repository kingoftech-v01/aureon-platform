"""
Tests for clients app signals.
"""

import pytest
import logging
from apps.clients.models import Client


@pytest.mark.django_db
class TestClientSignals:
    """Tests for client signals."""

    def test_log_client_creation_on_new_client(self, caplog):
        """Test that creating a new client triggers a log message."""
        with caplog.at_level(logging.INFO, logger='aureon.clients'):
            client = Client.objects.create(
                client_type=Client.INDIVIDUAL,
                first_name='Signal',
                last_name='Test',
                email='signal.test@example.com',
                lifecycle_stage=Client.LEAD,
            )
        assert 'New client created' in caplog.text
        assert 'Signal Test' in caplog.text
        assert 'signal.test@example.com' in caplog.text

    def test_log_client_creation_for_company(self, caplog):
        """Test log message for company client creation."""
        with caplog.at_level(logging.INFO, logger='aureon.clients'):
            client = Client.objects.create(
                client_type=Client.COMPANY,
                company_name='Signal Corp',
                first_name='Test',
                last_name='User',
                email='signal.corp@example.com',
                lifecycle_stage=Client.LEAD,
            )
        assert 'New client created' in caplog.text
        assert 'Signal Corp' in caplog.text

    def test_no_log_on_client_update(self, client_company, caplog):
        """Test that updating an existing client does not trigger the creation log."""
        with caplog.at_level(logging.INFO, logger='aureon.clients'):
            caplog.clear()
            client_company.first_name = 'UpdatedName'
            client_company.save()
        # Should not log "New client created" on update
        assert 'New client created' not in caplog.text
