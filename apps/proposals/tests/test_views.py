"""
Tests for proposals app API views.

Tests cover:
- ProposalViewSet CRUD operations (list, retrieve, create, update, partial_update, destroy)
- Custom actions: send, accept, decline, duplicate, convert_to_contract, stats, activities
- Permission checks (authenticated vs unauthenticated, staff vs non-staff)
- Filtering, search, and ordering
- ProposalSectionViewSet CRUD
- ProposalPricingOptionViewSet CRUD
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone
from rest_framework import status as http_status
from rest_framework.test import APIClient

from apps.proposals.models import (
    Proposal,
    ProposalSection,
    ProposalPricingOption,
    ProposalActivity,
)
from apps.proposals.tests.factories import (
    ProposalFactory,
    ProposalSectionFactory,
    ProposalPricingOptionFactory,
    ProposalActivityFactory,
    UserFactory,
    ClientFactory,
)


# ============================================================================
# Helpers
# ============================================================================

PROPOSAL_LIST_URL = '/api/proposals/proposals/'


def proposal_detail_url(pk):
    return f'/api/proposals/proposals/{pk}/'


def proposal_action_url(pk, action):
    return f'/api/proposals/proposals/{pk}/{action}/'


PROPOSAL_STATS_URL = '/api/proposals/proposals/stats/'
SECTION_LIST_URL = '/api/proposals/proposal-sections/'
PRICING_OPTION_LIST_URL = '/api/proposals/proposal-pricing-options/'


# ============================================================================
# Authentication Tests
# ============================================================================


@pytest.mark.django_db
class TestProposalAuthentication:
    """Tests for authentication requirements on proposal endpoints."""

    def test_list_requires_authentication(self, api_client):
        """Test that listing proposals requires authentication."""
        response = api_client.get(PROPOSAL_LIST_URL)

        assert response.status_code == http_status.HTTP_401_UNAUTHORIZED

    def test_detail_requires_authentication(self, api_client):
        """Test that retrieving a proposal requires authentication."""
        proposal = ProposalFactory()
        response = api_client.get(proposal_detail_url(proposal.id))

        assert response.status_code == http_status.HTTP_401_UNAUTHORIZED

    def test_create_requires_authentication(self, api_client):
        """Test that creating a proposal requires authentication."""
        response = api_client.post(PROPOSAL_LIST_URL, {})

        assert response.status_code == http_status.HTTP_401_UNAUTHORIZED

    def test_stats_requires_authentication(self, api_client):
        """Test that stats endpoint requires authentication."""
        response = api_client.get(PROPOSAL_STATS_URL)

        assert response.status_code == http_status.HTTP_401_UNAUTHORIZED


# ============================================================================
# Proposal List Tests
# ============================================================================


@pytest.mark.django_db
class TestProposalList:
    """Tests for listing proposals."""

    def test_list_proposals_as_staff(self, authenticated_admin_client, admin_user):
        """Test listing proposals as a staff user returns all proposals."""
        ProposalFactory(owner=admin_user)
        other_user = UserFactory()
        ProposalFactory(owner=other_user)

        response = authenticated_admin_client.get(PROPOSAL_LIST_URL)

        assert response.status_code == http_status.HTTP_200_OK
        assert len(response.data['results']) == 2

    def test_list_proposals_non_staff_sees_own_and_unowned(self, api_client):
        """Test non-staff user sees only own and unowned proposals."""
        regular_user = UserFactory(is_staff=False, role='contributor')
        other_user = UserFactory()

        ProposalFactory(owner=regular_user)
        ProposalFactory(owner=None)
        ProposalFactory(owner=other_user)

        api_client.force_authenticate(user=regular_user)
        response = api_client.get(PROPOSAL_LIST_URL)

        assert response.status_code == http_status.HTTP_200_OK
        assert len(response.data['results']) == 2

    def test_list_proposals_empty(self, authenticated_admin_client):
        """Test listing proposals when none exist."""
        response = authenticated_admin_client.get(PROPOSAL_LIST_URL)

        assert response.status_code == http_status.HTTP_200_OK
        assert len(response.data['results']) == 0

    def test_list_proposals_filter_by_status(self, authenticated_admin_client, admin_user):
        """Test filtering proposals by status."""
        ProposalFactory(owner=admin_user, status=Proposal.DRAFT)
        ProposalFactory(owner=admin_user, status=Proposal.SENT)
        ProposalFactory(owner=admin_user, status=Proposal.SENT)

        response = authenticated_admin_client.get(
            PROPOSAL_LIST_URL, {'status': 'sent'}
        )

        assert response.status_code == http_status.HTTP_200_OK
        assert len(response.data['results']) == 2

    def test_list_proposals_search(self, authenticated_admin_client, admin_user):
        """Test searching proposals by title."""
        ProposalFactory(owner=admin_user, title='Website Redesign')
        ProposalFactory(owner=admin_user, title='Mobile App Development')

        response = authenticated_admin_client.get(
            PROPOSAL_LIST_URL, {'search': 'Website'}
        )

        assert response.status_code == http_status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['title'] == 'Website Redesign'

    def test_list_proposals_ordering(self, authenticated_admin_client, admin_user):
        """Test ordering proposals by total_value."""
        ProposalFactory(owner=admin_user, total_value=Decimal('1000.00'))
        ProposalFactory(owner=admin_user, total_value=Decimal('5000.00'))
        ProposalFactory(owner=admin_user, total_value=Decimal('3000.00'))

        response = authenticated_admin_client.get(
            PROPOSAL_LIST_URL, {'ordering': 'total_value'}
        )

        assert response.status_code == http_status.HTTP_200_OK
        values = [Decimal(r['total_value']) for r in response.data['results']]
        assert values == sorted(values)


# ============================================================================
# Proposal Retrieve Tests
# ============================================================================


@pytest.mark.django_db
class TestProposalRetrieve:
    """Tests for retrieving a single proposal."""

    def test_retrieve_proposal(self, authenticated_admin_client, admin_user):
        """Test retrieving a proposal detail."""
        proposal = ProposalFactory(owner=admin_user, title='My Proposal')
        ProposalSectionFactory(proposal=proposal, title='Scope')
        ProposalPricingOptionFactory(proposal=proposal, name='Basic')
        ProposalActivityFactory(proposal=proposal)

        response = authenticated_admin_client.get(proposal_detail_url(proposal.id))

        assert response.status_code == http_status.HTTP_200_OK
        assert response.data['title'] == 'My Proposal'
        assert len(response.data['sections']) == 1
        assert len(response.data['pricing_options']) == 1
        assert len(response.data['activities']) == 1

    def test_retrieve_nonexistent_proposal(self, authenticated_admin_client):
        """Test retrieving a non-existent proposal returns 404."""
        import uuid
        response = authenticated_admin_client.get(
            proposal_detail_url(uuid.uuid4())
        )

        assert response.status_code == http_status.HTTP_404_NOT_FOUND


# ============================================================================
# Proposal Create Tests
# ============================================================================


@pytest.mark.django_db
class TestProposalCreate:
    """Tests for creating proposals."""

    def test_create_proposal(self, authenticated_admin_client, admin_user):
        """Test creating a new proposal."""
        client = ClientFactory(owner=admin_user)
        data = {
            'title': 'New Project Proposal',
            'description': 'A detailed proposal for the new project.',
            'client': str(client.id),
            'valid_until': (date.today() + timedelta(days=30)).isoformat(),
            'total_value': '15000.00',
            'currency': 'USD',
        }

        response = authenticated_admin_client.post(PROPOSAL_LIST_URL, data, format='json')

        assert response.status_code == http_status.HTTP_201_CREATED
        assert response.data['title'] == 'New Project Proposal'
        assert response.data['proposal_number'].startswith('PRP-')

    def test_create_proposal_sets_owner(self, authenticated_admin_client, admin_user):
        """Test that creating a proposal sets the owner to the current user."""
        client = ClientFactory()
        data = {
            'title': 'Owner Test',
            'client': str(client.id),
            'valid_until': (date.today() + timedelta(days=30)).isoformat(),
            'total_value': '1000.00',
        }

        response = authenticated_admin_client.post(PROPOSAL_LIST_URL, data, format='json')

        assert response.status_code == http_status.HTTP_201_CREATED
        proposal = Proposal.objects.get(id=response.data['id'])
        assert proposal.owner == admin_user

    def test_create_proposal_creates_activity(self, authenticated_admin_client, admin_user):
        """Test that creating a proposal creates a CREATED activity."""
        client = ClientFactory()
        data = {
            'title': 'Activity Test',
            'client': str(client.id),
            'valid_until': (date.today() + timedelta(days=30)).isoformat(),
            'total_value': '1000.00',
        }

        response = authenticated_admin_client.post(PROPOSAL_LIST_URL, data, format='json')

        assert response.status_code == http_status.HTTP_201_CREATED
        proposal = Proposal.objects.get(id=response.data['id'])
        activity = proposal.activities.first()
        assert activity is not None
        assert activity.activity_type == ProposalActivity.CREATED
        assert activity.user == admin_user

    def test_create_proposal_with_past_valid_until_fails(self, authenticated_admin_client):
        """Test that creating a proposal with past valid_until date fails."""
        client = ClientFactory()
        data = {
            'title': 'Past Date',
            'client': str(client.id),
            'valid_until': (date.today() - timedelta(days=1)).isoformat(),
            'total_value': '1000.00',
        }

        response = authenticated_admin_client.post(PROPOSAL_LIST_URL, data, format='json')

        assert response.status_code == http_status.HTTP_400_BAD_REQUEST

    def test_create_proposal_missing_required_fields(self, authenticated_admin_client):
        """Test that missing required fields returns validation errors."""
        response = authenticated_admin_client.post(PROPOSAL_LIST_URL, {}, format='json')

        assert response.status_code == http_status.HTTP_400_BAD_REQUEST


# ============================================================================
# Proposal Update Tests
# ============================================================================


@pytest.mark.django_db
class TestProposalUpdate:
    """Tests for updating proposals."""

    def test_update_proposal(self, authenticated_admin_client, admin_user):
        """Test fully updating a proposal."""
        proposal = ProposalFactory(owner=admin_user, title='Old Title')
        data = {
            'title': 'Updated Title',
            'client': str(proposal.client.id),
            'valid_until': proposal.valid_until.isoformat(),
            'total_value': '20000.00',
            'currency': 'EUR',
        }

        response = authenticated_admin_client.put(
            proposal_detail_url(proposal.id), data, format='json'
        )

        assert response.status_code == http_status.HTTP_200_OK
        proposal.refresh_from_db()
        assert proposal.title == 'Updated Title'
        assert proposal.total_value == Decimal('20000.00')
        assert proposal.currency == 'EUR'

    def test_partial_update_proposal(self, authenticated_admin_client, admin_user):
        """Test partially updating a proposal."""
        proposal = ProposalFactory(owner=admin_user, title='Original')

        response = authenticated_admin_client.patch(
            proposal_detail_url(proposal.id),
            {'title': 'Patched Title'},
            format='json',
        )

        assert response.status_code == http_status.HTTP_200_OK
        proposal.refresh_from_db()
        assert proposal.title == 'Patched Title'


# ============================================================================
# Proposal Delete Tests
# ============================================================================


@pytest.mark.django_db
class TestProposalDelete:
    """Tests for deleting proposals."""

    def test_delete_proposal(self, authenticated_admin_client, admin_user):
        """Test deleting a proposal."""
        proposal = ProposalFactory(owner=admin_user)
        proposal_id = proposal.id

        response = authenticated_admin_client.delete(proposal_detail_url(proposal_id))

        assert response.status_code == http_status.HTTP_204_NO_CONTENT
        assert not Proposal.objects.filter(id=proposal_id).exists()

    def test_delete_nonexistent_proposal(self, authenticated_admin_client):
        """Test deleting a non-existent proposal returns 404."""
        import uuid
        response = authenticated_admin_client.delete(
            proposal_detail_url(uuid.uuid4())
        )

        assert response.status_code == http_status.HTTP_404_NOT_FOUND


# ============================================================================
# Proposal Send Action Tests
# ============================================================================


@pytest.mark.django_db
class TestProposalSendAction:
    """Tests for the send action."""

    def test_send_draft_proposal(self, authenticated_admin_client, admin_user):
        """Test sending a draft proposal."""
        proposal = ProposalFactory(owner=admin_user, status=Proposal.DRAFT)

        response = authenticated_admin_client.post(
            proposal_action_url(proposal.id, 'send')
        )

        assert response.status_code == http_status.HTTP_200_OK
        proposal.refresh_from_db()
        assert proposal.status == Proposal.SENT
        assert proposal.sent_at is not None

    def test_send_creates_activity(self, authenticated_admin_client, admin_user):
        """Test that sending a proposal creates a SENT activity."""
        proposal = ProposalFactory(owner=admin_user, status=Proposal.DRAFT)

        authenticated_admin_client.post(
            proposal_action_url(proposal.id, 'send')
        )

        activity = proposal.activities.filter(
            activity_type=ProposalActivity.SENT
        ).first()
        assert activity is not None
        assert activity.user == admin_user

    def test_send_non_draft_proposal_fails(self, authenticated_admin_client, admin_user):
        """Test that sending a non-draft proposal returns 400."""
        proposal = ProposalFactory(owner=admin_user, status=Proposal.SENT)

        response = authenticated_admin_client.post(
            proposal_action_url(proposal.id, 'send')
        )

        assert response.status_code == http_status.HTTP_400_BAD_REQUEST
        assert 'Only draft proposals can be sent' in response.data['detail']

    def test_send_accepted_proposal_fails(self, authenticated_admin_client, admin_user):
        """Test that sending an accepted proposal returns 400."""
        proposal = ProposalFactory(owner=admin_user, status=Proposal.ACCEPTED)

        response = authenticated_admin_client.post(
            proposal_action_url(proposal.id, 'send')
        )

        assert response.status_code == http_status.HTTP_400_BAD_REQUEST


# ============================================================================
# Proposal Accept Action Tests
# ============================================================================


@pytest.mark.django_db
class TestProposalAcceptAction:
    """Tests for the accept action."""

    def test_accept_sent_proposal(self, authenticated_admin_client, admin_user):
        """Test accepting a sent proposal."""
        proposal = ProposalFactory(owner=admin_user, status=Proposal.SENT)

        response = authenticated_admin_client.post(
            proposal_action_url(proposal.id, 'accept'),
            {'signature': 'John Doe', 'client_message': 'Looks great!'},
            format='json',
        )

        assert response.status_code == http_status.HTTP_200_OK
        proposal.refresh_from_db()
        assert proposal.status == Proposal.ACCEPTED
        assert proposal.accepted_at is not None
        assert proposal.signature == 'John Doe'
        assert proposal.client_message == 'Looks great!'

    def test_accept_viewed_proposal(self, authenticated_admin_client, admin_user):
        """Test accepting a viewed proposal."""
        proposal = ProposalFactory(owner=admin_user, status=Proposal.VIEWED)

        response = authenticated_admin_client.post(
            proposal_action_url(proposal.id, 'accept')
        )

        assert response.status_code == http_status.HTTP_200_OK
        proposal.refresh_from_db()
        assert proposal.status == Proposal.ACCEPTED

    def test_accept_creates_activity_with_metadata(self, authenticated_admin_client, admin_user):
        """Test that accepting a proposal creates an ACCEPTED activity."""
        proposal = ProposalFactory(owner=admin_user, status=Proposal.SENT)

        authenticated_admin_client.post(
            proposal_action_url(proposal.id, 'accept'),
            {'signature': 'Sig', 'client_message': 'OK'},
            format='json',
        )

        activity = proposal.activities.filter(
            activity_type=ProposalActivity.ACCEPTED
        ).first()
        assert activity is not None
        assert activity.metadata['has_signature'] is True
        assert activity.metadata['has_message'] is True

    def test_accept_draft_proposal_fails(self, authenticated_admin_client, admin_user):
        """Test that accepting a draft proposal returns 400."""
        proposal = ProposalFactory(owner=admin_user, status=Proposal.DRAFT)

        response = authenticated_admin_client.post(
            proposal_action_url(proposal.id, 'accept')
        )

        assert response.status_code == http_status.HTTP_400_BAD_REQUEST

    def test_accept_declined_proposal_fails(self, authenticated_admin_client, admin_user):
        """Test that accepting a declined proposal returns 400."""
        proposal = ProposalFactory(owner=admin_user, status=Proposal.DECLINED)

        response = authenticated_admin_client.post(
            proposal_action_url(proposal.id, 'accept')
        )

        assert response.status_code == http_status.HTTP_400_BAD_REQUEST

    def test_accept_without_optional_fields(self, authenticated_admin_client, admin_user):
        """Test accepting without signature or client_message."""
        proposal = ProposalFactory(owner=admin_user, status=Proposal.SENT)

        response = authenticated_admin_client.post(
            proposal_action_url(proposal.id, 'accept')
        )

        assert response.status_code == http_status.HTTP_200_OK
        proposal.refresh_from_db()
        assert proposal.signature == ''
        assert proposal.client_message == ''


# ============================================================================
# Proposal Decline Action Tests
# ============================================================================


@pytest.mark.django_db
class TestProposalDeclineAction:
    """Tests for the decline action."""

    def test_decline_sent_proposal(self, authenticated_admin_client, admin_user):
        """Test declining a sent proposal."""
        proposal = ProposalFactory(owner=admin_user, status=Proposal.SENT)

        response = authenticated_admin_client.post(
            proposal_action_url(proposal.id, 'decline'),
            {'client_message': 'Too expensive.'},
            format='json',
        )

        assert response.status_code == http_status.HTTP_200_OK
        proposal.refresh_from_db()
        assert proposal.status == Proposal.DECLINED
        assert proposal.declined_at is not None
        assert proposal.client_message == 'Too expensive.'

    def test_decline_viewed_proposal(self, authenticated_admin_client, admin_user):
        """Test declining a viewed proposal."""
        proposal = ProposalFactory(owner=admin_user, status=Proposal.VIEWED)

        response = authenticated_admin_client.post(
            proposal_action_url(proposal.id, 'decline')
        )

        assert response.status_code == http_status.HTTP_200_OK
        proposal.refresh_from_db()
        assert proposal.status == Proposal.DECLINED

    def test_decline_creates_activity(self, authenticated_admin_client, admin_user):
        """Test that declining creates a DECLINED activity."""
        proposal = ProposalFactory(owner=admin_user, status=Proposal.SENT)

        authenticated_admin_client.post(
            proposal_action_url(proposal.id, 'decline'),
            {'client_message': 'Not interested.'},
            format='json',
        )

        activity = proposal.activities.filter(
            activity_type=ProposalActivity.DECLINED
        ).first()
        assert activity is not None
        assert activity.metadata['has_message'] is True

    def test_decline_draft_proposal_fails(self, authenticated_admin_client, admin_user):
        """Test that declining a draft proposal returns 400."""
        proposal = ProposalFactory(owner=admin_user, status=Proposal.DRAFT)

        response = authenticated_admin_client.post(
            proposal_action_url(proposal.id, 'decline')
        )

        assert response.status_code == http_status.HTTP_400_BAD_REQUEST

    def test_decline_accepted_proposal_fails(self, authenticated_admin_client, admin_user):
        """Test that declining an accepted proposal returns 400."""
        proposal = ProposalFactory(owner=admin_user, status=Proposal.ACCEPTED)

        response = authenticated_admin_client.post(
            proposal_action_url(proposal.id, 'decline')
        )

        assert response.status_code == http_status.HTTP_400_BAD_REQUEST


# ============================================================================
# Proposal Duplicate Action Tests
# ============================================================================


@pytest.mark.django_db
class TestProposalDuplicateAction:
    """Tests for the duplicate action."""

    def test_duplicate_proposal(self, authenticated_admin_client, admin_user):
        """Test duplicating a proposal creates a new draft proposal."""
        proposal = ProposalFactory(
            owner=admin_user,
            title='Original Proposal',
            total_value=Decimal('10000.00'),
        )
        ProposalSectionFactory(proposal=proposal, title='Scope')
        ProposalPricingOptionFactory(proposal=proposal, name='Basic')

        response = authenticated_admin_client.post(
            proposal_action_url(proposal.id, 'duplicate')
        )

        assert response.status_code == http_status.HTTP_201_CREATED
        assert response.data['title'] == 'Original Proposal (Copy)'
        assert response.data['status'] == 'draft'
        assert len(response.data['sections']) == 1
        assert len(response.data['pricing_options']) == 1

    def test_duplicate_creates_new_proposal_number(self, authenticated_admin_client, admin_user):
        """Test that duplicate gets a new proposal number."""
        proposal = ProposalFactory(owner=admin_user)
        original_number = proposal.proposal_number

        response = authenticated_admin_client.post(
            proposal_action_url(proposal.id, 'duplicate')
        )

        assert response.status_code == http_status.HTTP_201_CREATED
        assert response.data['proposal_number'] != original_number

    def test_duplicate_copies_sections(self, authenticated_admin_client, admin_user):
        """Test that duplicate copies all sections."""
        proposal = ProposalFactory(owner=admin_user)
        ProposalSectionFactory(proposal=proposal, title='Scope', section_type='scope')
        ProposalSectionFactory(proposal=proposal, title='Timeline', section_type='timeline')

        response = authenticated_admin_client.post(
            proposal_action_url(proposal.id, 'duplicate')
        )

        assert response.status_code == http_status.HTTP_201_CREATED
        new_proposal = Proposal.objects.get(id=response.data['id'])
        assert new_proposal.sections.count() == 2

    def test_duplicate_copies_pricing_options(self, authenticated_admin_client, admin_user):
        """Test that duplicate copies all pricing options."""
        proposal = ProposalFactory(owner=admin_user)
        ProposalPricingOptionFactory(proposal=proposal, name='Basic')
        ProposalPricingOptionFactory(proposal=proposal, name='Premium')

        response = authenticated_admin_client.post(
            proposal_action_url(proposal.id, 'duplicate')
        )

        assert response.status_code == http_status.HTTP_201_CREATED
        new_proposal = Proposal.objects.get(id=response.data['id'])
        assert new_proposal.pricing_options.count() == 2

    def test_duplicate_creates_activity(self, authenticated_admin_client, admin_user):
        """Test that duplicate creates a CREATED activity with metadata."""
        proposal = ProposalFactory(owner=admin_user)

        response = authenticated_admin_client.post(
            proposal_action_url(proposal.id, 'duplicate')
        )

        assert response.status_code == http_status.HTTP_201_CREATED
        new_proposal = Proposal.objects.get(id=response.data['id'])
        activity = new_proposal.activities.first()
        assert activity is not None
        assert activity.activity_type == ProposalActivity.CREATED
        assert activity.metadata['duplicated_from'] == str(proposal.id)

    def test_duplicate_sets_owner_to_current_user(self, authenticated_admin_client, admin_user):
        """Test that the duplicate proposal owner is the current user."""
        other_user = UserFactory()
        proposal = ProposalFactory(owner=other_user)

        response = authenticated_admin_client.post(
            proposal_action_url(proposal.id, 'duplicate')
        )

        assert response.status_code == http_status.HTTP_201_CREATED
        new_proposal = Proposal.objects.get(id=response.data['id'])
        assert new_proposal.owner == admin_user


# ============================================================================
# Proposal Convert to Contract Action Tests
# ============================================================================


@pytest.mark.django_db
class TestProposalConvertToContractAction:
    """Tests for the convert_to_contract action."""

    def test_convert_accepted_proposal(self, authenticated_admin_client, admin_user):
        """Test converting an accepted proposal to a contract."""
        proposal = ProposalFactory(
            owner=admin_user,
            status=Proposal.ACCEPTED,
            title='Contract-Ready',
            total_value=Decimal('15000.00'),
        )

        response = authenticated_admin_client.post(
            proposal_action_url(proposal.id, 'convert_to_contract')
        )

        assert response.status_code == http_status.HTTP_201_CREATED
        proposal.refresh_from_db()
        assert proposal.status == Proposal.CONVERTED
        assert proposal.contract is not None
        assert proposal.contract.title == 'Contract-Ready'
        assert proposal.contract.value == Decimal('15000.00')

    def test_convert_creates_activity(self, authenticated_admin_client, admin_user):
        """Test that convert_to_contract creates a CONVERTED activity."""
        proposal = ProposalFactory(
            owner=admin_user,
            status=Proposal.ACCEPTED,
        )

        authenticated_admin_client.post(
            proposal_action_url(proposal.id, 'convert_to_contract')
        )

        activity = proposal.activities.filter(
            activity_type=ProposalActivity.CONVERTED
        ).first()
        assert activity is not None
        assert 'contract_id' in activity.metadata
        assert 'contract_number' in activity.metadata

    def test_convert_non_accepted_proposal_fails(self, authenticated_admin_client, admin_user):
        """Test that converting a non-accepted proposal returns 400."""
        for status_val in [Proposal.DRAFT, Proposal.SENT, Proposal.DECLINED]:
            proposal = ProposalFactory(owner=admin_user, status=status_val)

            response = authenticated_admin_client.post(
                proposal_action_url(proposal.id, 'convert_to_contract')
            )

            assert response.status_code == http_status.HTTP_400_BAD_REQUEST

    def test_convert_already_converted_proposal_fails(self, authenticated_admin_client, admin_user):
        """Test that converting an already-converted proposal returns 400."""
        from apps.contracts.models import Contract

        proposal = ProposalFactory(owner=admin_user, status=Proposal.ACCEPTED)
        contract = Contract.objects.create(
            client=proposal.client,
            title='Existing Contract',
            description='Already exists.',
            contract_type=Contract.FIXED_PRICE,
            status=Contract.DRAFT,
            start_date=date.today(),
            value=Decimal('5000.00'),
            currency='USD',
        )
        proposal.contract = contract
        proposal.save()

        response = authenticated_admin_client.post(
            proposal_action_url(proposal.id, 'convert_to_contract')
        )

        assert response.status_code == http_status.HTTP_400_BAD_REQUEST
        assert 'already been converted' in response.data['detail']


# ============================================================================
# Proposal Stats Action Tests
# ============================================================================


@pytest.mark.django_db
class TestProposalStatsAction:
    """Tests for the stats action."""

    def test_stats_returns_counts(self, authenticated_admin_client, admin_user):
        """Test stats endpoint returns correct counts."""
        ProposalFactory(owner=admin_user, status=Proposal.DRAFT)
        ProposalFactory(owner=admin_user, status=Proposal.SENT)
        ProposalFactory(owner=admin_user, status=Proposal.ACCEPTED)

        response = authenticated_admin_client.get(PROPOSAL_STATS_URL)

        assert response.status_code == http_status.HTTP_200_OK
        assert response.data['total'] == 3
        assert response.data['by_status']['draft'] == 1
        assert response.data['by_status']['sent'] == 1
        assert response.data['by_status']['accepted'] == 1

    def test_stats_total_value(self, authenticated_admin_client, admin_user):
        """Test stats endpoint returns correct total value."""
        ProposalFactory(owner=admin_user, total_value=Decimal('5000.00'))
        ProposalFactory(owner=admin_user, total_value=Decimal('3000.00'))

        response = authenticated_admin_client.get(PROPOSAL_STATS_URL)

        assert response.status_code == http_status.HTTP_200_OK
        assert Decimal(response.data['total_value']) == Decimal('8000.00')

    def test_stats_conversion_rate(self, authenticated_admin_client, admin_user):
        """Test stats endpoint calculates conversion rate."""
        ProposalFactory(owner=admin_user, status=Proposal.SENT)
        ProposalFactory(owner=admin_user, status=Proposal.ACCEPTED)
        ProposalFactory(owner=admin_user, status=Proposal.DECLINED)
        ProposalFactory(owner=admin_user, status=Proposal.CONVERTED)

        response = authenticated_admin_client.get(PROPOSAL_STATS_URL)

        assert response.status_code == http_status.HTTP_200_OK
        # 2 out of 4 non-draft = 50%
        assert response.data['conversion_rate'] == 50.0

    def test_stats_empty_returns_zeros(self, authenticated_admin_client):
        """Test stats with no proposals returns zero values."""
        response = authenticated_admin_client.get(PROPOSAL_STATS_URL)

        assert response.status_code == http_status.HTTP_200_OK
        assert response.data['total'] == 0
        assert response.data['conversion_rate'] == 0.0

    def test_stats_conversion_rate_all_drafts(self, authenticated_admin_client, admin_user):
        """Test conversion rate is 0 when all proposals are drafts."""
        ProposalFactory(owner=admin_user, status=Proposal.DRAFT)
        ProposalFactory(owner=admin_user, status=Proposal.DRAFT)

        response = authenticated_admin_client.get(PROPOSAL_STATS_URL)

        assert response.status_code == http_status.HTTP_200_OK
        assert response.data['conversion_rate'] == 0.0


# ============================================================================
# Proposal Activities Action Tests
# ============================================================================


@pytest.mark.django_db
class TestProposalActivitiesAction:
    """Tests for the activities action."""

    def test_list_activities_for_proposal(self, authenticated_admin_client, admin_user):
        """Test listing all activities for a proposal."""
        proposal = ProposalFactory(owner=admin_user)
        ProposalActivityFactory(
            proposal=proposal,
            activity_type=ProposalActivity.CREATED,
        )
        ProposalActivityFactory(
            proposal=proposal,
            activity_type=ProposalActivity.SENT,
        )

        response = authenticated_admin_client.get(
            proposal_action_url(proposal.id, 'activities')
        )

        assert response.status_code == http_status.HTTP_200_OK
        assert len(response.data) == 2

    def test_activities_for_proposal_with_no_activities(self, authenticated_admin_client, admin_user):
        """Test activities endpoint when proposal has no activities."""
        proposal = ProposalFactory(owner=admin_user)

        response = authenticated_admin_client.get(
            proposal_action_url(proposal.id, 'activities')
        )

        assert response.status_code == http_status.HTTP_200_OK
        assert len(response.data) == 0


# ============================================================================
# ProposalSection ViewSet Tests
# ============================================================================


@pytest.mark.django_db
class TestProposalSectionViewSet:
    """Tests for the ProposalSectionViewSet."""

    def test_list_sections(self, authenticated_admin_client, admin_user):
        """Test listing proposal sections."""
        proposal = ProposalFactory(owner=admin_user)
        ProposalSectionFactory(proposal=proposal)
        ProposalSectionFactory(proposal=proposal)

        response = authenticated_admin_client.get(SECTION_LIST_URL)

        assert response.status_code == http_status.HTTP_200_OK
        assert len(response.data['results']) == 2

    def test_create_section(self, authenticated_admin_client, admin_user):
        """Test creating a proposal section."""
        proposal = ProposalFactory(owner=admin_user)
        data = {
            'proposal': str(proposal.id),
            'title': 'New Section',
            'content': 'Section content.',
            'section_type': 'scope',
            'order': 1,
        }

        response = authenticated_admin_client.post(
            SECTION_LIST_URL, data, format='json'
        )

        assert response.status_code == http_status.HTTP_201_CREATED
        assert response.data['title'] == 'New Section'

    def test_update_section(self, authenticated_admin_client, admin_user):
        """Test updating a proposal section."""
        proposal = ProposalFactory(owner=admin_user)
        section = ProposalSectionFactory(proposal=proposal, title='Old')

        response = authenticated_admin_client.patch(
            f'{SECTION_LIST_URL}{section.id}/',
            {'title': 'Updated'},
            format='json',
        )

        assert response.status_code == http_status.HTTP_200_OK
        section.refresh_from_db()
        assert section.title == 'Updated'

    def test_delete_section(self, authenticated_admin_client, admin_user):
        """Test deleting a proposal section."""
        proposal = ProposalFactory(owner=admin_user)
        section = ProposalSectionFactory(proposal=proposal)
        section_id = section.id

        response = authenticated_admin_client.delete(
            f'{SECTION_LIST_URL}{section_id}/'
        )

        assert response.status_code == http_status.HTTP_204_NO_CONTENT
        assert not ProposalSection.objects.filter(id=section_id).exists()

    def test_filter_sections_by_proposal(self, authenticated_admin_client, admin_user):
        """Test filtering sections by proposal."""
        p1 = ProposalFactory(owner=admin_user)
        p2 = ProposalFactory(owner=admin_user)
        ProposalSectionFactory(proposal=p1)
        ProposalSectionFactory(proposal=p1)
        ProposalSectionFactory(proposal=p2)

        response = authenticated_admin_client.get(
            SECTION_LIST_URL, {'proposal': str(p1.id)}
        )

        assert response.status_code == http_status.HTTP_200_OK
        assert len(response.data['results']) == 2

    def test_filter_sections_by_type(self, authenticated_admin_client, admin_user):
        """Test filtering sections by section_type."""
        proposal = ProposalFactory(owner=admin_user)
        ProposalSectionFactory(proposal=proposal, section_type='scope')
        ProposalSectionFactory(proposal=proposal, section_type='timeline')
        ProposalSectionFactory(proposal=proposal, section_type='scope')

        response = authenticated_admin_client.get(
            SECTION_LIST_URL, {'section_type': 'scope'}
        )

        assert response.status_code == http_status.HTTP_200_OK
        assert len(response.data['results']) == 2

    def test_section_requires_authentication(self, api_client):
        """Test that section endpoints require authentication."""
        response = api_client.get(SECTION_LIST_URL)

        assert response.status_code == http_status.HTTP_401_UNAUTHORIZED

    def test_non_staff_sees_own_sections_only(self, api_client):
        """Test non-staff user sees only own proposal sections."""
        regular_user = UserFactory(is_staff=False, role='contributor')
        other_user = UserFactory()

        p1 = ProposalFactory(owner=regular_user)
        p2 = ProposalFactory(owner=other_user)
        ProposalSectionFactory(proposal=p1)
        ProposalSectionFactory(proposal=p2)

        api_client.force_authenticate(user=regular_user)
        response = api_client.get(SECTION_LIST_URL)

        assert response.status_code == http_status.HTTP_200_OK
        assert len(response.data['results']) == 1


# ============================================================================
# ProposalPricingOption ViewSet Tests
# ============================================================================


@pytest.mark.django_db
class TestProposalPricingOptionViewSet:
    """Tests for the ProposalPricingOptionViewSet."""

    def test_list_pricing_options(self, authenticated_admin_client, admin_user):
        """Test listing pricing options."""
        proposal = ProposalFactory(owner=admin_user)
        ProposalPricingOptionFactory(proposal=proposal)
        ProposalPricingOptionFactory(proposal=proposal)

        response = authenticated_admin_client.get(PRICING_OPTION_LIST_URL)

        assert response.status_code == http_status.HTTP_200_OK
        assert len(response.data['results']) == 2

    def test_create_pricing_option(self, authenticated_admin_client, admin_user):
        """Test creating a pricing option."""
        proposal = ProposalFactory(owner=admin_user)
        data = {
            'proposal': str(proposal.id),
            'name': 'Enterprise',
            'description': 'Full enterprise plan.',
            'price': '25000.00',
            'is_recommended': True,
            'features': ['Feature A', 'Feature B'],
            'order': 0,
        }

        response = authenticated_admin_client.post(
            PRICING_OPTION_LIST_URL, data, format='json'
        )

        assert response.status_code == http_status.HTTP_201_CREATED
        assert response.data['name'] == 'Enterprise'
        assert response.data['is_recommended'] is True

    def test_update_pricing_option(self, authenticated_admin_client, admin_user):
        """Test updating a pricing option."""
        proposal = ProposalFactory(owner=admin_user)
        option = ProposalPricingOptionFactory(proposal=proposal, name='Old')

        response = authenticated_admin_client.patch(
            f'{PRICING_OPTION_LIST_URL}{option.id}/',
            {'name': 'Updated', 'price': '3000.00'},
            format='json',
        )

        assert response.status_code == http_status.HTTP_200_OK
        option.refresh_from_db()
        assert option.name == 'Updated'
        assert option.price == Decimal('3000.00')

    def test_delete_pricing_option(self, authenticated_admin_client, admin_user):
        """Test deleting a pricing option."""
        proposal = ProposalFactory(owner=admin_user)
        option = ProposalPricingOptionFactory(proposal=proposal)
        option_id = option.id

        response = authenticated_admin_client.delete(
            f'{PRICING_OPTION_LIST_URL}{option_id}/'
        )

        assert response.status_code == http_status.HTTP_204_NO_CONTENT
        assert not ProposalPricingOption.objects.filter(id=option_id).exists()

    def test_filter_pricing_options_by_proposal(self, authenticated_admin_client, admin_user):
        """Test filtering pricing options by proposal."""
        p1 = ProposalFactory(owner=admin_user)
        p2 = ProposalFactory(owner=admin_user)
        ProposalPricingOptionFactory(proposal=p1)
        ProposalPricingOptionFactory(proposal=p2)

        response = authenticated_admin_client.get(
            PRICING_OPTION_LIST_URL, {'proposal': str(p1.id)}
        )

        assert response.status_code == http_status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_pricing_option_requires_authentication(self, api_client):
        """Test that pricing option endpoints require authentication."""
        response = api_client.get(PRICING_OPTION_LIST_URL)

        assert response.status_code == http_status.HTTP_401_UNAUTHORIZED

    def test_non_staff_sees_own_pricing_options_only(self, api_client):
        """Test non-staff user sees only own proposal pricing options."""
        regular_user = UserFactory(is_staff=False, role='contributor')
        other_user = UserFactory()

        p1 = ProposalFactory(owner=regular_user)
        p2 = ProposalFactory(owner=other_user)
        ProposalPricingOptionFactory(proposal=p1)
        ProposalPricingOptionFactory(proposal=p2)

        api_client.force_authenticate(user=regular_user)
        response = api_client.get(PRICING_OPTION_LIST_URL)

        assert response.status_code == http_status.HTTP_200_OK
        assert len(response.data['results']) == 1


# ============================================================================
# Client IP Extraction Tests
# ============================================================================


@pytest.mark.django_db
class TestClientIPExtraction:
    """Tests for client IP extraction in activities."""

    def test_ip_from_remote_addr(self, authenticated_admin_client, admin_user):
        """Test IP is recorded from REMOTE_ADDR."""
        proposal = ProposalFactory(owner=admin_user, status=Proposal.DRAFT)

        authenticated_admin_client.post(
            proposal_action_url(proposal.id, 'send')
        )

        activity = proposal.activities.filter(
            activity_type=ProposalActivity.SENT
        ).first()
        assert activity is not None
        # The test client sets REMOTE_ADDR by default
        assert activity.ip_address is not None

    def test_ip_from_x_forwarded_for(self, api_client, admin_user):
        """Test IP is extracted from X-Forwarded-For header."""
        api_client.force_authenticate(user=admin_user)
        proposal = ProposalFactory(owner=admin_user, status=Proposal.DRAFT)

        api_client.post(
            proposal_action_url(proposal.id, 'send'),
            HTTP_X_FORWARDED_FOR='203.0.113.50, 70.41.3.18',
        )

        activity = proposal.activities.filter(
            activity_type=ProposalActivity.SENT
        ).first()
        assert activity is not None
        assert activity.ip_address == '203.0.113.50'
