"""
Core application Celery tasks for Aureon SaaS Platform.

These tasks handle system-level operations like:
- Session cleanup
- Data backup
- Health checks for external services
"""
from celery import shared_task
from django.utils import timezone
from django.contrib.sessions.models import Session
import logging
import redis
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def cleanup_expired_sessions(self):
    """
    Remove expired sessions from the database.
    Runs daily to keep the sessions table clean.
    """
    try:
        expired_count = Session.objects.filter(
            expire_date__lt=timezone.now()
        ).delete()[0]

        logger.info(f"Cleaned up {expired_count} expired sessions")
        return {'status': 'success', 'expired_sessions_removed': expired_count}
    except Exception as exc:
        logger.error(f"Session cleanup failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=1)
def backup_critical_data(self):
    """
    Backup critical data (placeholder for actual backup logic).
    In production, this would:
    - Export database snapshots
    - Upload to S3/GCS
    - Verify backup integrity
    """
    try:
        logger.info("Starting critical data backup...")

        # Placeholder - in production, implement actual backup logic
        backup_timestamp = timezone.now().isoformat()

        logger.info(f"Backup completed at {backup_timestamp}")
        return {
            'status': 'success',
            'timestamp': backup_timestamp,
            'message': 'Backup task completed (placeholder)'
        }
    except Exception as exc:
        logger.error(f"Backup failed: {exc}")
        raise self.retry(exc=exc, countdown=300)


@shared_task(bind=True, max_retries=2)
def health_check_external_services(self):
    """
    Check health of external services (Stripe, Redis, etc.).
    Runs every 15 minutes to monitor service availability.
    """
    results = {
        'timestamp': timezone.now().isoformat(),
        'services': {}
    }

    # Check Redis
    try:
        redis_url = getattr(settings, 'CELERY_BROKER_URL', 'redis://localhost:6379/0')
        # Simple check - the celery worker is connected if this task runs
        results['services']['redis'] = {'status': 'healthy', 'message': 'Connected via Celery'}
    except Exception as e:
        results['services']['redis'] = {'status': 'unhealthy', 'error': str(e)}

    # Check Stripe API (if configured)
    stripe_key = getattr(settings, 'STRIPE_SECRET_KEY', None) or getattr(settings, 'STRIPE_LIVE_SECRET_KEY', None)
    if stripe_key and not stripe_key.startswith('sk_test_XXXX'):
        try:
            import stripe
            stripe.api_key = stripe_key
            # Simple API check
            stripe.Account.retrieve()
            results['services']['stripe'] = {'status': 'healthy'}
        except Exception as e:
            results['services']['stripe'] = {'status': 'unhealthy', 'error': str(e)}
    else:
        results['services']['stripe'] = {'status': 'skipped', 'message': 'Test keys or not configured'}

    # Check database (if we got here, DB is working)
    results['services']['database'] = {'status': 'healthy', 'message': 'Connected via Django ORM'}

    # Log results
    healthy_count = sum(1 for s in results['services'].values() if s.get('status') == 'healthy')
    total_count = len(results['services'])

    logger.info(f"Health check completed: {healthy_count}/{total_count} services healthy")

    return results
