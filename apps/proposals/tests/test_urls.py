"""
Tests for proposals app URL configuration.

Tests cover:
- URL resolution for all API routes (proposal-list, proposal-detail, etc.)
- URL resolution for all frontend routes (proposal_list, proposal_create, etc.)
- URL reverse and resolve consistency using django.urls.reverse and django.urls.resolve
"""

import pytest
import uuid
from django.urls import reverse, resolve

from apps.proposals.views import (
    ProposalViewSet,
    ProposalSectionViewSet,
    ProposalPricingOptionViewSet,
)
from apps.proposals.views_frontend import (
    ProposalListView,
    ProposalDetailView,
    ProposalCreateView,
    ProposalEditView,
    ProposalClientView,
)


# ============================================================================
# API URL Tests
# ============================================================================


class TestProposalAPIUrls:
    """Tests for proposals API URL patterns."""

    def test_proposal_list_url_resolves(self):
        """Test proposal-list URL resolves to ProposalViewSet."""
        url = reverse('proposals:proposal-list')
        assert url is not None
        resolved = resolve(url)
        assert resolved.url_name == 'proposal-list'
        assert resolved.func.cls == ProposalViewSet

    def test_proposal_detail_url_resolves(self):
        """Test proposal-detail URL resolves to ProposalViewSet."""
        pk = uuid.uuid4()
        url = reverse('proposals:proposal-detail', kwargs={'pk': pk})
        assert url is not None
        assert str(pk) in url
        resolved = resolve(url)
        assert resolved.url_name == 'proposal-detail'
        assert resolved.func.cls == ProposalViewSet

    def test_proposal_section_list_url_resolves(self):
        """Test proposal-section-list URL resolves to ProposalSectionViewSet."""
        url = reverse('proposals:proposal-section-list')
        assert url is not None
        resolved = resolve(url)
        assert resolved.url_name == 'proposal-section-list'
        assert resolved.func.cls == ProposalSectionViewSet

    def test_proposal_section_detail_url_resolves(self):
        """Test proposal-section-detail URL resolves to ProposalSectionViewSet."""
        pk = uuid.uuid4()
        url = reverse('proposals:proposal-section-detail', kwargs={'pk': pk})
        assert url is not None
        assert str(pk) in url
        resolved = resolve(url)
        assert resolved.url_name == 'proposal-section-detail'
        assert resolved.func.cls == ProposalSectionViewSet

    def test_proposal_pricing_option_list_url_resolves(self):
        """Test proposal-pricing-option-list URL resolves to ProposalPricingOptionViewSet."""
        url = reverse('proposals:proposal-pricing-option-list')
        assert url is not None
        resolved = resolve(url)
        assert resolved.url_name == 'proposal-pricing-option-list'
        assert resolved.func.cls == ProposalPricingOptionViewSet

    def test_proposal_pricing_option_detail_url_resolves(self):
        """Test proposal-pricing-option-detail URL resolves to ProposalPricingOptionViewSet."""
        pk = uuid.uuid4()
        url = reverse('proposals:proposal-pricing-option-detail', kwargs={'pk': pk})
        assert url is not None
        assert str(pk) in url
        resolved = resolve(url)
        assert resolved.url_name == 'proposal-pricing-option-detail'
        assert resolved.func.cls == ProposalPricingOptionViewSet


# ============================================================================
# Frontend URL Tests
# ============================================================================


class TestProposalFrontendUrls:
    """Tests for proposals frontend URL patterns."""

    def test_proposal_list_frontend_url(self):
        """Test proposal_list frontend URL resolves to ProposalListView."""
        url = reverse('proposals:proposal_list')
        assert url is not None
        resolved = resolve(url)
        assert resolved.url_name == 'proposal_list'
        assert resolved.func.view_class == ProposalListView

    def test_proposal_create_frontend_url(self):
        """Test proposal_create frontend URL resolves to ProposalCreateView."""
        url = reverse('proposals:proposal_create')
        assert url is not None
        resolved = resolve(url)
        assert resolved.url_name == 'proposal_create'
        assert resolved.func.view_class == ProposalCreateView

    def test_proposal_detail_frontend_url(self):
        """Test proposal_detail frontend URL resolves to ProposalDetailView."""
        pk = uuid.uuid4()
        url = reverse('proposals:proposal_detail', kwargs={'pk': pk})
        assert url is not None
        assert str(pk) in url
        resolved = resolve(url)
        assert resolved.url_name == 'proposal_detail'
        assert resolved.func.view_class == ProposalDetailView

    def test_proposal_edit_frontend_url(self):
        """Test proposal_edit frontend URL resolves to ProposalEditView."""
        pk = uuid.uuid4()
        url = reverse('proposals:proposal_edit', kwargs={'pk': pk})
        assert url is not None
        assert str(pk) in url
        resolved = resolve(url)
        assert resolved.url_name == 'proposal_edit'
        assert resolved.func.view_class == ProposalEditView

    def test_proposal_client_view_frontend_url(self):
        """Test proposal_client_view frontend URL resolves to ProposalClientView."""
        pk = uuid.uuid4()
        url = reverse('proposals:proposal_client_view', kwargs={'pk': pk})
        assert url is not None
        assert str(pk) in url
        resolved = resolve(url)
        assert resolved.url_name == 'proposal_client_view'
        assert resolved.func.view_class == ProposalClientView


# ============================================================================
# URL Structure and Configuration Tests
# ============================================================================


class TestProposalURLConfiguration:
    """Tests for proposals URL configuration structure."""

    def test_app_name(self):
        """Test the app_name is set to 'proposals'."""
        from apps.proposals import urls
        assert urls.app_name == 'proposals'

    def test_router_registered_viewsets(self):
        """Test the router has all expected viewsets registered."""
        from apps.proposals.urls import router
        registered_names = [prefix for prefix, viewset, basename in router.registry]
        assert 'proposals' in registered_names
        assert 'proposal-sections' in registered_names
        assert 'proposal-pricing-options' in registered_names

    def test_router_has_three_viewsets(self):
        """Test the router has exactly three registered viewsets."""
        from apps.proposals.urls import router
        assert len(router.registry) == 3

    def test_frontend_urlpatterns_count(self):
        """Test the correct number of frontend URL patterns are defined."""
        from apps.proposals.urls import frontend_urlpatterns
        assert len(frontend_urlpatterns) == 5

    def test_api_list_url_ends_with_slash(self):
        """Test API list URLs end with trailing slash."""
        url = reverse('proposals:proposal-list')
        assert url.endswith('/')

    def test_frontend_list_url_path(self):
        """Test frontend list URL is at the proposals root path."""
        url = reverse('proposals:proposal_list')
        assert url.endswith('/proposals/')

    def test_frontend_create_url_path(self):
        """Test frontend create URL includes 'create/' segment."""
        url = reverse('proposals:proposal_create')
        assert '/create/' in url

    def test_frontend_detail_url_contains_uuid(self):
        """Test frontend detail URL contains the UUID parameter."""
        pk = uuid.uuid4()
        url = reverse('proposals:proposal_detail', kwargs={'pk': pk})
        assert str(pk) in url

    def test_frontend_edit_url_contains_edit_segment(self):
        """Test frontend edit URL includes 'edit/' segment."""
        pk = uuid.uuid4()
        url = reverse('proposals:proposal_edit', kwargs={'pk': pk})
        assert '/edit/' in url

    def test_frontend_client_view_url_contains_view_segment(self):
        """Test frontend client view URL includes 'view/' segment."""
        pk = uuid.uuid4()
        url = reverse('proposals:proposal_client_view', kwargs={'pk': pk})
        assert '/view/' in url
