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
        assert result['expired_sessions_removed'] >= 3

        # Valid session should still exist
        assert Session.objects.filter(session_key='valid_key').exists()

    def test_no_expired_sessions(self):
        """Test behavior when there are no expired sessions."""
        result = cleanup_expired_sessions()

        assert result['status'] == 'success'
        assert result['expired_sessions_removed'] == 0

    def test_returns_status(self):
        """Test that the result includes status."""
        result = cleanup_expired_sessions()

        assert 'status' in result
        assert result['status'] == 'success'

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

    @patch('os.makedirs')
    @patch('builtins.open', new_callable=MagicMock)
    @patch('django.core.serializers.serialize')
    def test_creates_backup_files(self, mock_serialize, mock_open, mock_makedirs):
        """Test that backup creates serialized data files."""
        mock_serialize.return_value = '{"test": "data"}'

        result = backup_critical_data()

        assert result['status'] == 'success'
        assert len(result['files']) > 0
        mock_serialize.assert_called()

    @patch('os.makedirs')
    @patch('builtins.open', new_callable=MagicMock)
    @patch('django.core.serializers.serialize')
    def test_creates_backup_directory(self, mock_serialize, mock_open, mock_makedirs):
        """Test that the backup directory is created if it does not exist."""
        mock_serialize.return_value = '[]'

        backup_critical_data()

        mock_makedirs.assert_called()

    @patch('os.makedirs')
    @patch('builtins.open', new_callable=MagicMock)
    @patch('django.core.serializers.serialize')
    def test_returns_backup_timestamp(self, mock_serialize, mock_open, mock_makedirs):
        """Test that the result includes a backup timestamp."""
        mock_serialize.return_value = '[]'

        result = backup_critical_data()

        assert 'timestamp' in result

    @patch('os.makedirs')
    @patch('builtins.open', new_callable=MagicMock)
    @patch('django.core.serializers.serialize')
    def test_handles_serialization_error(self, mock_serialize, mock_open, mock_makedirs):
        """Test graceful handling of serialization errors."""
        mock_serialize.side_effect = Exception("Serialization failed")

        # The task catches per-model exceptions, so it should still succeed
        # but with an empty files list
        result = backup_critical_data()
        assert result['status'] == 'success'
        assert len(result['files']) == 0


@pytest.mark.django_db
class TestHealthCheckExternalServices:
    """Tests for health_check_external_services task."""

    def test_checks_all_services(self):
        """Test that all external services are checked."""
        result = health_check_external_services()

        assert 'services' in result
        assert 'database' in result['services']
        assert 'redis' in result['services']
        assert 'stripe' in result['services']

    def test_database_healthy(self):
        """Test that database health check passes."""
        result = health_check_external_services()

        assert result['services']['database']['status'] == 'healthy'

    def test_redis_status_reported(self):
        """Test that Redis status is reported."""
        result = health_check_external_services()

        assert 'status' in result['services']['redis']

    def test_stripe_status_reported(self):
        """Test that Stripe status is reported."""
        result = health_check_external_services()

        assert 'status' in result['services']['stripe']

    def test_all_services_have_status(self):
        """Test that all services report a status."""
        result = health_check_external_services()

        for service_name, service_info in result['services'].items():
            assert 'status' in service_info, f"Service {service_name} missing status"

    def test_returns_timestamp(self):
        """Test that the result includes a timestamp."""
        result = health_check_external_services()

        assert 'timestamp' in result

    @patch('apps.core.tasks.settings')
    def test_stripe_with_real_key_failure(self, mock_settings):
        """Test Stripe health check when API call fails."""
        mock_settings.CELERY_BROKER_URL = 'redis://localhost:6379/0'
        mock_settings.STRIPE_SECRET_KEY = 'sk_live_realkey123'
        mock_settings.STRIPE_LIVE_SECRET_KEY = 'sk_live_realkey123'

        with patch('stripe.Account.retrieve', side_effect=Exception("API error")):
            result = health_check_external_services()

        assert result['services']['stripe']['status'] == 'unhealthy'
        assert 'error' in result['services']['stripe']

    @patch('apps.core.tasks.settings')
    def test_stripe_with_real_key_success(self, mock_settings):
        """Test Stripe health check when API call succeeds."""
        mock_settings.CELERY_BROKER_URL = 'redis://localhost:6379/0'
        mock_settings.STRIPE_SECRET_KEY = 'sk_live_realkey123'
        mock_settings.STRIPE_LIVE_SECRET_KEY = 'sk_live_realkey123'

        with patch('stripe.Account.retrieve', return_value=MagicMock()):
            result = health_check_external_services()

        assert result['services']['stripe']['status'] == 'healthy'


@pytest.mark.django_db
class TestCleanupExpiredSessionsRetry:
    """Tests for cleanup_expired_sessions retry behavior."""

    @patch('apps.core.tasks.Session')
    def test_retries_on_exception(self, mock_session_cls):
        """Test that the task retries on database error."""
        mock_session_cls.objects.filter.return_value.delete.side_effect = Exception("DB error")

        with pytest.raises(Exception):
            cleanup_expired_sessions()


@pytest.mark.django_db
class TestBackupCriticalDataRetry:
    """Tests for backup_critical_data retry behavior."""

    @patch('os.makedirs', side_effect=Exception("Permission denied"))
    def test_retries_on_exception(self, mock_makedirs):
        """Test that the task retries on failure."""
        with pytest.raises(Exception):
            backup_critical_data()


# =============================================================================
# Redis Exception and Stripe Skipped Tests (covers lines 104-105, 119)
# =============================================================================

@pytest.mark.django_db
class TestHealthCheckRedisException:
    """Tests for Redis exception handling in health check (lines 104-105)."""

    @patch('apps.core.tasks.settings')
    def test_redis_unhealthy_when_getattr_raises(self, mock_settings):
        """Redis check should be unhealthy when settings access raises an exception."""
        # Make CELERY_BROKER_URL raise an AttributeError via side_effect on getattr
        type(mock_settings).CELERY_BROKER_URL = property(
            lambda self: (_ for _ in ()).throw(Exception("Redis connect failed"))
        )
        mock_settings.STRIPE_SECRET_KEY = 'sk_test_XXXX_dummy'
        mock_settings.STRIPE_LIVE_SECRET_KEY = ''

        result = health_check_external_services()

        assert result['services']['redis']['status'] == 'unhealthy'
        assert 'error' in result['services']['redis']


@pytest.mark.django_db
class TestHealthCheckStripeSkipped:
    """Tests for Stripe skipped when test keys are used (line 119)."""

    @patch('apps.core.tasks.settings')
    def test_stripe_skipped_with_test_key(self, mock_settings):
        """Stripe check should be skipped when using test placeholder key."""
        mock_settings.CELERY_BROKER_URL = 'redis://localhost:6379/0'
        mock_settings.STRIPE_SECRET_KEY = 'sk_test_XXXX_dummy'
        mock_settings.STRIPE_LIVE_SECRET_KEY = ''

        result = health_check_external_services()

        assert result['services']['stripe']['status'] == 'skipped'
        assert 'Test keys' in result['services']['stripe']['message']

    @patch('apps.core.tasks.settings')
    def test_stripe_skipped_when_not_configured(self, mock_settings):
        """Stripe check should be skipped when no key is configured."""
        mock_settings.CELERY_BROKER_URL = 'redis://localhost:6379/0'
        mock_settings.STRIPE_SECRET_KEY = None
        mock_settings.STRIPE_LIVE_SECRET_KEY = None

        result = health_check_external_services()

        assert result['services']['stripe']['status'] == 'skipped'
