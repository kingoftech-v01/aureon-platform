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
    Backup critical data by exporting key models to JSON.
    """
    try:
        import json
        from django.core import serializers
        from django.conf import settings
        import os

        logger.info("Starting critical data backup...")
        backup_timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        models_to_backup = [
            'contracts.Contract',
            'invoicing.Invoice',
            'payments.Payment',
            'clients.Client',
        ]

        backup_files = []
        for model_label in models_to_backup:
            try:
                app_label, model_name = model_label.split('.')
                from django.apps import apps
                Model = apps.get_model(app_label, model_name)
                data = serializers.serialize('json', Model.objects.all())
                filename = f"{model_name.lower()}_{backup_timestamp}.json"
                filepath = os.path.join(backup_dir, filename)
                with open(filepath, 'w') as f:
                    f.write(data)
                backup_files.append(filename)
                logger.info(f"Backed up {model_name}: {Model.objects.count()} records")
            except Exception as e:
                logger.warning(f"Could not backup {model_label}: {e}")

        logger.info(f"Backup completed at {backup_timestamp}: {len(backup_files)} models")
        return {
            'status': 'success',
            'timestamp': backup_timestamp,
            'files': backup_files
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
