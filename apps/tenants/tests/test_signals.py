"""
Tests for tenants app signals.
"""

import pytest
import logging
from apps.tenants.models import Tenant, Domain


@pytest.mark.django_db
class TestTenantSignals:
    """Tests for tenant signals."""

    def test_log_tenant_creation(self, caplog):
        """Test that creating a new tenant triggers a log message."""
        with caplog.at_level(logging.INFO, logger='aureon.tenants'):
            tenant = Tenant(
                name='Signal Test Tenant',
                slug='signal-test-tenant',
                schema_name='signal_test_tenant',
                contact_email='signal@test.com',
            )
            tenant.save()
        assert 'New tenant created' in caplog.text
        assert 'Signal Test Tenant' in caplog.text

    def test_no_log_on_tenant_update(self, tenant, caplog):
        """Test that updating a tenant does not trigger creation log."""
        with caplog.at_level(logging.INFO, logger='aureon.tenants'):
            caplog.clear()
            tenant.name = 'Updated Tenant Name'
            tenant.save()
        assert 'New tenant created' not in caplog.text


@pytest.mark.django_db
class TestDomainSignals:
    """Tests for domain signals."""

    def test_log_domain_creation(self, tenant, caplog):
        """Test that creating a new domain triggers a log message."""
        with caplog.at_level(logging.INFO, logger='aureon.tenants'):
            domain = Domain.objects.create(
                tenant=tenant,
                domain='signal-domain.aureon.local',
                is_primary=False,
            )
        assert 'New domain created' in caplog.text
        assert 'signal-domain.aureon.local' in caplog.text

    def test_no_log_on_domain_update(self, domain, caplog):
        """Test that updating a domain does not trigger creation log."""
        with caplog.at_level(logging.INFO, logger='aureon.tenants'):
            caplog.clear()
            domain.ssl_enabled = False
            domain.save()
        assert 'New domain created' not in caplog.text
