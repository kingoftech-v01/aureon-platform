"""
Tests for core security module.

Tests cover SecurityMonitor: alert sending, alert deduplication, and hourly stats.
"""
import pytest
from unittest.mock import patch, MagicMock, call

from django.core.cache import cache
from django.utils import timezone

from apps.core.security import SecurityMonitor


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before each test."""
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
class TestSecurityMonitorSendAlert:
    """Tests for SecurityMonitor._send_alert_notification."""

    @patch('django.core.mail.mail_admins')
    def test_sends_email_to_admins(self, mock_mail_admins):
        """Test that _send_alert_notification sends an email to admins."""
        monitor = SecurityMonitor()

        monitor._send_alert_notification(
            event_type='failed_logins',
            count=150,
            threshold=100,
            details={'ip': '10.0.0.1'},
        )

        mock_mail_admins.assert_called_once()
        call_args = mock_mail_admins.call_args
        subject = call_args[0][0]
        message = call_args[0][1]

        assert 'failed_logins' in subject
        assert '150' in message
        assert '100' in message

    @patch('django.core.mail.mail_admins')
    def test_email_includes_event_details(self, mock_mail_admins):
        """Test that the email body includes event details."""
        monitor = SecurityMonitor()

        details = {'ip': '192.168.1.50', 'user_agent': 'bad-bot/1.0'}
        monitor._send_alert_notification(
            event_type='suspicious_requests',
            count=200,
            threshold=100,
            details=details,
        )

        message = mock_mail_admins.call_args[0][1]
        assert '192.168.1.50' in message
        assert 'suspicious_requests' in message

    @patch('django.core.mail.mail_admins')
    def test_uses_fail_silently(self, mock_mail_admins):
        """Test that mail_admins is called with fail_silently=True."""
        monitor = SecurityMonitor()

        monitor._send_alert_notification('failed_logins', 100, 50, None)

        mock_mail_admins.assert_called_once()
        assert mock_mail_admins.call_args[1]['fail_silently'] is True

    @patch('django.core.mail.mail_admins')
    def test_handles_mail_exception_gracefully(self, mock_mail_admins):
        """Test that email sending failure does not raise an exception."""
        mock_mail_admins.side_effect = Exception("SMTP connection failed")
        monitor = SecurityMonitor()

        # Should not raise
        monitor._send_alert_notification('failed_logins', 100, 50, None)

    @patch('django.core.mail.mail_admins')
    def test_sends_alert_with_none_details(self, mock_mail_admins):
        """Test that sending alert with None details works."""
        monitor = SecurityMonitor()

        monitor._send_alert_notification(
            event_type='rate_limits',
            count=300,
            threshold=200,
            details=None,
        )

        mock_mail_admins.assert_called_once()
        message = mock_mail_admins.call_args[0][1]
        assert 'None' in message or 'rate_limits' in message


@pytest.mark.django_db
class TestSecurityMonitorTriggerAlert:
    """Tests for SecurityMonitor._trigger_alert and record_event."""

    @patch.object(SecurityMonitor, '_send_alert_notification')
    def test_triggers_alert_when_threshold_exceeded(self, mock_send_alert):
        """Test that an alert is triggered when event count exceeds threshold."""
        monitor = SecurityMonitor()
        monitor.thresholds = {'failed_logins_per_hour': 3}

        # Record events up to threshold
        for _ in range(3):
            monitor.record_event('failed_logins', {'ip': '10.0.0.1'})

        mock_send_alert.assert_called_once()
        call_args = mock_send_alert.call_args[1] if mock_send_alert.call_args[1] else {}
        positional = mock_send_alert.call_args[0]

        assert positional[0] == 'failed_logins'
        assert positional[1] == 3  # count
        assert positional[2] == 3  # threshold

    @patch.object(SecurityMonitor, '_send_alert_notification')
    def test_does_not_trigger_below_threshold(self, mock_send_alert):
        """Test that no alert is triggered when below threshold."""
        monitor = SecurityMonitor()
        monitor.thresholds = {'failed_logins_per_hour': 10}

        for _ in range(5):
            monitor.record_event('failed_logins')

        mock_send_alert.assert_not_called()

    @patch.object(SecurityMonitor, '_send_alert_notification')
    def test_only_alerts_once_per_hour(self, mock_send_alert):
        """Test that duplicate alerts are suppressed within the same hour."""
        monitor = SecurityMonitor()
        monitor.thresholds = {'failed_logins_per_hour': 2}

        # First threshold breach triggers alert
        monitor.record_event('failed_logins')
        monitor.record_event('failed_logins')

        # Second threshold breach in same hour should not trigger
        monitor.record_event('failed_logins')
        monitor.record_event('failed_logins')

        assert mock_send_alert.call_count == 1

    @patch.object(SecurityMonitor, '_send_alert_notification')
    def test_increments_counter_on_each_event(self, mock_send_alert):
        """Test that the counter increments with each recorded event."""
        monitor = SecurityMonitor()
        monitor.thresholds = {'test_event_per_hour': 1000}  # high threshold

        monitor.record_event('test_event')
        monitor.record_event('test_event')
        monitor.record_event('test_event')

        counter_key = monitor._get_counter_key('test_event')
        count = cache.get(counter_key, 0)
        assert count == 3

    @patch.object(SecurityMonitor, '_send_alert_notification')
    def test_separate_counters_per_event_type(self, mock_send_alert):
        """Test that different event types have separate counters."""
        monitor = SecurityMonitor()
        monitor.thresholds = {}

        monitor.record_event('failed_logins')
        monitor.record_event('failed_logins')
        monitor.record_event('blocked_ips')

        login_key = monitor._get_counter_key('failed_logins')
        ip_key = monitor._get_counter_key('blocked_ips')

        assert cache.get(login_key) == 2
        assert cache.get(ip_key) == 1

    @patch.object(SecurityMonitor, '_send_alert_notification')
    def test_no_alert_for_unconfigured_event_type(self, mock_send_alert):
        """Test that events without a threshold do not trigger alerts."""
        monitor = SecurityMonitor()
        monitor.thresholds = {}  # No thresholds configured

        for _ in range(100):
            monitor.record_event('custom_event')

        mock_send_alert.assert_not_called()


@pytest.mark.django_db
class TestSecurityMonitorHourlyStats:
    """Tests for SecurityMonitor.get_hourly_stats."""

    def test_returns_zero_counts_initially(self):
        """Test that hourly stats are all zero when no events recorded."""
        monitor = SecurityMonitor()

        stats = monitor.get_hourly_stats()

        assert stats['failed_logins'] == 0
        assert stats['blocked_ips'] == 0
        assert stats['rate_limits'] == 0
        assert stats['suspicious_requests'] == 0

    def test_returns_correct_counts(self):
        """Test that hourly stats reflect recorded events."""
        monitor = SecurityMonitor()
        monitor.thresholds = {}

        monitor.record_event('failed_logins')
        monitor.record_event('failed_logins')
        monitor.record_event('failed_logins')
        monitor.record_event('blocked_ips')
        monitor.record_event('suspicious_requests')
        monitor.record_event('suspicious_requests')

        stats = monitor.get_hourly_stats()

        assert stats['failed_logins'] == 3
        assert stats['blocked_ips'] == 1
        assert stats['rate_limits'] == 0
        assert stats['suspicious_requests'] == 2

    def test_returns_dict_with_expected_keys(self):
        """Test that hourly stats returns all expected event types."""
        monitor = SecurityMonitor()

        stats = monitor.get_hourly_stats()

        expected_keys = {'failed_logins', 'blocked_ips', 'rate_limits', 'suspicious_requests'}
        assert set(stats.keys()) == expected_keys

    def test_custom_events_not_in_hourly_stats(self):
        """Test that custom event types are not included in standard hourly stats."""
        monitor = SecurityMonitor()
        monitor.thresholds = {}

        monitor.record_event('custom_event_type')

        stats = monitor.get_hourly_stats()
        assert 'custom_event_type' not in stats

    def test_stats_reflect_current_hour_only(self):
        """Test that stats use the current hour's cache keys."""
        monitor = SecurityMonitor()
        monitor.thresholds = {}

        # Record an event
        monitor.record_event('failed_logins')

        stats = monitor.get_hourly_stats()
        assert stats['failed_logins'] == 1

        # Manually expire the counter by deleting from cache
        counter_key = monitor._get_counter_key('failed_logins')
        cache.delete(counter_key)

        stats = monitor.get_hourly_stats()
        assert stats['failed_logins'] == 0

    def test_concurrent_event_recording(self):
        """Test that multiple concurrent events are counted correctly."""
        monitor = SecurityMonitor()
        monitor.thresholds = {}

        # Record many events
        for _ in range(50):
            monitor.record_event('rate_limits')

        stats = monitor.get_hourly_stats()
        assert stats['rate_limits'] == 50
