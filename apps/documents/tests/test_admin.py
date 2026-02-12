"""
Tests for documents admin configuration.

Covers:
- DocumentAdmin registration, list_display, list_filter,
  search_fields, readonly_fields, raw_id_fields
"""

import pytest
from django.contrib import admin
from django.contrib.admin.sites import AdminSite

from apps.documents.models import Document
from apps.documents.admin import DocumentAdmin


@pytest.fixture
def site():
    return AdminSite()


@pytest.fixture
def doc_admin(site):
    return DocumentAdmin(Document, site)


class TestDocumentAdmin:

    def test_registered(self):
        assert Document in admin.site._registry

    def test_list_display(self, doc_admin):
        expected = ['title', 'document_type', 'file_type', 'file_size', 'uploaded_by', 'client', 'created_at']
        assert doc_admin.list_display == expected

    def test_list_filter(self, doc_admin):
        assert 'document_type' in doc_admin.list_filter
        assert 'processing_status' in doc_admin.list_filter
        assert 'is_public' in doc_admin.list_filter
        assert 'created_at' in doc_admin.list_filter

    def test_search_fields(self, doc_admin):
        assert 'title' in doc_admin.search_fields
        assert 'description' in doc_admin.search_fields

    def test_readonly_fields(self, doc_admin):
        expected = ['id', 'file_size', 'file_type', 'processing_status', 'created_at', 'updated_at']
        assert doc_admin.readonly_fields == expected

    def test_raw_id_fields(self, doc_admin):
        expected = ['uploaded_by', 'client', 'contract', 'invoice']
        assert doc_admin.raw_id_fields == expected

    def test_admin_class_type(self, doc_admin):
        assert isinstance(doc_admin, admin.ModelAdmin)
