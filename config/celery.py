"""
Celery configuration for Finance SaaS Platform.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('finance_saas')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat Schedule
app.conf.beat_schedule = {
    # Invoice generation
    'generate-recurring-invoices': {
        'task': 'apps.invoicing.tasks.generate_recurring_invoices',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
    # Send payment reminders
    'send-payment-reminders': {
        'task': 'apps.invoicing.tasks.send_payment_reminders',
        'schedule': crontab(hour=9, minute=0),  # Daily at 9 AM
    },
    # Process subscription renewals
    'process-subscription-renewals': {
        'task': 'apps.subscriptions.tasks.process_subscription_renewals',
        'schedule': crontab(hour=1, minute=0),  # Daily at 1 AM
    },
    # Sync Stripe data
    'sync-stripe-data': {
        'task': 'apps.payments.tasks.sync_stripe_data',
        'schedule': crontab(hour='*/6'),  # Every 6 hours
    },
    # Clean up expired sessions
    'cleanup-expired-sessions': {
        'task': 'apps.core.tasks.cleanup_expired_sessions',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    # Generate analytics reports
    'generate-daily-analytics': {
        'task': 'apps.analytics.tasks.generate_daily_analytics',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
    },
    # Check contract expirations
    'check-contract-expirations': {
        'task': 'apps.contracts.tasks.check_contract_expirations',
        'schedule': crontab(hour=8, minute=0),  # Daily at 8 AM
    },
    # Backup critical data
    'backup-critical-data': {
        'task': 'apps.core.tasks.backup_critical_data',
        'schedule': crontab(hour=4, minute=0, day_of_week=0),  # Weekly on Sunday at 4 AM
    },
}

# Celery configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing."""
    print(f'Request: {self.request!r}')
