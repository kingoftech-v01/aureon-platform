"""
Tests for proposals URL configuration.
"""

import pytest
from django.urls import reverse, resolve


@pytest.mark.django_db
class TestProposalAPIUrls:
    """Tests for proposals API URL patterns."""

    def test_proposal_list_url(self):
        url = reverse('proposals:proposal-list')
        assert url is not None
        resolved = resolve(url)
        assert resolved.url_name == 'proposal-list'

    def test_proposal_section_list_url(self):
        url = reverse('proposals:proposal-section-list')
        assert url is not None
        resolved = resolve(url)
        assert resolved.url_name == 'proposal-section-list'

    def test_proposal_pricing_option_list_url(self):
        url = reverse('proposals:proposal-pricing-option-list')
        assert url is not None
        resolved = resolve(url)
        assert resolved.url_name == 'proposal-pricing-option-list'


@pytest.mark.django_db
class TestProposalFrontendUrls:
    """Tests for proposals frontend URL patterns."""

    def test_proposal_list_frontend(self):
        url = reverse('proposals:proposal_list')
        assert url is not None

    def test_proposal_create_frontend(self):
        url = reverse('proposals:proposal_create')
        assert url is not None

    def test_proposal_detail_frontend(self):
        import uuid
        pk = uuid.uuid4()
        url = reverse('proposals:proposal_detail', kwargs={'pk': pk})
        assert str(pk) in url

    def test_proposal_edit_frontend(self):
        import uuid
        pk = uuid.uuid4()
        url = reverse('proposals:proposal_edit', kwargs={'pk': pk})
        assert str(pk) in url

    def test_proposal_client_view_frontend(self):
        import uuid
        pk = uuid.uuid4()
        url = reverse('proposals:proposal_client_view', kwargs={'pk': pk})
        assert str(pk) in url
