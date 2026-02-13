"""
Tests for proposals app serializers.

Tests cover:
- ProposalListSerializer (computed fields, client_name, counts)
- ProposalDetailSerializer (nested sections, pricing, activities, owner_name)
- ProposalCreateUpdateSerializer (validation, read-only fields)
- ProposalSectionSerializer
- ProposalPricingOptionSerializer
- ProposalActivitySerializer (user_name computed field)
- ProposalStatsSerializer
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone

from apps.proposals.models import Proposal
from apps.proposals.serializers import (
    ProposalListSerializer,
    ProposalDetailSerializer,
    ProposalCreateUpdateSerializer,
    ProposalSectionSerializer,
    ProposalPricingOptionSerializer,
    ProposalActivitySerializer,
    ProposalStatsSerializer,
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
# ProposalSectionSerializer Tests
# ============================================================================


@pytest.mark.django_db
class TestProposalSectionSerializer:
    """Tests for the ProposalSectionSerializer."""

    def test_serialize_section(self):
        """Test serializing a proposal section."""
        section = ProposalSectionFactory(
            title='Project Scope',
            content='Detailed scope of work.',
            section_type='scope',
            order=1,
        )

        serializer = ProposalSectionSerializer(section)
        data = serializer.data

        assert data['title'] == 'Project Scope'
        assert data['content'] == 'Detailed scope of work.'
        assert data['section_type'] == 'scope'
        assert data['order'] == 1

    def test_read_only_fields(self):
        """Test that id, created_at, updated_at are read-only."""
        section = ProposalSectionFactory()
        serializer = ProposalSectionSerializer(section)
        data = serializer.data

        assert 'id' in data
        assert 'created_at' in data
        assert 'updated_at' in data

    def test_deserialize_section(self):
        """Test deserializing section data for creation."""
        proposal = ProposalFactory()
        data = {
            'proposal': str(proposal.id),
            'title': 'New Section',
            'content': 'Section content',
            'section_type': 'custom',
            'order': 0,
        }
        serializer = ProposalSectionSerializer(data=data)

        assert serializer.is_valid(), serializer.errors
        section = serializer.save()
        assert section.title == 'New Section'


# ============================================================================
# ProposalPricingOptionSerializer Tests
# ============================================================================


@pytest.mark.django_db
class TestProposalPricingOptionSerializer:
    """Tests for the ProposalPricingOptionSerializer."""

    def test_serialize_pricing_option(self):
        """Test serializing a pricing option."""
        option = ProposalPricingOptionFactory(
            name='Premium Plan',
            price=Decimal('9999.99'),
            is_recommended=True,
            features=['Feature X', 'Feature Y'],
        )

        serializer = ProposalPricingOptionSerializer(option)
        data = serializer.data

        assert data['name'] == 'Premium Plan'
        assert Decimal(data['price']) == Decimal('9999.99')
        assert data['is_recommended'] is True
        assert data['features'] == ['Feature X', 'Feature Y']

    def test_deserialize_pricing_option(self):
        """Test deserializing pricing option data."""
        proposal = ProposalFactory()
        data = {
            'proposal': str(proposal.id),
            'name': 'Basic',
            'price': '1000.00',
            'is_recommended': False,
            'features': ['Support'],
            'order': 0,
        }
        serializer = ProposalPricingOptionSerializer(data=data)

        assert serializer.is_valid(), serializer.errors
        option = serializer.save()
        assert option.name == 'Basic'

    def test_read_only_fields(self):
        """Test that id, created_at, updated_at are read-only."""
        option = ProposalPricingOptionFactory()
        serializer = ProposalPricingOptionSerializer(option)
        data = serializer.data

        assert 'id' in data
        assert 'created_at' in data
        assert 'updated_at' in data


# ============================================================================
# ProposalActivitySerializer Tests
# ============================================================================


@pytest.mark.django_db
class TestProposalActivitySerializer:
    """Tests for the ProposalActivitySerializer."""

    def test_serialize_activity(self):
        """Test serializing a proposal activity."""
        activity = ProposalActivityFactory(
            activity_type='sent',
            description='Proposal was sent to client.',
            ip_address='10.0.0.1',
        )

        serializer = ProposalActivitySerializer(activity)
        data = serializer.data

        assert data['activity_type'] == 'sent'
        assert data['description'] == 'Proposal was sent to client.'
        assert data['ip_address'] == '10.0.0.1'

    def test_user_name_field_with_user(self):
        """Test user_name computed field when user exists."""
        user = UserFactory(first_name='Alice', last_name='Johnson')
        activity = ProposalActivityFactory(user=user)

        serializer = ProposalActivitySerializer(activity)
        data = serializer.data

        assert data['user_name'] == 'Alice Johnson'

    def test_user_name_field_without_user(self):
        """Test user_name computed field when user is None."""
        activity = ProposalActivityFactory(user=None)

        serializer = ProposalActivitySerializer(activity)
        data = serializer.data

        assert data['user_name'] is None

    def test_all_fields_are_read_only(self):
        """Test that all fields in ProposalActivitySerializer are read-only."""
        serializer = ProposalActivitySerializer()
        read_only = serializer.Meta.read_only_fields

        assert 'id' in read_only
        assert 'proposal' in read_only
        assert 'activity_type' in read_only
        assert 'description' in read_only
        assert 'user' in read_only
        assert 'ip_address' in read_only
        assert 'metadata' in read_only
        assert 'created_at' in read_only


# ============================================================================
# ProposalListSerializer Tests
# ============================================================================


@pytest.mark.django_db
class TestProposalListSerializer:
    """Tests for the ProposalListSerializer."""

    def test_serialize_proposal_list(self):
        """Test serializing a proposal for list view."""
        proposal = ProposalFactory(title='Web Development')

        serializer = ProposalListSerializer(proposal)
        data = serializer.data

        assert data['title'] == 'Web Development'
        assert data['proposal_number'] == proposal.proposal_number
        assert data['status'] == 'draft'
        assert 'id' in data
        assert 'total_value' in data
        assert 'currency' in data
        assert 'valid_until' in data

    def test_client_name_field(self):
        """Test client_name computed field."""
        client = ClientFactory(company_name='Acme Corp')
        proposal = ProposalFactory(client=client)

        serializer = ProposalListSerializer(proposal)
        data = serializer.data

        assert data['client_name'] == client.get_display_name()

    def test_client_id_field(self):
        """Test client_id computed field returns string UUID."""
        proposal = ProposalFactory()

        serializer = ProposalListSerializer(proposal)
        data = serializer.data

        assert data['client_id'] == str(proposal.client.id)

    def test_is_expired_field(self):
        """Test is_expired read-only field."""
        proposal = ProposalFactory(
            valid_until=date.today() - timedelta(days=1),
        )

        serializer = ProposalListSerializer(proposal)
        data = serializer.data

        assert data['is_expired'] is True

    def test_sections_count_field(self):
        """Test sections_count computed field."""
        proposal = ProposalFactory()
        ProposalSectionFactory(proposal=proposal)
        ProposalSectionFactory(proposal=proposal)

        serializer = ProposalListSerializer(proposal)
        data = serializer.data

        assert data['sections_count'] == 2

    def test_pricing_options_count_field(self):
        """Test pricing_options_count computed field."""
        proposal = ProposalFactory()
        ProposalPricingOptionFactory(proposal=proposal)
        ProposalPricingOptionFactory(proposal=proposal)
        ProposalPricingOptionFactory(proposal=proposal)

        serializer = ProposalListSerializer(proposal)
        data = serializer.data

        assert data['pricing_options_count'] == 3

    def test_read_only_fields(self):
        """Test that id, proposal_number, created_at are read-only."""
        serializer = ProposalListSerializer()
        read_only = serializer.Meta.read_only_fields

        assert 'id' in read_only
        assert 'proposal_number' in read_only
        assert 'created_at' in read_only

    def test_list_serializer_excludes_heavy_fields(self):
        """Test that list serializer does not include heavy nested data."""
        proposal = ProposalFactory()
        serializer = ProposalListSerializer(proposal)
        data = serializer.data

        assert 'sections' not in data
        assert 'pricing_options' not in data
        assert 'activities' not in data
        assert 'description' not in data


# ============================================================================
# ProposalDetailSerializer Tests
# ============================================================================


@pytest.mark.django_db
class TestProposalDetailSerializer:
    """Tests for the ProposalDetailSerializer."""

    def test_serialize_proposal_detail(self):
        """Test serializing a proposal for detail view."""
        proposal = ProposalFactory(title='Detailed Proposal')

        serializer = ProposalDetailSerializer(proposal)
        data = serializer.data

        assert data['title'] == 'Detailed Proposal'
        assert 'sections' in data
        assert 'pricing_options' in data
        assert 'activities' in data
        assert 'is_expired' in data

    def test_nested_sections(self):
        """Test that sections are nested in detail serializer."""
        proposal = ProposalFactory()
        ProposalSectionFactory(proposal=proposal, title='Scope')
        ProposalSectionFactory(proposal=proposal, title='Timeline')

        serializer = ProposalDetailSerializer(proposal)
        data = serializer.data

        assert len(data['sections']) == 2
        section_titles = [s['title'] for s in data['sections']]
        assert 'Scope' in section_titles
        assert 'Timeline' in section_titles

    def test_nested_pricing_options(self):
        """Test that pricing options are nested in detail serializer."""
        proposal = ProposalFactory()
        ProposalPricingOptionFactory(proposal=proposal, name='Basic')
        ProposalPricingOptionFactory(proposal=proposal, name='Premium')

        serializer = ProposalDetailSerializer(proposal)
        data = serializer.data

        assert len(data['pricing_options']) == 2

    def test_nested_activities(self):
        """Test that activities are nested in detail serializer."""
        proposal = ProposalFactory()
        ProposalActivityFactory(proposal=proposal, activity_type='created')
        ProposalActivityFactory(proposal=proposal, activity_type='sent')

        serializer = ProposalDetailSerializer(proposal)
        data = serializer.data

        assert len(data['activities']) == 2

    def test_owner_name_with_owner(self):
        """Test owner_name computed field when owner exists."""
        owner = UserFactory(first_name='Bob', last_name='Smith')
        proposal = ProposalFactory(owner=owner)

        serializer = ProposalDetailSerializer(proposal)
        data = serializer.data

        assert data['owner_name'] == 'Bob Smith'

    def test_owner_name_without_owner(self):
        """Test owner_name computed field when owner is None."""
        proposal = ProposalFactory(owner=None)

        serializer = ProposalDetailSerializer(proposal)
        data = serializer.data

        assert data['owner_name'] is None

    def test_client_name_field(self):
        """Test client_name computed field."""
        client = ClientFactory(company_name='MegaCorp')
        proposal = ProposalFactory(client=client)

        serializer = ProposalDetailSerializer(proposal)
        data = serializer.data

        assert data['client_name'] == 'MegaCorp'

    def test_read_only_fields(self):
        """Test read-only fields in detail serializer."""
        serializer = ProposalDetailSerializer()
        read_only = serializer.Meta.read_only_fields

        assert 'id' in read_only
        assert 'proposal_number' in read_only
        assert 'created_at' in read_only
        assert 'updated_at' in read_only


# ============================================================================
# ProposalCreateUpdateSerializer Tests
# ============================================================================


@pytest.mark.django_db
class TestProposalCreateUpdateSerializer:
    """Tests for the ProposalCreateUpdateSerializer."""

    def test_valid_create_data(self):
        """Test creating a proposal with valid data."""
        client = ClientFactory()
        data = {
            'title': 'New Proposal',
            'description': 'A fresh proposal.',
            'client': str(client.id),
            'valid_until': (date.today() + timedelta(days=30)).isoformat(),
            'total_value': '10000.00',
            'currency': 'EUR',
        }

        serializer = ProposalCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

        proposal = serializer.save()
        assert proposal.title == 'New Proposal'
        assert proposal.currency == 'EUR'
        assert proposal.proposal_number.startswith('PRP-')

    def test_valid_until_past_date_rejected_on_create(self):
        """Test that valid_until in the past is rejected for new proposals."""
        client = ClientFactory()
        data = {
            'title': 'Expired Proposal',
            'client': str(client.id),
            'valid_until': (date.today() - timedelta(days=1)).isoformat(),
            'total_value': '1000.00',
        }

        serializer = ProposalCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'valid_until' in serializer.errors

    def test_valid_until_past_date_allowed_on_update(self):
        """Test that valid_until in the past is allowed when updating."""
        proposal = ProposalFactory()
        data = {
            'title': proposal.title,
            'client': str(proposal.client.id),
            'valid_until': (date.today() - timedelta(days=1)).isoformat(),
            'total_value': str(proposal.total_value),
        }

        serializer = ProposalCreateUpdateSerializer(instance=proposal, data=data)
        assert serializer.is_valid(), serializer.errors

    def test_read_only_fields_ignored_on_create(self):
        """Test that read-only fields (id, proposal_number) are ignored."""
        client = ClientFactory()
        data = {
            'id': 'should-be-ignored',
            'proposal_number': 'CUSTOM-001',
            'title': 'Read-only Test',
            'client': str(client.id),
            'valid_until': (date.today() + timedelta(days=30)).isoformat(),
            'total_value': '5000.00',
        }

        serializer = ProposalCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

        proposal = serializer.save()
        # proposal_number should be auto-generated, not 'CUSTOM-001'
        assert proposal.proposal_number != 'CUSTOM-001'
        assert proposal.proposal_number.startswith('PRP-')

    def test_fields_included(self):
        """Test that the correct fields are included."""
        serializer = ProposalCreateUpdateSerializer()
        fields = serializer.Meta.fields

        assert 'title' in fields
        assert 'description' in fields
        assert 'client' in fields
        assert 'valid_until' in fields
        assert 'total_value' in fields
        assert 'currency' in fields
        assert 'metadata' in fields

    def test_missing_required_fields(self):
        """Test that required fields cause validation errors when missing."""
        serializer = ProposalCreateUpdateSerializer(data={})
        assert not serializer.is_valid()
        assert 'title' in serializer.errors
        assert 'client' in serializer.errors
        assert 'valid_until' in serializer.errors

    def test_update_existing_proposal(self):
        """Test updating an existing proposal."""
        proposal = ProposalFactory(title='Old Title')
        data = {
            'title': 'Updated Title',
            'client': str(proposal.client.id),
            'valid_until': proposal.valid_until.isoformat(),
            'total_value': '7500.00',
        }

        serializer = ProposalCreateUpdateSerializer(instance=proposal, data=data)
        assert serializer.is_valid(), serializer.errors

        updated = serializer.save()
        assert updated.title == 'Updated Title'
        assert updated.total_value == Decimal('7500.00')

    def test_metadata_json_field(self):
        """Test that metadata JSON field is handled correctly."""
        client = ClientFactory()
        data = {
            'title': 'Meta Proposal',
            'client': str(client.id),
            'valid_until': (date.today() + timedelta(days=30)).isoformat(),
            'total_value': '5000.00',
            'metadata': {'custom_key': 'custom_value'},
        }

        serializer = ProposalCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

        proposal = serializer.save()
        assert proposal.metadata == {'custom_key': 'custom_value'}


# ============================================================================
# ProposalStatsSerializer Tests
# ============================================================================


@pytest.mark.django_db
class TestProposalStatsSerializer:
    """Tests for the ProposalStatsSerializer."""

    def test_serialize_stats(self):
        """Test serializing stats data."""
        stats_data = {
            'total': 10,
            'by_status': {
                'draft': 3,
                'sent': 2,
                'accepted': 4,
                'declined': 1,
            },
            'total_value': Decimal('50000.00'),
            'conversion_rate': 66.67,
        }

        serializer = ProposalStatsSerializer(stats_data)
        data = serializer.data

        assert data['total'] == 10
        assert data['by_status']['draft'] == 3
        assert Decimal(data['total_value']) == Decimal('50000.00')
        assert data['conversion_rate'] == 66.67

    def test_zero_values(self):
        """Test serializing zero stats."""
        stats_data = {
            'total': 0,
            'by_status': {},
            'total_value': Decimal('0.00'),
            'conversion_rate': 0.0,
        }

        serializer = ProposalStatsSerializer(stats_data)
        data = serializer.data

        assert data['total'] == 0
        assert data['total_value'] == '0.00'
        assert data['conversion_rate'] == 0.0

    def test_stats_serializer_fields(self):
        """Test that ProposalStatsSerializer has the expected fields."""
        serializer = ProposalStatsSerializer()

        assert 'total' in serializer.fields
        assert 'by_status' in serializer.fields
        assert 'total_value' in serializer.fields
        assert 'conversion_rate' in serializer.fields
