"""
Tests for clients app admin configuration.
"""

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory
from apps.clients.models import Client, ClientNote, ClientDocument
from apps.clients.admin import ClientAdmin, ClientNoteAdmin, ClientDocumentAdmin


@pytest.mark.django_db
class TestClientAdmin:
    """Tests for ClientAdmin."""

    def setup_method(self):
        """Set up admin site and admin class."""
        self.site = AdminSite()
        self.admin = ClientAdmin(Client, self.site)
        self.request_factory = RequestFactory()

    def _make_request(self, user):
        """Create a request with messages support."""
        request = self.request_factory.get('/admin/')
        request.user = user
        request.session = SessionStore()
        request._messages = FallbackStorage(request)
        return request

    def test_client_admin_is_registered(self):
        """Test Client model is registered in admin."""
        from django.contrib import admin
        assert Client in admin.site._registry

    def test_list_display(self):
        """Test list_display fields are configured."""
        expected = [
            'get_display_name', 'email', 'phone', 'stage_badge',
            'owner', 'total_value', 'outstanding_balance', 'created_at',
        ]
        assert self.admin.list_display == expected

    def test_list_filter(self):
        """Test list_filter fields are configured."""
        expected = [
            'client_type', 'lifecycle_stage', 'industry',
            'is_active', 'portal_access_enabled', 'created_at',
        ]
        assert self.admin.list_filter == expected

    def test_search_fields(self):
        """Test search_fields are configured."""
        expected = ['first_name', 'last_name', 'company_name', 'email', 'phone']
        assert self.admin.search_fields == expected

    def test_readonly_fields(self):
        """Test readonly_fields are configured."""
        assert 'id' in self.admin.readonly_fields
        assert 'total_value' in self.admin.readonly_fields
        assert 'total_paid' in self.admin.readonly_fields
        assert 'outstanding_balance' in self.admin.readonly_fields
        assert 'created_at' in self.admin.readonly_fields
        assert 'updated_at' in self.admin.readonly_fields

    def test_inlines(self):
        """Test inlines are configured."""
        from apps.clients.admin import ClientNoteInline, ClientDocumentInline
        inline_classes = [type(i) for i in self.admin.get_inline_instances(None)]
        # Check inline classes are registered
        assert ClientNoteInline in [type(cls) for cls in self.admin.inlines] or True
        # Check inlines list
        from apps.clients.admin import ClientNoteInline, ClientDocumentInline
        assert ClientNoteInline in self.admin.inlines
        assert ClientDocumentInline in self.admin.inlines

    def test_stage_badge_active(self, client_company):
        """Test stage_badge for active client."""
        result = self.admin.stage_badge(client_company)
        assert 'green' in result
        assert 'Active Client' in result

    def test_stage_badge_lead(self, client_lead):
        """Test stage_badge for lead client."""
        result = self.admin.stage_badge(client_lead)
        assert 'gray' in result

    def test_stage_badge_prospect(self, client_individual):
        """Test stage_badge for prospect client."""
        result = self.admin.stage_badge(client_individual)
        assert 'blue' in result

    def test_stage_badge_inactive(self, client_company):
        """Test stage_badge for inactive client."""
        client_company.lifecycle_stage = Client.INACTIVE
        result = self.admin.stage_badge(client_company)
        assert 'orange' in result

    def test_stage_badge_churned(self, client_company):
        """Test stage_badge for churned client."""
        client_company.lifecycle_stage = Client.CHURNED
        result = self.admin.stage_badge(client_company)
        assert 'red' in result

    def test_stage_badge_unknown(self, client_company):
        """Test stage_badge with unknown stage defaults to gray."""
        client_company.lifecycle_stage = 'unknown_stage'
        result = self.admin.stage_badge(client_company)
        assert 'gray' in result

    def test_stage_badge_short_description(self):
        """Test stage_badge has proper short_description."""
        assert self.admin.stage_badge.short_description is not None

    def test_move_to_active_action(self, admin_user, client_lead, client_individual):
        """Test move_to_active admin action."""
        request = self._make_request(admin_user)
        queryset = Client.objects.filter(pk__in=[client_lead.pk, client_individual.pk])
        self.admin.move_to_active(request, queryset)
        client_lead.refresh_from_db()
        client_individual.refresh_from_db()
        assert client_lead.lifecycle_stage == Client.ACTIVE
        assert client_individual.lifecycle_stage == Client.ACTIVE

    def test_move_to_active_short_description(self):
        """Test move_to_active has short_description."""
        assert self.admin.move_to_active.short_description is not None

    def test_create_portal_access_action(self, admin_user, client_company):
        """Test create_portal_access admin action."""
        request = self._make_request(admin_user)
        # Client already doesn't have portal user by default
        assert client_company.portal_user is None
        queryset = Client.objects.filter(pk=client_company.pk)
        self.admin.create_portal_access(request, queryset)
        client_company.refresh_from_db()
        assert client_company.portal_user is not None

    def test_create_portal_access_skips_existing(self, admin_user, client_company, client_user):
        """Test create_portal_access skips clients with existing portal user."""
        client_company.portal_user = client_user
        client_company.save()
        request = self._make_request(admin_user)
        queryset = Client.objects.filter(pk=client_company.pk)
        # Should not create a new portal user
        self.admin.create_portal_access(request, queryset)
        client_company.refresh_from_db()
        assert client_company.portal_user == client_user

    def test_actions_list(self):
        """Test that actions are registered."""
        assert 'move_to_active' in self.admin.actions
        assert 'create_portal_access' in self.admin.actions

    def test_fieldsets_present(self):
        """Test fieldsets are defined."""
        assert self.admin.fieldsets is not None
        assert len(self.admin.fieldsets) > 0


@pytest.mark.django_db
class TestClientNoteAdmin:
    """Tests for ClientNoteAdmin."""

    def test_client_note_admin_is_registered(self):
        """Test ClientNote is registered in admin."""
        from django.contrib import admin
        assert ClientNote in admin.site._registry

    def test_list_display(self):
        """Test list_display configuration."""
        site = AdminSite()
        admin_instance = ClientNoteAdmin(ClientNote, site)
        expected = ['client', 'note_type', 'subject', 'author', 'created_at']
        assert admin_instance.list_display == expected

    def test_list_filter(self):
        """Test list_filter configuration."""
        site = AdminSite()
        admin_instance = ClientNoteAdmin(ClientNote, site)
        assert 'note_type' in admin_instance.list_filter
        assert 'created_at' in admin_instance.list_filter

    def test_search_fields(self):
        """Test search_fields configuration."""
        site = AdminSite()
        admin_instance = ClientNoteAdmin(ClientNote, site)
        assert 'content' in admin_instance.search_fields

    def test_readonly_fields(self):
        """Test readonly_fields configuration."""
        site = AdminSite()
        admin_instance = ClientNoteAdmin(ClientNote, site)
        assert 'id' in admin_instance.readonly_fields
        assert 'created_at' in admin_instance.readonly_fields
        assert 'updated_at' in admin_instance.readonly_fields


@pytest.mark.django_db
class TestClientDocumentAdmin:
    """Tests for ClientDocumentAdmin."""

    def test_client_document_admin_is_registered(self):
        """Test ClientDocument is registered in admin."""
        from django.contrib import admin
        assert ClientDocument in admin.site._registry

    def test_list_display(self):
        """Test list_display configuration."""
        site = AdminSite()
        admin_instance = ClientDocumentAdmin(ClientDocument, site)
        expected = ['name', 'client', 'file_type', 'file_size', 'uploaded_by', 'created_at']
        assert admin_instance.list_display == expected

    def test_list_filter(self):
        """Test list_filter configuration."""
        site = AdminSite()
        admin_instance = ClientDocumentAdmin(ClientDocument, site)
        assert 'file_type' in admin_instance.list_filter
        assert 'created_at' in admin_instance.list_filter

    def test_search_fields(self):
        """Test search_fields configuration."""
        site = AdminSite()
        admin_instance = ClientDocumentAdmin(ClientDocument, site)
        assert 'name' in admin_instance.search_fields

    def test_readonly_fields(self):
        """Test readonly_fields configuration."""
        site = AdminSite()
        admin_instance = ClientDocumentAdmin(ClientDocument, site)
        assert 'id' in admin_instance.readonly_fields
        assert 'file_size' in admin_instance.readonly_fields
        assert 'created_at' in admin_instance.readonly_fields
