"""
Tests for accounts signals module.

Covers:
- log_user_creation signal handler (fires on user creation, does not fire on update)
"""

import logging
import pytest
from unittest.mock import patch
from django.contrib.auth import get_user_model

User = get_user_model()


class TestLogUserCreationSignal:
    """Tests for the log_user_creation post_save signal."""

    @pytest.mark.django_db
    def test_signal_fires_on_user_creation(self, tenant, caplog):
        """Signal logs a message when a new user is created."""
        with caplog.at_level(logging.INFO, logger='aureon.accounts'):
            user = User.objects.create_user(
                username='signaltest',
                email='signaltest@example.com',
                password='V3ryS3cureP@ss!',
                first_name='Signal',
                last_name='Test',
                tenant=tenant,
            )

        assert any(
            'New user created' in record.message and 'signaltest@example.com' in record.message
            for record in caplog.records
        )

    @pytest.mark.django_db
    def test_signal_does_not_fire_on_update(self, admin_user, caplog):
        """Signal does not log on user update (only on creation)."""
        with caplog.at_level(logging.INFO, logger='aureon.accounts'):
            admin_user.first_name = 'Updated'
            admin_user.save()

        creation_logs = [
            record for record in caplog.records
            if 'New user created' in record.message and admin_user.email in record.message
        ]
        assert len(creation_logs) == 0

    @pytest.mark.django_db
    def test_signal_logs_tenant_info(self, tenant, caplog):
        """Signal log message includes tenant information."""
        with caplog.at_level(logging.INFO, logger='aureon.accounts'):
            User.objects.create_user(
                username='tenantlog',
                email='tenantlog@example.com',
                password='V3ryS3cureP@ss!',
                first_name='Tenant',
                last_name='Log',
                tenant=tenant,
            )

        assert any(
            'Tenant' in record.message
            for record in caplog.records
            if 'New user created' in record.message
        )

    @pytest.mark.django_db
    def test_signal_logs_for_user_without_tenant(self, caplog):
        """Signal fires correctly for a user created without a tenant (e.g., superuser)."""
        with caplog.at_level(logging.INFO, logger='aureon.accounts'):
            User.objects.create_superuser(
                username='notenant',
                email='notenant@example.com',
                password='V3ryS3cureP@ss!',
                first_name='No',
                last_name='Tenant',
            )

        assert any(
            'New user created' in record.message and 'notenant@example.com' in record.message
            for record in caplog.records
        )

    @pytest.mark.django_db
    @patch('apps.accounts.signals.logging.getLogger')
    def test_signal_uses_correct_logger(self, mock_get_logger, tenant):
        """Signal uses the 'aureon.accounts' logger."""
        mock_logger = mock_get_logger.return_value

        User.objects.create_user(
            username='loggername',
            email='loggername@example.com',
            password='V3ryS3cureP@ss!',
            first_name='Logger',
            last_name='Name',
            tenant=tenant,
        )

        mock_get_logger.assert_called_with('aureon.accounts')
        mock_logger.info.assert_called_once()

    @pytest.mark.django_db
    def test_signal_fires_for_each_creation(self, tenant, caplog):
        """Signal fires independently for each user created."""
        with caplog.at_level(logging.INFO, logger='aureon.accounts'):
            User.objects.create_user(
                username='first',
                email='first@example.com',
                password='V3ryS3cureP@ss!',
                first_name='First',
                last_name='User',
                tenant=tenant,
            )
            User.objects.create_user(
                username='second',
                email='second@example.com',
                password='V3ryS3cureP@ss!',
                first_name='Second',
                last_name='User',
                tenant=tenant,
            )

        creation_logs = [
            record for record in caplog.records
            if 'New user created' in record.message
        ]
        assert len(creation_logs) == 2
        messages = [r.message for r in creation_logs]
        assert any('first@example.com' in m for m in messages)
        assert any('second@example.com' in m for m in messages)
