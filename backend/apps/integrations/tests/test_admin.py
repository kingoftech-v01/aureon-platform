"""
Tests for integrations admin configuration.

Covers:
- IntegrationAdmin registration, list_display, list_filter, search_fields, readonly_fields
- IntegrationSyncLogAdmin registration, list_display, list_filter, readonly_fields
"""

import pytest
from django.contrib import admin
from django.contrib.admin.sites import AdminSite

from apps.integrations.models import Integration, IntegrationSyncLog
from apps.integrations.admin import IntegrationAdmin, IntegrationSyncLogAdmin


@pytest.fixture
def site():
    return AdminSite()


@pytest.fixture
def int_admin(site):
    return IntegrationAdmin(Integration, site)


@pytest.fixture
def sync_log_admin(site):
    return IntegrationSyncLogAdmin(IntegrationSyncLog, site)


class TestIntegrationAdmin:

    def test_registered(self):
        assert Integration in admin.site._registry

    def test_list_display(self, int_admin):
        expected = ['name', 'service_type', 'status', 'sync_enabled', 'last_sync_at', 'created_at']
        assert int_admin.list_display == expected

    def test_list_filter(self, int_admin):
        assert 'service_type' in int_admin.list_filter
        assert 'status' in int_admin.list_filter
        assert 'sync_enabled' in int_admin.list_filter

    def test_search_fields(self, int_admin):
        assert 'name' in int_admin.search_fields

    def test_readonly_fields(self, int_admin):
        expected = ['id', 'created_at', 'updated_at']
        assert int_admin.readonly_fields == expected

    def test_admin_class_type(self, int_admin):
        assert isinstance(int_admin, admin.ModelAdmin)


class TestIntegrationSyncLogAdmin:

    def test_registered(self):
        assert IntegrationSyncLog in admin.site._registry

    def test_list_display(self, sync_log_admin):
        expected = ['integration', 'status', 'records_synced', 'duration_ms', 'started_at']
        assert sync_log_admin.list_display == expected

    def test_list_filter(self, sync_log_admin):
        assert 'status' in sync_log_admin.list_filter

    def test_readonly_fields(self, sync_log_admin):
        expected = ['id', 'started_at']
        assert sync_log_admin.readonly_fields == expected

    def test_admin_class_type(self, sync_log_admin):
        assert isinstance(sync_log_admin, admin.ModelAdmin)
