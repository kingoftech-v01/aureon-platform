"""
Tests for config/db_router.py.

Tests database routing including:
- ReadWriteRouter (read/write splitting)
- PrimaryReplicaRouter (weighted replicas)
- TransactionAwareRouter (transaction-safe routing)
- use_master decorator
- UseMaster context manager
- check_replica_lag utility
"""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from django.db import models

from config.db_router import (
    ReadWriteRouter,
    PrimaryReplicaRouter,
    TransactionAwareRouter,
    use_master,
    UseMaster,
    check_replica_lag,
)


# ============================================================================
# Helper models for testing
# ============================================================================

class MockModel:
    """Mock model for testing routing."""
    class _meta:
        app_label = "myapp"
        model_name = "mymodel"


class MockUserModel:
    """Mock User model in accounts app."""
    class _meta:
        app_label = "accounts"
        model_name = "User"


class MockPaymentModel:
    """Mock Payment model."""
    class _meta:
        app_label = "payments"
        model_name = "Payment"


class MockContractModel:
    """Mock Contract model."""
    class _meta:
        app_label = "contracts"
        model_name = "Contract"


class MockSessionModel:
    """Mock Session model in sessions app."""
    class _meta:
        app_label = "sessions"
        model_name = "session"


class MockAuthModel:
    """Mock auth model."""
    class _meta:
        app_label = "auth"
        model_name = "User"


class MockAdminModel:
    """Mock admin model."""
    class _meta:
        app_label = "admin"
        model_name = "logentry"


class MockCeleryBeatModel:
    """Mock django_celery_beat model."""
    class _meta:
        app_label = "django_celery_beat"
        model_name = "PeriodicTask"


class MockAuditModel:
    """Mock audit model."""
    class _meta:
        app_label = "auditlog"
        model_name = "logentry"


class MockAxesModel:
    """Mock axes model."""
    class _meta:
        app_label = "axes"
        model_name = "accessattempt"


class MockTenantModel:
    """Mock Tenant model."""
    class _meta:
        app_label = "tenants"
        model_name = "Tenant"


class MockDomainModel:
    """Mock Domain model."""
    class _meta:
        app_label = "tenants"
        model_name = "Domain"


class MockSubscriptionModel:
    """Mock Subscription model."""
    class _meta:
        app_label = "payments"
        model_name = "Subscription"


class MockContractSignatureModel:
    """Mock ContractSignature model."""
    class _meta:
        app_label = "contracts"
        model_name = "ContractSignature"


class MockInvoiceModel:
    """Mock Invoice model."""
    class _meta:
        app_label = "invoicing"
        model_name = "Invoice"


class MockMasterFlagModel:
    """Mock model with _use_master flag."""
    _use_master = True

    class _meta:
        app_label = "myapp"
        model_name = "mastermodel"


class MockNoMasterFlagModel:
    """Mock model with _use_master False."""
    _use_master = False

    class _meta:
        app_label = "myapp"
        model_name = "nomastermodel"


class MockContentTypesModel:
    """Mock contenttypes model."""
    class _meta:
        app_label = "contenttypes"
        model_name = "contenttype"


# ============================================================================
# ReadWriteRouter Tests
# ============================================================================

class TestReadWriteRouter:
    """Test the ReadWriteRouter."""

    def setup_method(self):
        self.router = ReadWriteRouter()

    # --- _get_model_label ---

    def test_get_model_label(self):
        """Test model label generation."""
        label = self.router._get_model_label(MockModel)
        assert label == "myapp.mymodel"

    def test_get_model_label_auth(self):
        """Test model label for auth.User."""
        label = self.router._get_model_label(MockAuthModel)
        assert label == "auth.User"

    # --- _should_use_master ---

    def test_should_use_master_none_model(self):
        """Test that None model defaults to master."""
        assert self.router._should_use_master(None) is True

    def test_should_use_master_for_master_only_models(self):
        """Test master-only models use master."""
        assert self.router._should_use_master(MockAuthModel) is True
        assert self.router._should_use_master(MockPaymentModel) is True
        assert self.router._should_use_master(MockContractModel) is True
        assert self.router._should_use_master(MockTenantModel) is True
        assert self.router._should_use_master(MockDomainModel) is True
        assert self.router._should_use_master(MockSubscriptionModel) is True
        assert self.router._should_use_master(MockContractSignatureModel) is True
        assert self.router._should_use_master(MockInvoiceModel) is True

    def test_should_use_master_for_master_only_apps(self):
        """Test master-only apps use master."""
        assert self.router._should_use_master(MockAdminModel) is True
        assert self.router._should_use_master(MockSessionModel) is True
        assert self.router._should_use_master(MockCeleryBeatModel) is True
        assert self.router._should_use_master(MockAxesModel) is True
        assert self.router._should_use_master(MockAuditModel) is True
        assert self.router._should_use_master(MockContentTypesModel) is True

    def test_should_use_master_model_hint(self):
        """Test model with _use_master flag."""
        assert self.router._should_use_master(MockMasterFlagModel) is True

    def test_should_not_use_master_for_regular_models(self):
        """Test regular models do not use master."""
        assert self.router._should_use_master(MockModel) is False

    def test_should_not_use_master_false_flag(self):
        """Test model with _use_master=False."""
        assert self.router._should_use_master(MockNoMasterFlagModel) is False

    # --- db_for_read ---

    def test_db_for_read_regular_model(self):
        """Test reads of regular models go to replica."""
        db = self.router.db_for_read(MockModel)
        assert db == "replica"

    def test_db_for_read_master_only_model(self):
        """Test reads of master-only models go to master."""
        db = self.router.db_for_read(MockPaymentModel)
        assert db == "default"

    def test_db_for_read_master_only_app(self):
        """Test reads of master-only app models go to master."""
        db = self.router.db_for_read(MockSessionModel)
        assert db == "default"

    def test_db_for_read_with_adding_instance_hint(self):
        """Test that reads for just-saved instances use master."""
        instance = MagicMock()
        instance._state.adding = True
        db = self.router.db_for_read(MockModel, instance=instance)
        assert db == "default"

    def test_db_for_read_with_non_adding_instance_hint(self):
        """Test that reads for existing instances can use replica."""
        instance = MagicMock()
        instance._state.adding = False
        db = self.router.db_for_read(MockModel, instance=instance)
        assert db == "replica"

    def test_db_for_read_no_hints(self):
        """Test reads without hints."""
        db = self.router.db_for_read(MockModel)
        assert db == "replica"

    def test_db_for_read_auth_user(self):
        """Test reads for auth user go to master."""
        db = self.router.db_for_read(MockAuthModel)
        assert db == "default"

    def test_db_for_read_accounts_user(self):
        """Test reads for accounts user go to master."""
        db = self.router.db_for_read(MockUserModel)
        assert db == "default"

    # --- db_for_write ---

    def test_db_for_write_always_default(self):
        """Test all writes go to master."""
        assert self.router.db_for_write(MockModel) == "default"
        assert self.router.db_for_write(MockPaymentModel) == "default"
        assert self.router.db_for_write(MockSessionModel) == "default"

    def test_db_for_write_with_hints(self):
        """Test writes with hints still go to master."""
        assert self.router.db_for_write(MockModel, instance=MagicMock()) == "default"

    # --- allow_relation ---

    def test_allow_relation_always_true(self):
        """Test all relations are allowed."""
        obj1 = MagicMock()
        obj2 = MagicMock()
        assert self.router.allow_relation(obj1, obj2) is True

    def test_allow_relation_same_model(self):
        """Test self-relations are allowed."""
        obj = MagicMock()
        assert self.router.allow_relation(obj, obj) is True

    def test_allow_relation_with_hints(self):
        """Test allow_relation with hints."""
        obj1 = MagicMock()
        obj2 = MagicMock()
        assert self.router.allow_relation(obj1, obj2, some_hint="value") is True

    # --- allow_migrate ---

    def test_allow_migrate_on_default(self):
        """Test migrations are allowed on default database."""
        assert self.router.allow_migrate("default", "myapp") is True

    def test_allow_migrate_on_replica(self):
        """Test migrations are not allowed on replica."""
        assert self.router.allow_migrate("replica", "myapp") is False

    def test_allow_migrate_on_other_db(self):
        """Test migrations are not allowed on other databases."""
        assert self.router.allow_migrate("other", "myapp") is False

    def test_allow_migrate_with_model_name(self):
        """Test allow_migrate with model_name parameter."""
        assert self.router.allow_migrate("default", "myapp", model_name="MyModel") is True
        assert self.router.allow_migrate("replica", "myapp", model_name="MyModel") is False

    def test_allow_migrate_with_hints(self):
        """Test allow_migrate with hints."""
        assert self.router.allow_migrate("default", "myapp", some_hint=True) is True


# ============================================================================
# PrimaryReplicaRouter Tests
# ============================================================================

class TestPrimaryReplicaRouter:
    """Test the PrimaryReplicaRouter."""

    def setup_method(self):
        self.router = PrimaryReplicaRouter()

    def test_inherits_from_read_write_router(self):
        """Test that PrimaryReplicaRouter extends ReadWriteRouter."""
        assert isinstance(self.router, ReadWriteRouter)

    def test_replicas_configured(self):
        """Test that replicas are configured."""
        assert len(self.router.replicas) == 1
        assert self.router.replicas[0] == ("replica", 1)

    def test_replica_pool_built(self):
        """Test that replica pool is built from configuration."""
        assert len(self.router._replica_pool) == 1
        assert "replica" in self.router._replica_pool

    def test_build_replica_pool(self):
        """Test _build_replica_pool method."""
        pool = self.router._build_replica_pool()
        assert pool == ["replica"]

    def test_build_replica_pool_weighted(self):
        """Test weighted replica pool building."""
        self.router.replicas = [("replica1", 2), ("replica2", 1)]
        pool = self.router._build_replica_pool()
        assert pool.count("replica1") == 2
        assert pool.count("replica2") == 1

    def test_db_for_read_master_only_model(self):
        """Test reads of master-only models go to default."""
        db = self.router.db_for_read(MockPaymentModel)
        assert db == "default"

    def test_db_for_read_regular_model(self):
        """Test reads of regular models go to replica pool."""
        db = self.router.db_for_read(MockModel)
        assert db in self.router._replica_pool

    def test_db_for_read_with_adding_instance(self):
        """Test reads for just-saved instances go to default."""
        instance = MagicMock()
        instance._state.adding = True
        db = self.router.db_for_read(MockModel, instance=instance)
        assert db == "default"

    def test_db_for_read_empty_pool_fallback(self):
        """Test fallback to default when replica pool is empty."""
        self.router._replica_pool = []
        db = self.router.db_for_read(MockModel)
        assert db == "default"

    def test_db_for_write(self):
        """Test writes still go to default."""
        assert self.router.db_for_write(MockModel) == "default"

    def test_allow_relation(self):
        """Test relations are allowed."""
        assert self.router.allow_relation(MagicMock(), MagicMock()) is True

    def test_allow_migrate_default(self):
        """Test migrations allowed on default."""
        assert self.router.allow_migrate("default", "myapp") is True

    def test_allow_migrate_replica(self):
        """Test migrations not allowed on replica."""
        assert self.router.allow_migrate("replica", "myapp") is False


# ============================================================================
# TransactionAwareRouter Tests
# ============================================================================

class TestTransactionAwareRouter:
    """Test the TransactionAwareRouter."""

    def setup_method(self):
        self.router = TransactionAwareRouter()

    def test_inherits_from_read_write_router(self):
        """Test that TransactionAwareRouter extends ReadWriteRouter."""
        assert isinstance(self.router, ReadWriteRouter)

    @patch("django.db.connection")
    def test_db_for_read_in_atomic_block(self, mock_connection):
        """Test reads in atomic block use master."""
        mock_connection.in_atomic_block = True
        db = self.router.db_for_read(MockModel)
        assert db == "default"

    @patch("django.db.connection")
    def test_db_for_read_outside_atomic_block(self, mock_connection):
        """Test reads outside atomic block use normal routing."""
        mock_connection.in_atomic_block = False
        db = self.router.db_for_read(MockModel)
        assert db == "replica"

    @patch("django.db.connection")
    def test_db_for_read_master_model_in_atomic(self, mock_connection):
        """Test master-only model reads in atomic block use master."""
        mock_connection.in_atomic_block = True
        db = self.router.db_for_read(MockPaymentModel)
        assert db == "default"

    @patch("django.db.connection")
    def test_db_for_read_master_model_outside_atomic(self, mock_connection):
        """Test master-only model reads outside atomic block still use master."""
        mock_connection.in_atomic_block = False
        db = self.router.db_for_read(MockPaymentModel)
        assert db == "default"

    def test_db_for_write(self):
        """Test writes always use default."""
        assert self.router.db_for_write(MockModel) == "default"


# ============================================================================
# use_master decorator Tests
# ============================================================================

class TestUseMasterDecorator:
    """Test the use_master decorator."""

    def test_decorator_preserves_function_name(self):
        """Test that the decorator preserves the function name."""
        @use_master
        def my_func():
            return "test"

        assert my_func.__name__ == "my_func"

    @patch("django.db.connection")
    def test_decorator_sets_alias_to_default(self, mock_connection):
        """Test that the decorator forces default database."""
        mock_cursor = MagicMock()
        mock_cursor.db.alias = "replica"
        mock_connection.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_connection.cursor.return_value.__exit__ = MagicMock(return_value=False)

        @use_master
        def my_func():
            return "result"

        result = my_func()
        assert result == "result"

    def test_decorator_returns_function_result(self):
        """Test that the decorator passes through the function's return value."""
        @use_master
        def add(a, b):
            return a + b

        with patch("django.db.connection"):
            result = add(3, 4)
            assert result == 7


# ============================================================================
# UseMaster context manager Tests
# ============================================================================

class TestUseMasterContextManager:
    """Test the UseMaster context manager."""

    @patch("django.db.connections")
    def test_context_manager_enter(self, mock_connections):
        """Test entering the context manager."""
        mock_connections.__getitem__.return_value.alias = "default"

        with UseMaster() as ctx:
            assert ctx is not None

    @patch("django.db.connections")
    def test_context_manager_exit(self, mock_connections):
        """Test exiting the context manager."""
        mock_connections.__getitem__.return_value.alias = "default"

        with UseMaster():
            pass
        # Should not raise

    @patch("django.db.connections")
    def test_context_manager_stores_old_db(self, mock_connections):
        """Test that the context manager stores the old database alias."""
        mock_connections.__getitem__.return_value.alias = "replica"

        cm = UseMaster()
        cm.__enter__()
        assert cm._old_db == "replica"
        cm.__exit__(None, None, None)


# ============================================================================
# check_replica_lag Tests
# ============================================================================

class TestCheckReplicaLag:
    """Test the check_replica_lag function."""

    @patch("django.db.connections")
    def test_healthy_replica(self, mock_connections):
        """Test healthy replica with low lag."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1.5,)
        mock_connections.__getitem__.return_value.cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor
        )
        mock_connections.__getitem__.return_value.cursor.return_value.__exit__ = MagicMock(
            return_value=False
        )

        results = check_replica_lag(max_lag_seconds=5.0)
        assert "replica" in results
        assert results["replica"]["status"] == "healthy"
        assert results["replica"]["lag_seconds"] == 1.5

    @patch("django.db.connections")
    def test_lagging_replica(self, mock_connections):
        """Test lagging replica with high lag."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (10.5,)
        mock_connections.__getitem__.return_value.cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor
        )
        mock_connections.__getitem__.return_value.cursor.return_value.__exit__ = MagicMock(
            return_value=False
        )

        results = check_replica_lag(max_lag_seconds=5.0)
        assert results["replica"]["status"] == "lagging"
        assert results["replica"]["lag_seconds"] == 10.5

    @patch("django.db.connections")
    def test_replica_error(self, mock_connections):
        """Test replica with connection error."""
        mock_connections.__getitem__.return_value.cursor.return_value.__enter__ = MagicMock(
            side_effect=Exception("Connection refused")
        )

        results = check_replica_lag()
        assert results["replica"]["status"] == "error"
        assert "Connection refused" in results["replica"]["error"]

    @patch("django.db.connections")
    def test_replica_zero_lag(self, mock_connections):
        """Test replica with zero lag (fully caught up)."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (0,)
        mock_connections.__getitem__.return_value.cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor
        )
        mock_connections.__getitem__.return_value.cursor.return_value.__exit__ = MagicMock(
            return_value=False
        )

        results = check_replica_lag()
        assert results["replica"]["status"] == "healthy"
        assert results["replica"]["lag_seconds"] == 0

    @patch("django.db.connections")
    def test_replica_none_lag(self, mock_connections):
        """Test replica with None lag value."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (None,)
        mock_connections.__getitem__.return_value.cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor
        )
        mock_connections.__getitem__.return_value.cursor.return_value.__exit__ = MagicMock(
            return_value=False
        )

        results = check_replica_lag()
        assert results["replica"]["status"] == "lagging"

    @patch("django.db.connections")
    def test_replica_empty_fetchone(self, mock_connections):
        """Test replica when fetchone returns None."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_connections.__getitem__.return_value.cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor
        )
        mock_connections.__getitem__.return_value.cursor.return_value.__exit__ = MagicMock(
            return_value=False
        )

        results = check_replica_lag()
        assert results["replica"]["status"] == "lagging"

    def test_custom_max_lag(self):
        """Test custom max_lag_seconds parameter."""
        with patch("django.db.connections") as mock_connections:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = (3.0,)
            mock_connections.__getitem__.return_value.cursor.return_value.__enter__ = MagicMock(
                return_value=mock_cursor
            )
            mock_connections.__getitem__.return_value.cursor.return_value.__exit__ = MagicMock(
                return_value=False
            )

            # With max_lag=2, 3 seconds lag is too high
            results = check_replica_lag(max_lag_seconds=2.0)
            assert results["replica"]["status"] == "lagging"
            assert results["replica"]["max_lag"] == 2.0


# ============================================================================
# MASTER_ONLY Constants Tests
# ============================================================================

class TestMasterOnlyConstants:
    """Test MASTER_ONLY_MODELS and MASTER_ONLY_APPS constants."""

    def test_master_only_models_contains_auth_user(self):
        """Test that auth.User is in master-only models."""
        assert "auth.User" in ReadWriteRouter.MASTER_ONLY_MODELS

    def test_master_only_models_contains_accounts_user(self):
        """Test that accounts.User is in master-only models."""
        assert "accounts.User" in ReadWriteRouter.MASTER_ONLY_MODELS

    def test_master_only_models_contains_tenant(self):
        """Test that tenants.Tenant is in master-only models."""
        assert "tenants.Tenant" in ReadWriteRouter.MASTER_ONLY_MODELS

    def test_master_only_models_contains_payment(self):
        """Test that payments.Payment is in master-only models."""
        assert "payments.Payment" in ReadWriteRouter.MASTER_ONLY_MODELS

    def test_master_only_models_contains_contract(self):
        """Test that contracts.Contract is in master-only models."""
        assert "contracts.Contract" in ReadWriteRouter.MASTER_ONLY_MODELS

    def test_master_only_models_contains_invoice(self):
        """Test that invoicing.Invoice is in master-only models."""
        assert "invoicing.Invoice" in ReadWriteRouter.MASTER_ONLY_MODELS

    def test_master_only_apps_contains_admin(self):
        """Test that admin is in master-only apps."""
        assert "admin" in ReadWriteRouter.MASTER_ONLY_APPS

    def test_master_only_apps_contains_auth(self):
        """Test that auth is in master-only apps."""
        assert "auth" in ReadWriteRouter.MASTER_ONLY_APPS

    def test_master_only_apps_contains_sessions(self):
        """Test that sessions is in master-only apps."""
        assert "sessions" in ReadWriteRouter.MASTER_ONLY_APPS

    def test_master_only_apps_contains_celery_beat(self):
        """Test that django_celery_beat is in master-only apps."""
        assert "django_celery_beat" in ReadWriteRouter.MASTER_ONLY_APPS

    def test_master_only_apps_contains_celery_results(self):
        """Test that django_celery_results is in master-only apps."""
        assert "django_celery_results" in ReadWriteRouter.MASTER_ONLY_APPS

    def test_master_only_apps_contains_axes(self):
        """Test that axes is in master-only apps."""
        assert "axes" in ReadWriteRouter.MASTER_ONLY_APPS

    def test_master_only_apps_contains_auditlog(self):
        """Test that auditlog is in master-only apps."""
        assert "auditlog" in ReadWriteRouter.MASTER_ONLY_APPS

    def test_master_only_apps_contains_contenttypes(self):
        """Test that contenttypes is in master-only apps."""
        assert "contenttypes" in ReadWriteRouter.MASTER_ONLY_APPS
