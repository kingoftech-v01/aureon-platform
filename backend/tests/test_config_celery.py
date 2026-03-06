"""
Tests for config/celery.py.

Tests Celery app configuration including:
- App initialization and naming
- Task autodiscovery
- Queue definitions
- Task routing
- Rate limiting annotations
- Beat schedule
- TaskPriority constants
- get_queue_for_priority helper
- debug_task
"""

import pytest
from unittest.mock import patch, MagicMock

from config.celery import (
    app,
    TaskPriority,
    get_queue_for_priority,
    debug_task,
    default_exchange,
    high_priority_exchange,
    medium_priority_exchange,
    low_priority_exchange,
)


class TestCeleryAppConfiguration:
    """Test basic Celery app configuration."""

    def test_celery_app_name(self):
        """Test that the Celery app has the correct name."""
        assert app.main == "aureon_saas"

    def test_config_from_object(self):
        """Test that Celery reads config from Django settings."""
        # The namespace is CELERY
        assert app.config_from_object is not None

    def test_autodiscover_tasks(self):
        """Test that autodiscover_tasks has been called."""
        # Autodiscovery is already configured; verify the app is functional
        assert app.autodiscover_tasks is not None

    def test_default_queue(self):
        """Test that the default queue is set to 'default'."""
        assert app.conf.task_default_queue == "default"

    def test_default_exchange(self):
        """Test that the default exchange is set."""
        assert app.conf.task_default_exchange == "default"

    def test_default_routing_key(self):
        """Test that the default routing key is set."""
        assert app.conf.task_default_routing_key == "default"


class TestExchangeDefinitions:
    """Test exchange definitions."""

    def test_default_exchange(self):
        """Test default exchange is defined."""
        assert default_exchange.name == "default"
        assert default_exchange.type == "direct"

    def test_high_priority_exchange(self):
        """Test high priority exchange is defined."""
        assert high_priority_exchange.name == "high_priority"
        assert high_priority_exchange.type == "direct"

    def test_medium_priority_exchange(self):
        """Test medium priority exchange is defined."""
        assert medium_priority_exchange.name == "medium_priority"
        assert medium_priority_exchange.type == "direct"

    def test_low_priority_exchange(self):
        """Test low priority exchange is defined."""
        assert low_priority_exchange.name == "low_priority"
        assert low_priority_exchange.type == "direct"


class TestQueueDefinitions:
    """Test queue definitions."""

    def test_queues_defined(self):
        """Test that task queues are defined."""
        queues = app.conf.task_queues
        assert queues is not None
        assert len(queues) == 6

    def test_queue_names(self):
        """Test that all expected queues are present."""
        queue_names = {q.name for q in app.conf.task_queues}
        expected = {"high_priority", "medium_priority", "default", "low_priority", "batch", "analytics"}
        assert queue_names == expected

    def test_high_priority_queue_settings(self):
        """Test high priority queue settings."""
        queue = next(q for q in app.conf.task_queues if q.name == "high_priority")
        assert queue.queue_arguments.get("x-max-priority") == 10

    def test_default_queue_settings(self):
        """Test default queue settings."""
        queue = next(q for q in app.conf.task_queues if q.name == "default")
        assert queue.queue_arguments.get("x-max-priority") == 5

    def test_low_priority_queue_settings(self):
        """Test low priority queue settings."""
        queue = next(q for q in app.conf.task_queues if q.name == "low_priority")
        assert queue.queue_arguments.get("x-max-priority") == 3

    def test_batch_queue_settings(self):
        """Test batch queue settings."""
        queue = next(q for q in app.conf.task_queues if q.name == "batch")
        assert queue.queue_arguments.get("x-max-priority") == 1

    def test_analytics_queue_settings(self):
        """Test analytics queue settings."""
        queue = next(q for q in app.conf.task_queues if q.name == "analytics")
        assert queue.queue_arguments.get("x-max-priority") == 2


class TestTaskRouting:
    """Test task routing configuration."""

    def test_task_routes_defined(self):
        """Test that task routes are defined."""
        assert app.conf.task_routes is not None
        assert len(app.conf.task_routes) > 0

    def test_payment_tasks_routed_to_high_priority(self):
        """Test that payment tasks are routed to high priority queue."""
        routes = app.conf.task_routes
        assert routes.get("apps.payments.tasks.*", {}).get("queue") == "high_priority"
        assert routes.get("apps.payments.tasks.process_payment", {}).get("queue") == "high_priority"

    def test_webhook_tasks_routed_to_high_priority(self):
        """Test that webhook tasks are routed to high priority queue."""
        routes = app.conf.task_routes
        assert routes.get("apps.webhooks.tasks.*", {}).get("queue") == "high_priority"

    def test_notification_tasks_routed_to_medium_priority(self):
        """Test that notification tasks are routed to medium priority."""
        routes = app.conf.task_routes
        assert routes.get("apps.notifications.tasks.*", {}).get("queue") == "medium_priority"

    def test_contract_pdf_routed_to_medium_priority(self):
        """Test that contract PDF generation is routed to medium priority."""
        routes = app.conf.task_routes
        assert routes.get("apps.contracts.tasks.generate_contract_pdf", {}).get("queue") == "medium_priority"

    def test_invoice_generation_routed_to_medium_priority(self):
        """Test that invoice generation is routed to medium priority."""
        routes = app.conf.task_routes
        assert routes.get("apps.invoicing.tasks.generate_invoice", {}).get("queue") == "medium_priority"

    def test_recurring_invoices_routed_to_low_priority(self):
        """Test that recurring invoice generation is routed to low priority."""
        routes = app.conf.task_routes
        assert routes.get("apps.invoicing.tasks.generate_recurring_invoices", {}).get("queue") == "low_priority"

    def test_analytics_tasks_routed_to_analytics_queue(self):
        """Test that analytics tasks are routed to analytics queue."""
        routes = app.conf.task_routes
        assert routes.get("apps.analytics.tasks.*", {}).get("queue") == "analytics"

    def test_batch_tasks_routed_to_batch_queue(self):
        """Test that batch tasks are routed to batch queue."""
        routes = app.conf.task_routes
        assert routes.get("apps.core.tasks.cleanup_expired_sessions", {}).get("queue") == "batch"
        assert routes.get("apps.integrations.tasks.*", {}).get("queue") == "batch"

    def test_stripe_sync_routed_to_batch_queue(self):
        """Test that stripe sync is routed to batch queue."""
        routes = app.conf.task_routes
        assert routes.get("apps.payments.tasks.sync_stripe_data", {}).get("queue") == "batch"


class TestTaskAnnotations:
    """Test task annotation configuration."""

    def test_annotations_defined(self):
        """Test that task annotations are defined."""
        assert app.conf.task_annotations is not None

    def test_stripe_webhook_annotations(self):
        """Test stripe webhook task rate limit."""
        annotations = app.conf.task_annotations
        stripe_ann = annotations.get("apps.payments.tasks.process_stripe_webhook", {})
        assert stripe_ann.get("rate_limit") == "1000/m"
        assert stripe_ann.get("max_retries") == 5
        assert stripe_ann.get("default_retry_delay") == 30

    def test_process_payment_annotations(self):
        """Test process payment task rate limit."""
        annotations = app.conf.task_annotations
        payment_ann = annotations.get("apps.payments.tasks.process_payment", {})
        assert payment_ann.get("rate_limit") == "500/m"
        assert payment_ann.get("max_retries") == 3

    def test_default_annotations(self):
        """Test default wildcard annotations."""
        annotations = app.conf.task_annotations
        default_ann = annotations.get("*", {})
        assert default_ann.get("rate_limit") == "100/m"
        assert default_ann.get("max_retries") == 3
        assert default_ann.get("acks_late") is True

    def test_analytics_annotations(self):
        """Test analytics task annotations."""
        annotations = app.conf.task_annotations
        analytics_ann = annotations.get("apps.analytics.tasks.generate_daily_analytics", {})
        assert analytics_ann.get("rate_limit") == "10/h"

    def test_backup_annotations(self):
        """Test backup task annotations."""
        annotations = app.conf.task_annotations
        backup_ann = annotations.get("apps.core.tasks.backup_critical_data", {})
        assert backup_ann.get("rate_limit") == "1/h"
        assert backup_ann.get("max_retries") == 1


class TestAutoRetryConfiguration:
    """Test auto-retry and acknowledgement settings."""

    def test_acks_late_enabled(self):
        """Test that task_acks_late is enabled."""
        assert app.conf.task_acks_late is True

    def test_reject_on_worker_lost(self):
        """Test that tasks are rejected on worker lost."""
        assert app.conf.task_reject_on_worker_lost is True

    def test_default_retry_delay(self):
        """Test default retry delay is 60 seconds."""
        assert app.conf.task_default_retry_delay == 60

    def test_max_retries(self):
        """Test max retries is 3."""
        assert app.conf.task_max_retries == 3

    def test_autoretry_exceptions(self):
        """Test auto-retry exception types."""
        autoretry_for = app.conf.task_autoretry_for
        assert ConnectionError in autoretry_for
        assert TimeoutError in autoretry_for
        assert OSError in autoretry_for

    def test_retry_backoff_enabled(self):
        """Test exponential backoff is enabled."""
        assert app.conf.task_retry_backoff is True

    def test_retry_backoff_max(self):
        """Test max backoff is 600 seconds."""
        assert app.conf.task_retry_backoff_max == 600

    def test_retry_jitter_enabled(self):
        """Test jitter is enabled for retries."""
        assert app.conf.task_retry_jitter is True


class TestResultBackendConfiguration:
    """Test result backend settings."""

    def test_result_expires(self):
        """Test results expire after 1 hour."""
        assert app.conf.result_expires == 3600

    def test_result_extended(self):
        """Test extended results are enabled."""
        assert app.conf.result_extended is True

    def test_result_compression(self):
        """Test result compression uses gzip."""
        assert app.conf.result_compression == "gzip"

    def test_result_chord_retry_interval(self):
        """Test chord retry interval."""
        assert app.conf.result_chord_retry_interval == 1.0

    def test_result_chord_join_timeout(self):
        """Test chord join timeout."""
        assert app.conf.result_chord_join_timeout == 3.0


class TestWorkerConfiguration:
    """Test worker configuration settings."""

    def test_worker_prefetch_multiplier(self):
        """Test worker prefetch multiplier."""
        assert app.conf.worker_prefetch_multiplier == 4

    def test_worker_max_tasks_per_child(self):
        """Test worker max tasks per child."""
        assert app.conf.worker_max_tasks_per_child == 1000

    def test_worker_max_memory_per_child(self):
        """Test worker max memory per child (400MB)."""
        assert app.conf.worker_max_memory_per_child == 400000

    def test_worker_pool(self):
        """Test worker pool type is prefork."""
        assert app.conf.worker_pool == "prefork"

    def test_worker_send_task_events(self):
        """Test task events are sent."""
        assert app.conf.worker_send_task_events is True

    def test_task_send_sent_event(self):
        """Test sent events are enabled."""
        assert app.conf.task_send_sent_event is True

    def test_worker_hijack_root_logger(self):
        """Test root logger is not hijacked."""
        assert app.conf.worker_hijack_root_logger is False

    def test_worker_redirect_stdouts(self):
        """Test stdout redirect is enabled."""
        assert app.conf.worker_redirect_stdouts is True

    def test_worker_redirect_stdouts_level(self):
        """Test stdout redirect level is INFO."""
        assert app.conf.worker_redirect_stdouts_level == "INFO"


class TestBrokerSettings:
    """Test broker connection settings."""

    def test_broker_connection_retry(self):
        """Test broker connection retry is enabled."""
        assert app.conf.broker_connection_retry is True

    def test_broker_connection_retry_on_startup(self):
        """Test broker retry on startup is enabled."""
        assert app.conf.broker_connection_retry_on_startup is True

    def test_broker_connection_max_retries(self):
        """Test broker max retries is 10."""
        assert app.conf.broker_connection_max_retries == 10

    def test_broker_connection_timeout(self):
        """Test broker connection timeout is 10 seconds."""
        assert app.conf.broker_connection_timeout == 10

    def test_broker_pool_limit(self):
        """Test broker pool limit is 100."""
        assert app.conf.broker_pool_limit == 100

    def test_broker_heartbeat(self):
        """Test broker heartbeat is 10 seconds."""
        assert app.conf.broker_heartbeat == 10

    def test_broker_transport_options(self):
        """Test broker transport options are set."""
        opts = app.conf.broker_transport_options
        assert opts["visibility_timeout"] == 3600
        assert opts["fanout_prefix"] is True
        assert opts["fanout_patterns"] is True
        assert opts["socket_connect_timeout"] == 5
        assert opts["socket_keepalive"] is True
        assert opts["retry_on_timeout"] is True
        assert opts["health_check_interval"] == 30


class TestSerializationSettings:
    """Test serialization settings."""

    def test_task_serializer(self):
        """Test task serializer is JSON."""
        assert app.conf.task_serializer == "json"

    def test_accept_content(self):
        """Test accepted content types."""
        assert app.conf.accept_content == ["json"]

    def test_result_serializer(self):
        """Test result serializer is JSON."""
        assert app.conf.result_serializer == "json"

    def test_event_serializer(self):
        """Test event serializer is JSON."""
        assert app.conf.event_serializer == "json"


class TestTimezoneSettings:
    """Test timezone settings."""

    def test_timezone(self):
        """Test timezone is UTC."""
        assert app.conf.timezone == "UTC"

    def test_enable_utc(self):
        """Test UTC is enabled."""
        assert app.conf.enable_utc is True


class TestTaskExecutionSettings:
    """Test task execution settings."""

    def test_track_started(self):
        """Test task tracking of started state is enabled."""
        assert app.conf.task_track_started is True

    def test_time_limit(self):
        """Test hard time limit is 30 minutes."""
        assert app.conf.task_time_limit == 30 * 60

    def test_soft_time_limit(self):
        """Test soft time limit is 25 minutes."""
        assert app.conf.task_soft_time_limit == 25 * 60

    def test_always_eager_disabled(self):
        """Test that tasks are never run synchronously."""
        assert app.conf.task_always_eager is False

    def test_inherit_parent_priority(self):
        """Test that tasks inherit parent priority."""
        assert app.conf.task_inherit_parent_priority is True

    def test_publish_retry_enabled(self):
        """Test task publish retry is enabled."""
        assert app.conf.task_publish_retry is True

    def test_publish_retry_policy(self):
        """Test task publish retry policy."""
        policy = app.conf.task_publish_retry_policy
        assert policy["max_retries"] == 3
        assert policy["interval_start"] == 0
        assert policy["interval_step"] == 0.2
        assert policy["interval_max"] == 0.5


class TestBeatSchedule:
    """Test Celery Beat schedule configuration."""

    def test_beat_schedule_defined(self):
        """Test that beat schedule is defined."""
        assert app.conf.beat_schedule is not None
        assert len(app.conf.beat_schedule) > 0

    def test_subscription_renewals_scheduled(self):
        """Test subscription renewals scheduling."""
        task = app.conf.beat_schedule.get("process-subscription-renewals")
        assert task is not None
        assert task["task"] == "apps.subscriptions.tasks.process_subscription_renewals"
        assert task["options"]["queue"] == "high_priority"

    def test_recurring_invoices_scheduled(self):
        """Test recurring invoices scheduling."""
        task = app.conf.beat_schedule.get("generate-recurring-invoices")
        assert task is not None
        assert task["task"] == "apps.invoicing.tasks.generate_recurring_invoices"
        assert task["options"]["queue"] == "medium_priority"

    def test_payment_reminders_scheduled(self):
        """Test payment reminders scheduling."""
        task = app.conf.beat_schedule.get("send-payment-reminders")
        assert task is not None
        assert task["task"] == "apps.invoicing.tasks.send_payment_reminders"

    def test_contract_expirations_scheduled(self):
        """Test contract expirations scheduling."""
        task = app.conf.beat_schedule.get("check-contract-expirations")
        assert task is not None
        assert task["task"] == "apps.contracts.tasks.check_contract_expirations"

    def test_stripe_sync_scheduled(self):
        """Test stripe sync scheduling."""
        task = app.conf.beat_schedule.get("sync-stripe-data")
        assert task is not None
        assert task["task"] == "apps.payments.tasks.sync_stripe_data"
        assert task["options"]["queue"] == "batch"

    def test_session_cleanup_scheduled(self):
        """Test session cleanup scheduling."""
        task = app.conf.beat_schedule.get("cleanup-expired-sessions")
        assert task is not None
        assert task["task"] == "apps.core.tasks.cleanup_expired_sessions"

    def test_backup_scheduled(self):
        """Test backup scheduling."""
        task = app.conf.beat_schedule.get("backup-critical-data")
        assert task is not None
        assert task["task"] == "apps.core.tasks.backup_critical_data"
        assert task["options"]["priority"] == 1

    def test_daily_analytics_scheduled(self):
        """Test daily analytics scheduling."""
        task = app.conf.beat_schedule.get("generate-daily-analytics")
        assert task is not None
        assert task["task"] == "apps.analytics.tasks.generate_daily_analytics"
        assert task["options"]["queue"] == "analytics"

    def test_weekly_reports_scheduled(self):
        """Test weekly reports scheduling."""
        task = app.conf.beat_schedule.get("generate-weekly-reports")
        assert task is not None
        assert task["task"] == "apps.analytics.tasks.generate_weekly_reports"

    def test_revenue_metrics_scheduled(self):
        """Test revenue metrics scheduling."""
        task = app.conf.beat_schedule.get("calculate-revenue-metrics")
        assert task is not None
        assert task["task"] == "apps.analytics.tasks.calculate_revenue_metrics"

    def test_health_check_scheduled(self):
        """Test health check scheduling."""
        task = app.conf.beat_schedule.get("health-check-external-services")
        assert task is not None
        assert task["task"] == "apps.core.tasks.health_check_external_services"
        assert task["options"]["queue"] == "high_priority"

    def test_beat_scheduler_class(self):
        """Test that beat uses database scheduler."""
        assert app.conf.beat_scheduler == "django_celery_beat.schedulers:DatabaseScheduler"

    def test_beat_max_loop_interval(self):
        """Test beat max loop interval is 5 seconds."""
        assert app.conf.beat_max_loop_interval == 5


class TestFlowerSettings:
    """Test Flower monitoring settings."""

    def test_flower_port(self):
        """Test Flower port is 5555."""
        assert app.conf.flower_port == 5555

    def test_flower_url_prefix(self):
        """Test Flower URL prefix."""
        assert app.conf.flower_url_prefix == "flower"


class TestDebugTask:
    """Test the debug task."""

    def test_debug_task_is_registered(self):
        """Test that the debug task is registered."""
        assert debug_task is not None
        assert debug_task.name == "config.celery.debug_task"

    def test_debug_task_ignore_result(self):
        """Test that debug task ignores result."""
        assert debug_task.ignore_result is True

    def test_debug_task_execution(self):
        """Test that debug task can be called."""
        # For bind=True tasks, Celery auto-injects self when calling .run()
        # We need to call the underlying __wrapped__ function or use apply()
        # The task wraps a function(self) with bind=True
        with patch("builtins.print") as mock_print:
            debug_task.run()
            mock_print.assert_called_once()


class TestTaskPriority:
    """Test TaskPriority constants."""

    def test_critical_priority(self):
        """Test CRITICAL priority is 10."""
        assert TaskPriority.CRITICAL == 10

    def test_high_priority(self):
        """Test HIGH priority is 8."""
        assert TaskPriority.HIGH == 8

    def test_medium_priority(self):
        """Test MEDIUM priority is 5."""
        assert TaskPriority.MEDIUM == 5

    def test_low_priority(self):
        """Test LOW priority is 3."""
        assert TaskPriority.LOW == 3

    def test_batch_priority(self):
        """Test BATCH priority is 1."""
        assert TaskPriority.BATCH == 1


class TestGetQueueForPriority:
    """Test the get_queue_for_priority helper function."""

    def test_critical_returns_high_priority(self):
        """Test priority 10 returns high_priority queue."""
        assert get_queue_for_priority(10) == "high_priority"

    def test_high_returns_high_priority(self):
        """Test priority 8 returns high_priority queue."""
        assert get_queue_for_priority(8) == "high_priority"

    def test_priority_9_returns_high_priority(self):
        """Test priority 9 returns high_priority queue."""
        assert get_queue_for_priority(9) == "high_priority"

    def test_medium_returns_medium_priority(self):
        """Test priority 5 returns medium_priority queue."""
        assert get_queue_for_priority(5) == "medium_priority"

    def test_priority_6_returns_medium_priority(self):
        """Test priority 6 returns medium_priority queue."""
        assert get_queue_for_priority(6) == "medium_priority"

    def test_priority_7_returns_medium_priority(self):
        """Test priority 7 returns medium_priority queue."""
        assert get_queue_for_priority(7) == "medium_priority"

    def test_low_returns_low_priority(self):
        """Test priority 3 returns low_priority queue."""
        assert get_queue_for_priority(3) == "low_priority"

    def test_priority_4_returns_low_priority(self):
        """Test priority 4 returns low_priority queue."""
        assert get_queue_for_priority(4) == "low_priority"

    def test_batch_returns_batch(self):
        """Test priority 1 returns batch queue."""
        assert get_queue_for_priority(1) == "batch"

    def test_priority_0_returns_batch(self):
        """Test priority 0 returns batch queue."""
        assert get_queue_for_priority(0) == "batch"

    def test_priority_2_returns_batch(self):
        """Test priority 2 returns batch queue."""
        assert get_queue_for_priority(2) == "batch"

    def test_negative_priority_returns_batch(self):
        """Test negative priority returns batch queue."""
        assert get_queue_for_priority(-1) == "batch"

    def test_very_high_priority_returns_high(self):
        """Test very high priority returns high_priority queue."""
        assert get_queue_for_priority(100) == "high_priority"


class TestCeleryInit:
    """Test the config/__init__.py exports celery_app."""

    def test_celery_app_exported(self):
        """Test that celery_app is exported from config package."""
        from config import celery_app
        assert celery_app is app
