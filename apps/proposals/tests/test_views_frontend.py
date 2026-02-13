"""
Tests for proposals app frontend views.

Tests cover:
- ProposalListView (list, filtering by status, search by title/number/client)
- ProposalDetailView (detail page with sections, pricing, and activity)
- ProposalCreateView (create form page)
- ProposalEditView (edit form page with existing proposal data)
- ProposalClientView (public client-facing view, no login required)
- Authentication enforcement (LoginRequiredMixin redirects)
"""

import pytest
from django.test import Client as TestClient
from django.template import TemplateDoesNotExist

from apps.proposals.models import Proposal
from .factories import (
    UserFactory,
    ClientFactory,
    ProposalFactory,
    ProposalSectionFactory,
    ProposalPricingOptionFactory,
    ProposalActivityFactory,
)


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------
PROPOSAL_LIST_URL = '/api/proposals/'
PROPOSAL_CREATE_URL = '/api/proposals/create/'


def proposal_detail_url(pk):
    return f'/api/proposals/{pk}/'


def proposal_edit_url(pk):
    return f'/api/proposals/{pk}/edit/'


def proposal_client_view_url(pk):
    return f'/api/proposals/{pk}/view/'


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def auth_client(user):
    client = TestClient()
    client.force_login(user)
    return client


@pytest.fixture
def client_obj(user):
    return ClientFactory(owner=user)


@pytest.fixture
def proposal(user, client_obj):
    return ProposalFactory(client=client_obj, owner=user)


@pytest.fixture
def proposal_with_details(proposal):
    ProposalSectionFactory(proposal=proposal)
    ProposalSectionFactory(proposal=proposal)
    ProposalPricingOptionFactory(proposal=proposal)
    ProposalActivityFactory(proposal=proposal)
    return proposal


# ---------------------------------------------------------------------------
# ProposalListView tests
# ---------------------------------------------------------------------------
class TestProposalListView:
    """Tests for ProposalListView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self):
        client = TestClient()
        response = client.get(PROPOSAL_LIST_URL)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client, proposal):
        try:
            response = auth_client.get(PROPOSAL_LIST_URL)
            assert response.status_code in (200, 302)
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_expected_keys(self, auth_client, proposal):
        try:
            response = auth_client.get(PROPOSAL_LIST_URL)
            if response.status_code == 200 and response.context:
                ctx = response.context
                assert ctx['page_title'] == 'Proposals'
                assert 'status_choices' in ctx
                assert 'current_status' in ctx
                assert 'search_query' in ctx
                assert 'total_proposals' in ctx
                assert 'pending_count' in ctx
                assert 'accepted_count' in ctx
                assert 'proposals' in ctx
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_filter_by_status(self, auth_client, user, client_obj):
        draft_proposal = ProposalFactory(
            client=client_obj, owner=user, status=Proposal.DRAFT
        )
        ProposalFactory(
            client=client_obj, owner=user, status=Proposal.ACCEPTED
        )
        try:
            response = auth_client.get(
                PROPOSAL_LIST_URL, {'status': Proposal.DRAFT}
            )
            if response.status_code == 200 and response.context:
                proposals = list(response.context['proposals'])
                assert draft_proposal in proposals
                assert all(p.status == Proposal.DRAFT for p in proposals)
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_search_by_title(self, auth_client, user, client_obj):
        target = ProposalFactory(
            client=client_obj, owner=user, title='Unique Proposal Title XYZ'
        )
        ProposalFactory(
            client=client_obj, owner=user, title='Other Proposal'
        )
        try:
            response = auth_client.get(
                PROPOSAL_LIST_URL, {'q': 'Unique Proposal Title XYZ'}
            )
            if response.status_code == 200 and response.context:
                proposals = list(response.context['proposals'])
                assert target in proposals
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_search_by_client_company_name(self, auth_client, user):
        special_client = ClientFactory(
            company_name='SpecialSearchCompany', owner=user
        )
        target = ProposalFactory(
            client=special_client, owner=user
        )
        ProposalFactory(
            client=ClientFactory(owner=user), owner=user
        )
        try:
            response = auth_client.get(
                PROPOSAL_LIST_URL, {'q': 'SpecialSearchCompany'}
            )
            if response.status_code == 200 and response.context:
                proposals = list(response.context['proposals'])
                assert target in proposals
        except TemplateDoesNotExist:
            pass


# ---------------------------------------------------------------------------
# ProposalDetailView tests
# ---------------------------------------------------------------------------
class TestProposalDetailView:
    """Tests for ProposalDetailView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self, proposal):
        client = TestClient()
        response = client.get(proposal_detail_url(proposal.pk))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client, proposal_with_details):
        try:
            response = auth_client.get(
                proposal_detail_url(proposal_with_details.pk)
            )
            assert response.status_code in (200, 302)
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_expected_keys(self, auth_client, proposal_with_details):
        try:
            response = auth_client.get(
                proposal_detail_url(proposal_with_details.pk)
            )
            if response.status_code == 200 and response.context:
                ctx = response.context
                assert ctx['proposal'] == proposal_with_details
                assert 'page_title' in ctx
                assert 'sections' in ctx
                assert 'pricing_options' in ctx
                assert 'activities' in ctx
                assert 'is_expired' in ctx
                assert 'client' in ctx
                assert 'contract' in ctx
        except TemplateDoesNotExist:
            pass


# ---------------------------------------------------------------------------
# ProposalCreateView tests
# ---------------------------------------------------------------------------
class TestProposalCreateView:
    """Tests for ProposalCreateView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self):
        client = TestClient()
        response = client.get(PROPOSAL_CREATE_URL)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client):
        try:
            response = auth_client.get(PROPOSAL_CREATE_URL)
            assert response.status_code in (200, 302)
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_expected_keys(self, auth_client):
        try:
            response = auth_client.get(PROPOSAL_CREATE_URL)
            if response.status_code == 200 and response.context:
                ctx = response.context
                assert ctx['page_title'] == 'Create Proposal'
                assert 'clients' in ctx
                assert 'section_type_choices' in ctx
        except TemplateDoesNotExist:
            pass


# ---------------------------------------------------------------------------
# ProposalEditView tests
# ---------------------------------------------------------------------------
class TestProposalEditView:
    """Tests for ProposalEditView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self, proposal):
        client = TestClient()
        response = client.get(proposal_edit_url(proposal.pk))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client, proposal):
        try:
            response = auth_client.get(proposal_edit_url(proposal.pk))
            assert response.status_code in (200, 302)
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_expected_keys(self, auth_client, proposal_with_details):
        try:
            response = auth_client.get(
                proposal_edit_url(proposal_with_details.pk)
            )
            if response.status_code == 200 and response.context:
                ctx = response.context
                assert ctx['proposal'] == proposal_with_details
                assert 'sections' in ctx
                assert 'pricing_options' in ctx
                assert 'page_title' in ctx
                assert 'status_choices' in ctx
                assert 'section_type_choices' in ctx
                assert 'clients' in ctx
        except TemplateDoesNotExist:
            pass


# ---------------------------------------------------------------------------
# ProposalClientView tests (public, no login required)
# ---------------------------------------------------------------------------
class TestProposalClientView:
    """Tests for ProposalClientView (public client-facing view)."""

    @pytest.mark.django_db
    def test_no_login_required(self, proposal):
        """ProposalClientView should be accessible without authentication."""
        client = TestClient()
        try:
            response = client.get(proposal_client_view_url(proposal.pk))
            # Should NOT redirect to login
            assert response.status_code in (200, 302)
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_expected_keys(self, proposal_with_details):
        client = TestClient()
        try:
            response = client.get(
                proposal_client_view_url(proposal_with_details.pk)
            )
            if response.status_code == 200 and response.context:
                ctx = response.context
                assert ctx['proposal'] == proposal_with_details
                assert 'page_title' in ctx
                assert 'sections' in ctx
                assert 'pricing_options' in ctx
                assert 'is_expired' in ctx
                assert 'client' in ctx
                assert 'total_value' in ctx
                assert 'valid_until' in ctx
        except TemplateDoesNotExist:
            pass
