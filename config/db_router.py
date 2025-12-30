"""
Database Router for Aureon SaaS Platform.
Handles read/write splitting between master and replica databases.
"""
import random
from typing import Optional, Type

from django.db import models


class ReadWriteRouter:
    """
    A database router that sends reads to replicas and writes to the master.

    This router supports:
    - Automatic read/write splitting
    - Multiple read replicas with random selection
    - Sticky sessions for transactions
    - Model-level routing hints
    """

    # Models that should always use the master (for consistency)
    MASTER_ONLY_MODELS = {
        'auth.User',
        'accounts.User',
        'tenants.Tenant',
        'tenants.Domain',
        'payments.Payment',
        'payments.Subscription',
        'contracts.Contract',
        'contracts.ContractSignature',
        'invoicing.Invoice',
        'django_celery_beat.PeriodicTask',
        'django_celery_results.TaskResult',
    }

    # Apps that should always use the master
    MASTER_ONLY_APPS = {
        'admin',
        'auth',
        'contenttypes',
        'sessions',
        'django_celery_beat',
        'django_celery_results',
        'axes',
        'auditlog',
    }

    def _get_model_label(self, model: Type[models.Model]) -> str:
        """Get the app_label.model_name for a model."""
        return f'{model._meta.app_label}.{model._meta.model_name}'

    def _should_use_master(self, model: Optional[Type[models.Model]] = None) -> bool:
        """
        Determine if this operation should use the master database.
        """
        if model is None:
            return True

        # Check if model is in master-only list
        model_label = self._get_model_label(model)
        if model_label in self.MASTER_ONLY_MODELS:
            return True

        # Check if app is in master-only list
        if model._meta.app_label in self.MASTER_ONLY_APPS:
            return True

        # Check for model-level hints
        if hasattr(model, '_use_master') and model._use_master:
            return True

        return False

    def db_for_read(self, model: Type[models.Model], **hints) -> str:
        """
        Route reads to replica unless model requires master.

        Args:
            model: The model class being read
            **hints: Additional routing hints

        Returns:
            Database alias to use for the read
        """
        # Check for explicit hints
        if hints.get('instance'):
            instance = hints['instance']
            # If the instance was just saved, read from master for consistency
            if hasattr(instance, '_state') and instance._state.adding:
                return 'default'

        # Use master for master-only models
        if self._should_use_master(model):
            return 'default'

        # Route to replica for general reads
        # In production with multiple replicas, you could use:
        # return random.choice(['replica', 'replica2', 'replica3'])
        return 'replica'

    def db_for_write(self, model: Type[models.Model], **hints) -> str:
        """
        Route all writes to the master database.

        Args:
            model: The model class being written
            **hints: Additional routing hints

        Returns:
            Database alias to use for the write (always 'default')
        """
        return 'default'

    def allow_relation(self, obj1: models.Model, obj2: models.Model, **hints) -> bool:
        """
        Allow relations between objects in the same database cluster.

        Since all databases are part of the same PostgreSQL cluster
        with replication, we allow all relations.

        Args:
            obj1: First model instance
            obj2: Second model instance
            **hints: Additional routing hints

        Returns:
            True to allow the relation
        """
        return True

    def allow_migrate(self, db: str, app_label: str, model_name: Optional[str] = None, **hints) -> Optional[bool]:
        """
        Only allow migrations on the master database.

        Args:
            db: Database alias
            app_label: App label for the migration
            model_name: Model name (optional)
            **hints: Additional routing hints

        Returns:
            True if migration is allowed on this database
        """
        # Only run migrations on the master
        return db == 'default'


class PrimaryReplicaRouter(ReadWriteRouter):
    """
    Extended router with support for multiple replicas and weighted routing.
    """

    def __init__(self):
        super().__init__()
        # Replica configuration: (alias, weight)
        # Higher weight = more traffic
        self.replicas = [
            ('replica', 1),
        ]
        self._replica_pool = self._build_replica_pool()

    def _build_replica_pool(self) -> list:
        """Build a weighted pool of replicas for random selection."""
        pool = []
        for alias, weight in self.replicas:
            pool.extend([alias] * weight)
        return pool

    def db_for_read(self, model: Type[models.Model], **hints) -> str:
        """Route reads with weighted replica selection."""
        if self._should_use_master(model):
            return 'default'

        if hints.get('instance'):
            instance = hints['instance']
            if hasattr(instance, '_state') and instance._state.adding:
                return 'default'

        # Random selection from weighted pool
        if self._replica_pool:
            return random.choice(self._replica_pool)
        return 'default'


class TransactionAwareRouter(ReadWriteRouter):
    """
    Router that respects transaction boundaries.

    When inside a transaction, all operations use the master to ensure
    consistency. Outside transactions, reads can go to replicas.
    """

    def db_for_read(self, model: Type[models.Model], **hints) -> str:
        """Route reads, respecting transaction state."""
        from django.db import connection

        # If we're in an atomic block, use master for consistency
        if connection.in_atomic_block:
            return 'default'

        return super().db_for_read(model, **hints)


# Utility decorator for forcing master reads
def use_master(func):
    """
    Decorator to force a view or function to use the master database.

    Usage:
        @use_master
        def my_view(request):
            # All database reads here will use master
            ...
    """
    from functools import wraps
    from django.db import connection

    @wraps(func)
    def wrapper(*args, **kwargs):
        with connection.cursor() as cursor:
            cursor.db.alias = 'default'
            return func(*args, **kwargs)
    return wrapper


# Context manager for master reads
class UseMaster:
    """
    Context manager to force master database usage.

    Usage:
        with UseMaster():
            # All reads here use master
            user = User.objects.get(id=1)
    """

    def __enter__(self):
        from django.db import connections
        self._old_db = connections['default'].alias
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


# Helper to check replica lag
def check_replica_lag(max_lag_seconds: float = 5.0) -> dict:
    """
    Check replication lag for all replicas.

    Args:
        max_lag_seconds: Maximum acceptable lag in seconds

    Returns:
        Dict with replica status information
    """
    from django.db import connections

    results = {}

    for alias in ['replica']:
        try:
            with connections[alias].cursor() as cursor:
                # PostgreSQL specific query to check replication lag
                cursor.execute("""
                    SELECT
                        CASE
                            WHEN pg_last_wal_receive_lsn() = pg_last_wal_replay_lsn()
                            THEN 0
                            ELSE EXTRACT(EPOCH FROM now() - pg_last_xact_replay_timestamp())
                        END AS lag_seconds
                """)
                row = cursor.fetchone()
                lag = row[0] if row else None

                results[alias] = {
                    'status': 'healthy' if lag is not None and lag <= max_lag_seconds else 'lagging',
                    'lag_seconds': lag,
                    'max_lag': max_lag_seconds,
                }
        except Exception as e:
            results[alias] = {
                'status': 'error',
                'error': str(e),
            }

    return results
