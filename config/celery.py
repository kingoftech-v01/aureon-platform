"""
Celery configuration for Aureon SaaS Platform.
Optimized for 1M users and 500K concurrent connections.

Features:
- Priority-based task routing (high/medium/low queues)
- Auto-retry with exponential backoff
- Rate limiting per task type
- Worker concurrency optimization
- Result backend optimization with Redis cluster
"""
import os
from celery import Celery
from celery.schedules import crontab
from kombu import Queue, Exchange

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('aureon_saas')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# ====================
# EXCHANGE DEFINITIONS
# ====================
default_exchange = Exchange('default', type='direct')
high_priority_exchange = Exchange('high_priority', type='direct')
medium_priority_exchange = Exchange('medium_priority', type='direct')
low_priority_exchange = Exchange('low_priority', type='direct')

# ====================
# QUEUE DEFINITIONS
# ====================
app.conf.task_queues = (
    # High priority - Payment processing, webhooks, critical notifications
    Queue('high_priority', high_priority_exchange, routing_key='high',
          queue_arguments={'x-max-priority': 10}),

    # Medium priority - Email sending, contract generation, invoice creation
    Queue('medium_priority', medium_priority_exchange, routing_key='medium',
          queue_arguments={'x-max-priority': 5}),

    # Default queue - General tasks
    Queue('default', default_exchange, routing_key='default',
          queue_arguments={'x-max-priority': 5}),

    # Low priority - Analytics, reporting, batch processing
    Queue('low_priority', low_priority_exchange, routing_key='low',
          queue_arguments={'x-max-priority': 3}),

    # Batch processing - Large data operations
    Queue('batch', low_priority_exchange, routing_key='batch',
          queue_arguments={'x-max-priority': 1}),

    # Analytics - Reporting and metrics
    Queue('analytics', low_priority_exchange, routing_key='analytics',
          queue_arguments={'x-max-priority': 2}),
)

# ====================
# TASK ROUTING
# ====================
app.conf.task_routes = {
    # High Priority Tasks - Payment and Critical Operations
    'apps.payments.tasks.*': {'queue': 'high_priority', 'routing_key': 'high'},
    'apps.webhooks.tasks.*': {'queue': 'high_priority', 'routing_key': 'high'},
    'apps.payments.tasks.process_stripe_webhook': {'queue': 'high_priority'},
    'apps.payments.tasks.process_payment': {'queue': 'high_priority'},
    'apps.payments.tasks.retry_failed_payment': {'queue': 'high_priority'},
    'apps.subscriptions.tasks.process_subscription_payment': {'queue': 'high_priority'},

    # Medium Priority Tasks - User-facing Operations
    'apps.notifications.tasks.*': {'queue': 'medium_priority', 'routing_key': 'medium'},
    'apps.contracts.tasks.generate_contract_pdf': {'queue': 'medium_priority'},
    'apps.contracts.tasks.send_contract_for_signature': {'queue': 'medium_priority'},
    'apps.invoicing.tasks.generate_invoice': {'queue': 'medium_priority'},
    'apps.invoicing.tasks.send_invoice_email': {'queue': 'medium_priority'},
    'apps.documents.tasks.process_document': {'queue': 'medium_priority'},

    # Low Priority Tasks - Background Operations
    'apps.invoicing.tasks.generate_recurring_invoices': {'queue': 'low_priority', 'routing_key': 'low'},
    'apps.invoicing.tasks.send_payment_reminders': {'queue': 'low_priority'},
    'apps.subscriptions.tasks.process_subscription_renewals': {'queue': 'low_priority'},
    'apps.contracts.tasks.check_contract_expirations': {'queue': 'low_priority'},

    # Batch Processing Tasks
    'apps.core.tasks.cleanup_expired_sessions': {'queue': 'batch', 'routing_key': 'batch'},
    'apps.core.tasks.backup_critical_data': {'queue': 'batch'},
    'apps.payments.tasks.sync_stripe_data': {'queue': 'batch'},
    'apps.integrations.tasks.*': {'queue': 'batch'},

    # Analytics Tasks
    'apps.analytics.tasks.*': {'queue': 'analytics', 'routing_key': 'analytics'},
    'apps.analytics.tasks.generate_daily_analytics': {'queue': 'analytics'},
    'apps.analytics.tasks.calculate_revenue_metrics': {'queue': 'analytics'},
}

# ====================
# DEFAULT QUEUE ROUTING
# ====================
app.conf.task_default_queue = 'default'
app.conf.task_default_exchange = 'default'
app.conf.task_default_routing_key = 'default'

# ====================
# RATE LIMITING PER TASK TYPE
# ====================
app.conf.task_annotations = {
    # High priority tasks - Higher rate limits
    'apps.payments.tasks.process_stripe_webhook': {
        'rate_limit': '1000/m',  # 1000 per minute
        'max_retries': 5,
        'default_retry_delay': 30,
    },
    'apps.payments.tasks.process_payment': {
        'rate_limit': '500/m',
        'max_retries': 3,
        'default_retry_delay': 60,
    },

    # Medium priority tasks
    'apps.notifications.tasks.send_pending_notifications': {
        'rate_limit': '300/m',  # Respect email provider limits
        'max_retries': 3,
        'default_retry_delay': 120,
    },
    'apps.contracts.tasks.generate_contract_pdf': {
        'rate_limit': '100/m',  # CPU intensive
        'max_retries': 2,
    },
    'apps.invoicing.tasks.generate_invoice': {
        'rate_limit': '200/m',
        'max_retries': 3,
    },

    # Low priority tasks - More conservative limits
    'apps.analytics.tasks.generate_daily_analytics': {
        'rate_limit': '10/h',
        'max_retries': 2,
    },
    'apps.core.tasks.backup_critical_data': {
        'rate_limit': '1/h',
        'max_retries': 1,
    },
    'apps.payments.tasks.sync_stripe_data': {
        'rate_limit': '5/h',  # Stripe API limits
        'max_retries': 3,
    },

    # Default annotations for all tasks
    '*': {
        'rate_limit': '100/m',
        'max_retries': 3,
        'acks_late': True,
    },
}

# ====================
# AUTO-RETRY CONFIGURATION
# ====================
app.conf.task_acks_late = True
app.conf.task_reject_on_worker_lost = True

# Default retry settings
app.conf.task_default_retry_delay = 60  # 1 minute
app.conf.task_max_retries = 3

# Retry with exponential backoff (base settings)
app.conf.task_autoretry_for = (
    ConnectionError,
    TimeoutError,
    OSError,
)
app.conf.task_retry_backoff = True
app.conf.task_retry_backoff_max = 600  # Max 10 minutes
app.conf.task_retry_jitter = True

# ====================
# RESULT BACKEND OPTIMIZATION
# ====================
app.conf.result_backend = os.environ.get(
    'CELERY_RESULT_BACKEND',
    'redis://:${REDIS_PASSWORD}@redis-result:6379/0'
)

# Result settings
app.conf.result_expires = 3600  # Results expire after 1 hour
app.conf.result_extended = True
app.conf.result_compression = 'gzip'

# Result backend optimization for high throughput
app.conf.result_chord_retry_interval = 1.0
app.conf.result_chord_join_timeout = 3.0

# ====================
# WORKER CONFIGURATION
# ====================
# Worker concurrency settings (optimized for containers)
app.conf.worker_concurrency = int(os.environ.get('CELERY_WORKER_CONCURRENCY', 4))
app.conf.worker_prefetch_multiplier = 4  # Prefetch 4 tasks per worker
app.conf.worker_max_tasks_per_child = 1000  # Restart worker after 1000 tasks
app.conf.worker_max_memory_per_child = 400000  # 400MB per worker

# Worker pool settings
app.conf.worker_pool = 'prefork'  # Use prefork for CPU-bound tasks

# Enable task events for monitoring
app.conf.worker_send_task_events = True
app.conf.task_send_sent_event = True

# Worker hijack settings
app.conf.worker_hijack_root_logger = False
app.conf.worker_redirect_stdouts = True
app.conf.worker_redirect_stdouts_level = 'INFO'

# ====================
# BROKER SETTINGS (Redis Cluster Ready)
# ====================
app.conf.broker_url = os.environ.get(
    'CELERY_BROKER_URL',
    'redis://:${REDIS_PASSWORD}@redis-queue:6379/1'
)

# Broker connection settings
app.conf.broker_connection_retry = True
app.conf.broker_connection_retry_on_startup = True
app.conf.broker_connection_max_retries = 10
app.conf.broker_connection_timeout = 10

# Broker pool settings for high concurrency
app.conf.broker_pool_limit = 100
app.conf.broker_heartbeat = 10

# Broker transport options for Redis
app.conf.broker_transport_options = {
    'visibility_timeout': 3600,  # 1 hour
    'fanout_prefix': True,
    'fanout_patterns': True,
    'socket_connect_timeout': 5,
    'socket_keepalive': True,
    'socket_timeout': 5,
    'retry_on_timeout': True,
    'health_check_interval': 30,
    # Redis Sentinel support (for high availability)
    # 'master_name': 'aureon-master',
    # 'sentinel_kwargs': {'password': os.environ.get('REDIS_PASSWORD')},
}

# ====================
# SERIALIZATION
# ====================
app.conf.task_serializer = 'json'
app.conf.accept_content = ['json']
app.conf.result_serializer = 'json'
app.conf.event_serializer = 'json'

# ====================
# TIMEZONE
# ====================
app.conf.timezone = 'UTC'
app.conf.enable_utc = True

# ====================
# TASK EXECUTION SETTINGS
# ====================
app.conf.task_track_started = True
app.conf.task_time_limit = 30 * 60  # 30 minutes hard limit
app.conf.task_soft_time_limit = 25 * 60  # 25 minutes soft limit
# Note: task_always_eager should be False in production.
# This is enforced via CELERY_TASK_ALWAYS_EAGER in Django settings.
# Test settings may override to True for synchronous test execution.

# Task priority (higher = more priority)
app.conf.task_inherit_parent_priority = True

# Task publishing settings
app.conf.task_publish_retry = True
app.conf.task_publish_retry_policy = {
    'max_retries': 3,
    'interval_start': 0,
    'interval_step': 0.2,
    'interval_max': 0.5,
}

# ====================
# CELERY BEAT SCHEDULE
# ====================
app.conf.beat_schedule = {
    # High Priority Scheduled Tasks
    'process-subscription-renewals': {
        'task': 'apps.subscriptions.tasks.process_subscription_renewals',
        'schedule': crontab(hour=1, minute=0),  # Daily at 1 AM
        'options': {'queue': 'high_priority', 'priority': 9},
    },

    # Medium Priority Scheduled Tasks
    'generate-recurring-invoices': {
        'task': 'apps.invoicing.tasks.generate_recurring_invoices',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
        'options': {'queue': 'medium_priority', 'priority': 5},
    },
    'send-payment-reminders': {
        'task': 'apps.invoicing.tasks.send_payment_reminders',
        'schedule': crontab(hour=9, minute=0),  # Daily at 9 AM
        'options': {'queue': 'medium_priority', 'priority': 5},
    },
    'check-contract-expirations': {
        'task': 'apps.contracts.tasks.check_contract_expirations',
        'schedule': crontab(hour=8, minute=0),  # Daily at 8 AM
        'options': {'queue': 'medium_priority', 'priority': 5},
    },

    # Low Priority / Batch Scheduled Tasks
    'sync-stripe-data': {
        'task': 'apps.payments.tasks.sync_stripe_data',
        'schedule': crontab(hour='*/6'),  # Every 6 hours
        'options': {'queue': 'batch', 'priority': 3},
    },
    'cleanup-expired-sessions': {
        'task': 'apps.core.tasks.cleanup_expired_sessions',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
        'options': {'queue': 'batch', 'priority': 2},
    },
    'backup-critical-data': {
        'task': 'apps.core.tasks.backup_critical_data',
        'schedule': crontab(hour=4, minute=0, day_of_week=0),  # Weekly on Sunday at 4 AM
        'options': {'queue': 'batch', 'priority': 1},
    },

    # Analytics Scheduled Tasks
    'generate-daily-analytics': {
        'task': 'apps.analytics.tasks.generate_daily_analytics',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
        'options': {'queue': 'analytics', 'priority': 2},
    },
    'generate-weekly-reports': {
        'task': 'apps.analytics.tasks.generate_weekly_reports',
        'schedule': crontab(hour=5, minute=0, day_of_week=1),  # Monday at 5 AM
        'options': {'queue': 'analytics', 'priority': 2},
    },
    'calculate-revenue-metrics': {
        'task': 'apps.analytics.tasks.calculate_revenue_metrics',
        'schedule': crontab(hour='*/4'),  # Every 4 hours
        'options': {'queue': 'analytics', 'priority': 3},
    },

    # Health Check Tasks
    'health-check-external-services': {
        'task': 'apps.core.tasks.health_check_external_services',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
        'options': {'queue': 'high_priority', 'priority': 8},
    },
}

# Beat scheduler settings
app.conf.beat_scheduler = 'django_celery_beat.schedulers:DatabaseScheduler'
app.conf.beat_max_loop_interval = 5  # Check for new tasks every 5 seconds


# ====================
# FLOWER MONITORING SETTINGS
# ====================
app.conf.flower_port = 5555
app.conf.flower_url_prefix = 'flower'


# ====================
# DEBUG TASK
# ====================
@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing."""
    print(f'Request: {self.request!r}')


# ====================
# TASK PRIORITY HELPERS
# ====================
class TaskPriority:
    """Task priority constants for consistent priority assignment."""
    CRITICAL = 10
    HIGH = 8
    MEDIUM = 5
    LOW = 3
    BATCH = 1


def get_queue_for_priority(priority):
    """Get the appropriate queue name for a given priority level."""
    if priority >= 8:
        return 'high_priority'
    elif priority >= 5:
        return 'medium_priority'
    elif priority >= 3:
        return 'low_priority'
    else:
        return 'batch'
