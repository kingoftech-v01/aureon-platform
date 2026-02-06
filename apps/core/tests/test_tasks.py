"""
Tests for core Celery tasks.

Tests cover session cleanup, critical data backup, and external service health checks.
"""
import pytest
from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.utils import timezone

from apps.core.tasks import (
    cleanup_expired_sessions,
    backup_critical_data,
    health_check_external_services,
)


@pytest.mark.django_db
class TestCleanupExpiredSessions:
    """Tests for cleanup_expired_sessions task."""

    def test_deletes_expired_sessions(self):
        """Test that expired sessions are removed from the database."""
        from django.contrib.sessions.models import Session

        # Create expired sessions
        for i in range(3):
            Session.objects.create(
                session_key=f'expired_key_{i}',
                session_data='encoded_data',
                expire_date=timezone.now() - timedelta(hours=i + 1),
            )

        # Create a valid session
        Session.objects.create(
            session_key='valid_key',
            session_data='encoded_data',
            expire_date=timezone.now() + timedelta(hours=12),
        )

        result = cleanup_expired_sessions()

        assert result['status'] == 'success'
        assert result['deleted_count'] >= 3

        # Valid session should still exist
        assert Session.objects.filter(session_key='valid_key').exists()

    def test_no_expired_sessions(self):
        """Test behavior when there are no expired sessions."""
        result = cleanup_expired_sessions()

        assert result['status'] == 'success'
        assert result['deleted_count'] == 0

    def test_returns_timestamp(self):
        """Test that the result includes a timestamp."""
        result = cleanup_expired_sessions()

        assert 'timestamp' in result

    def test_preserves_future_sessions(self):
        """Test that sessions with future expiry dates are preserved."""
        from django.contrib.sessions.models import Session

        Session.objects.create(
            session_key='future_session',
            session_data='encoded_data',
            expire_date=timezone.now() + timedelta(days=7),
        )

        cleanup_expired_sessions()

        assert Session.objects.filter(session_key='future_session').exists()


@pytest.mark.django_db
class TestBackupCriticalData:
    """Tests for backup_critical_data task."""

    @patch('apps.core.tasks.os')
    @patch('builtins.open', new_callable=MagicMock)
    @patch('django.core.serializers.serialize')
    def test_creates_backup_files(self, mock_serialize, mock_open, mock_os):
        """Test that backup creates serialized data files."""
        mock_os.makedirs = MagicMock()
        mock_os.path.join = lambda *args: '/'.join(args)
        mock_serialize.return_value = '{"test": "data"}'

        result = backup_critical_data()

        assert result['status'] == 'success'
        assert result['backup_count'] > 0
        mock_serialize.assert_called()

    @patch('apps.core.tasks.os')
    @patch('builtins.open', new_callable=MagicMock)
    @patch('django.core.serializers.serialize')
    def test_creates_backup_directory(self, mock_serialize, mock_open, mock_os):
        """Test that the backup directory is created if it does not exist."""
        mock_os.makedirs = MagicMock()
        mock_os.path.join = lambda *args: '/'.join(args)
        mock_serialize.return_value = '[]'

        backup_critical_data()

        mock_os.makedirs.assert_called()

    @patch('apps.core.tasks.os')
    @patch('builtins.open', new_callable=MagicMock)
    @patch('django.core.serializers.serialize')
    def test_returns_backup_timestamp(self, mock_serialize, mock_open, mock_os):
        """Test that the result includes a backup timestamp."""
        mock_os.makedirs = MagicMock()
        mock_os.path.join = lambda *args: '/'.join(args)
        mock_serialize.return_value = '[]'

        result = backup_critical_data()

        assert 'timestamp' in result

    @patch('apps.core.tasks.os')
    @patch('builtins.open', new_callable=MagicMock)
    @patch('django.core.serializers.serialize')
    def test_handles_serialization_error(self, mock_serialize, mock_open, mock_os):
        """Test graceful handling of serialization errors."""
        mock_os.makedirs = MagicMock()
        mock_os.path.join = lambda *args: '/'.join(args)
        mock_serialize.side_effect = Exception("Serialization failed")

        from celery.exceptions import Retry

        with pytest.raises(Retry):
            backup_critical_data()


@pytest.mark.django_db
class TestHealthCheckExternalServices:
    """Tests for health_check_external_services task."""

    @patch('apps.core.tasks.redis.Redis')
    @patch('stripe.Account.retrieve')
    def test_checks_all_services(self, mock_stripe, mock_redis_cls):
        """Test that all external services are checked."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_cls.from_url.return_value = mock_redis
        mock_stripe.return_value = MagicMock()

        result = health_check_external_services()

        assert result['status'] == 'success'
        assert 'services' in result
        assert 'database' in result['services']
        assert 'redis' in result['services']
        assert 'stripe' in result['services']

    @patch('apps.core.tasks.redis.Redis')
    @patch('stripe.Account.retrieve')
    def test_database_healthy(self, mock_stripe, mock_redis_cls):
        """Test that database health check passes."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_cls.from_url.return_value = mock_redis
        mock_stripe.return_value = MagicMock()

        result = health_check_external_services()

        assert result['services']['database']['healthy'] is True

    @patch('apps.core.tasks.redis.Redis')
    @patch('stripe.Account.retrieve')
    def test_redis_unhealthy(self, mock_stripe, mock_redis_cls):
        """Test that Redis failure is reported correctly."""
        mock_redis = MagicMock()
        mock_redis.ping.side_effect = Exception("Connection refused")
        mock_redis_cls.from_url.return_value = mock_redis
        mock_stripe.return_value = MagicMock()

        result = health_check_external_services()

        assert result['services']['redis']['healthy'] is False
        assert 'error' in result['services']['redis']

    @patch('apps.core.tasks.redis.Redis')
    @patch('stripe.Account.retrieve')
    def test_stripe_unhealthy(self, mock_stripe, mock_redis_cls):
        """Test that Stripe failure is reported correctly."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_cls.from_url.return_value = mock_redis
        mock_stripe.side_effect = Exception("Invalid API key")

        result = health_check_external_services()

        assert result['services']['stripe']['healthy'] is False
        assert 'error' in result['services']['stripe']

    @patch('apps.core.tasks.redis.Redis')
    @patch('stripe.Account.retrieve')
    def test_all_services_unhealthy(self, mock_stripe, mock_redis_cls):
        """Test behavior when all external services are down."""
        mock_redis = MagicMock()
        mock_redis.ping.side_effect = Exception("Redis down")
        mock_redis_cls.from_url.return_value = mock_redis
        mock_stripe.side_effect = Exception("Stripe down")

        result = health_check_external_services()

        assert result['status'] == 'success'
        assert result['services']['redis']['healthy'] is False
        assert result['services']['stripe']['healthy'] is False

    @patch('apps.core.tasks.redis.Redis')
    @patch('stripe.Account.retrieve')
    def test_returns_timestamp(self, mock_stripe, mock_redis_cls):
        """Test that the result includes a timestamp."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_cls.from_url.return_value = mock_redis
        mock_stripe.return_value = MagicMock()

        result = health_check_external_services()

        assert 'timestamp' in result
