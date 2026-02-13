"""
Tests for proposals app models.

Tests cover:
- Proposal model creation, __str__, save (auto-number generation), is_expired
- ProposalSection model creation, __str__, ordering
- ProposalPricingOption model creation, __str__, ordering
- ProposalActivity model creation, __str__, ordering
- Unique constraint on proposal_number
- Default values and field validation
"""

import uuid
import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone
from django.db import IntegrityError

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
# Proposal Model Tests
# ============================================================================


@pytest.mark.django_db
class TestProposalModel:
    """Tests for the Proposal model."""

    def test_create_proposal(self):
        """Test creating a proposal with factory defaults."""
        proposal = ProposalFactory()

        assert proposal.pk is not None
        assert isinstance(proposal.id, uuid.UUID)
        assert proposal.status == Proposal.DRAFT
        assert proposal.total_value == Decimal('5000.00')
        assert proposal.currency == 'USD'
        assert proposal.client is not None
        assert proposal.owner is not None

    def test_str_representation(self):
        """Test the __str__ method returns proposal_number - title."""
        proposal = ProposalFactory(title='Website Redesign')

        expected = f"{proposal.proposal_number} - Website Redesign"
        assert str(proposal) == expected

    def test_auto_generate_proposal_number_first(self):
        """Test that the first proposal gets PRP-00001."""
        proposal = ProposalFactory()

        assert proposal.proposal_number == 'PRP-00001'

    def test_auto_generate_proposal_number_sequential(self):
        """Test sequential auto-numbering of proposals."""
        p1 = ProposalFactory()
        p2 = ProposalFactory()
        p3 = ProposalFactory()

        assert p1.proposal_number == 'PRP-00001'
        assert p2.proposal_number == 'PRP-00002'
        assert p3.proposal_number == 'PRP-00003'

    def test_auto_generate_skips_when_number_set(self):
        """Test that auto-generation is skipped when proposal_number is preset."""
        proposal = ProposalFactory(proposal_number='PRP-99999')

        assert proposal.proposal_number == 'PRP-99999'

    def test_proposal_number_unique_constraint(self):
        """Test that proposal_number is unique."""
        ProposalFactory(proposal_number='PRP-UNIQUE')

        with pytest.raises(IntegrityError):
            ProposalFactory(proposal_number='PRP-UNIQUE')

    def test_default_status_is_draft(self):
        """Test that the default status is DRAFT."""
        proposal = ProposalFactory()

        assert proposal.status == Proposal.DRAFT

    def test_default_total_value(self):
        """Test default total_value is 0.00 when not specified."""
        client = ClientFactory()
        owner = UserFactory()
        proposal = Proposal.objects.create(
            client=client,
            title='Zero Value',
            valid_until=date.today() + timedelta(days=30),
            owner=owner,
        )

        assert proposal.total_value == Decimal('0.00')

    def test_default_currency_is_usd(self):
        """Test default currency is USD."""
        client = ClientFactory()
        proposal = Proposal.objects.create(
            client=client,
            title='Default Currency',
            valid_until=date.today() + timedelta(days=30),
        )

        assert proposal.currency == 'USD'

    def test_default_metadata_is_empty_dict(self):
        """Test default metadata is an empty dict."""
        proposal = ProposalFactory()

        assert proposal.metadata == {}

    def test_uuid_primary_key(self):
        """Test that proposal has UUID primary key."""
        proposal = ProposalFactory()

        assert isinstance(proposal.id, uuid.UUID)

    def test_timestamps_are_set(self):
        """Test that created_at and updated_at are auto-set."""
        proposal = ProposalFactory()

        assert proposal.created_at is not None
        assert proposal.updated_at is not None

    def test_ordering_by_created_at_descending(self):
        """Test that default ordering is -created_at."""
        p1 = ProposalFactory()
        p2 = ProposalFactory()
        p3 = ProposalFactory()

        proposals = list(Proposal.objects.all())
        assert proposals[0] == p3
        assert proposals[1] == p2
        assert proposals[2] == p1

    def test_client_cascade_delete(self):
        """Test that deleting a client cascades to proposals."""
        proposal = ProposalFactory()
        client = proposal.client
        proposal_id = proposal.id

        client.delete()

        assert not Proposal.objects.filter(id=proposal_id).exists()

    def test_owner_set_null_on_delete(self):
        """Test that deleting the owner sets it to NULL."""
        proposal = ProposalFactory()
        owner = proposal.owner

        owner.delete()
        proposal.refresh_from_db()

        assert proposal.owner is None

    def test_contract_set_null_on_delete(self):
        """Test that deleting the linked contract sets it to NULL."""
        from apps.contracts.models import Contract

        proposal = ProposalFactory()
        contract = Contract.objects.create(
            client=proposal.client,
            title='Test Contract',
            description='A test contract',
            contract_type=Contract.FIXED_PRICE,
            status=Contract.DRAFT,
            start_date=date.today(),
            value=Decimal('5000.00'),
            currency='USD',
        )
        proposal.contract = contract
        proposal.save()

        contract.delete()
        proposal.refresh_from_db()

        assert proposal.contract is None

    def test_status_choices_are_valid(self):
        """Test all status choices."""
        valid_statuses = [
            Proposal.DRAFT,
            Proposal.SENT,
            Proposal.VIEWED,
            Proposal.ACCEPTED,
            Proposal.DECLINED,
            Proposal.EXPIRED,
            Proposal.CONVERTED,
        ]
        choice_values = [choice[0] for choice in Proposal.STATUS_CHOICES]
        for status_val in valid_statuses:
            assert status_val in choice_values

    def test_tracking_date_fields_nullable(self):
        """Test that tracking date fields can be null."""
        proposal = ProposalFactory()

        assert proposal.sent_at is None
        assert proposal.viewed_at is None
        assert proposal.accepted_at is None
        assert proposal.declined_at is None

    def test_client_message_blank_by_default(self):
        """Test that client_message is blank by default."""
        proposal = ProposalFactory()

        assert proposal.client_message == ''

    def test_signature_blank_by_default(self):
        """Test that signature is blank by default."""
        proposal = ProposalFactory()

        assert proposal.signature == ''

    def test_pdf_file_null_by_default(self):
        """Test that pdf_file is null by default."""
        proposal = ProposalFactory()

        assert not proposal.pdf_file


# ============================================================================
# Proposal is_expired Property Tests
# ============================================================================


@pytest.mark.django_db
class TestProposalIsExpired:
    """Tests for the Proposal.is_expired property."""

    def test_not_expired_when_valid_until_in_future(self):
        """Test proposal is not expired when valid_until is in the future."""
        proposal = ProposalFactory(
            valid_until=date.today() + timedelta(days=30),
        )

        assert proposal.is_expired is False

    def test_expired_when_valid_until_in_past(self):
        """Test proposal is expired when valid_until is in the past."""
        proposal = ProposalFactory(
            valid_until=date.today() - timedelta(days=1),
        )

        assert proposal.is_expired is True

    def test_not_expired_when_accepted(self):
        """Test accepted proposal is never considered expired."""
        proposal = ProposalFactory(
            status=Proposal.ACCEPTED,
            valid_until=date.today() - timedelta(days=30),
        )

        assert proposal.is_expired is False

    def test_not_expired_when_converted(self):
        """Test converted proposal is never considered expired."""
        proposal = ProposalFactory(
            status=Proposal.CONVERTED,
            valid_until=date.today() - timedelta(days=30),
        )

        assert proposal.is_expired is False

    def test_expired_when_draft_and_past_date(self):
        """Test draft proposal with past valid_until is expired."""
        proposal = ProposalFactory(
            status=Proposal.DRAFT,
            valid_until=date.today() - timedelta(days=1),
        )

        assert proposal.is_expired is True

    def test_expired_when_sent_and_past_date(self):
        """Test sent proposal with past valid_until is expired."""
        proposal = ProposalFactory(
            status=Proposal.SENT,
            valid_until=date.today() - timedelta(days=1),
        )

        assert proposal.is_expired is True

    def test_expired_when_declined_and_past_date(self):
        """Test declined proposal with past valid_until is expired."""
        proposal = ProposalFactory(
            status=Proposal.DECLINED,
            valid_until=date.today() - timedelta(days=1),
        )

        assert proposal.is_expired is True

    def test_expired_on_today_boundary(self):
        """Test proposal expiration on exact date boundary (today)."""
        proposal = ProposalFactory(
            valid_until=date.today(),
        )

        # timezone.now().date() > valid_until, so if valid_until == today, not expired
        assert proposal.is_expired is False


# ============================================================================
# ProposalSection Model Tests
# ============================================================================


@pytest.mark.django_db
class TestProposalSectionModel:
    """Tests for the ProposalSection model."""

    def test_create_section(self):
        """Test creating a proposal section."""
        section = ProposalSectionFactory()

        assert section.pk is not None
        assert isinstance(section.id, uuid.UUID)
        assert section.proposal is not None
        assert section.section_type == ProposalSection.CUSTOM

    def test_str_representation(self):
        """Test the __str__ method."""
        section = ProposalSectionFactory(title='Project Scope')

        expected = f"{section.proposal.proposal_number} - Project Scope"
        assert str(section) == expected

    def test_ordering_by_order_field(self):
        """Test sections are ordered by the order field."""
        proposal = ProposalFactory()
        s3 = ProposalSectionFactory(proposal=proposal, order=3)
        s1 = ProposalSectionFactory(proposal=proposal, order=1)
        s2 = ProposalSectionFactory(proposal=proposal, order=2)

        sections = list(proposal.sections.all())
        assert sections[0] == s1
        assert sections[1] == s2
        assert sections[2] == s3

    def test_section_type_choices(self):
        """Test all section type choices are valid."""
        valid_types = [
            ProposalSection.OVERVIEW,
            ProposalSection.SCOPE,
            ProposalSection.TIMELINE,
            ProposalSection.PRICING,
            ProposalSection.TERMS,
            ProposalSection.CUSTOM,
        ]
        choice_values = [c[0] for c in ProposalSection.SECTION_TYPE_CHOICES]
        for st in valid_types:
            assert st in choice_values

    def test_cascade_delete_with_proposal(self):
        """Test section is deleted when proposal is deleted."""
        section = ProposalSectionFactory()
        section_id = section.id
        proposal = section.proposal

        proposal.delete()

        assert not ProposalSection.objects.filter(id=section_id).exists()

    def test_content_blank_allowed(self):
        """Test section content can be blank."""
        section = ProposalSectionFactory(content='')

        assert section.content == ''

    def test_default_order_is_zero(self):
        """Test default order value."""
        proposal = ProposalFactory()
        section = ProposalSection.objects.create(
            proposal=proposal,
            title='Default Order',
        )

        assert section.order == 0

    def test_timestamps_are_set(self):
        """Test that created_at and updated_at are auto-set."""
        section = ProposalSectionFactory()

        assert section.created_at is not None
        assert section.updated_at is not None


# ============================================================================
# ProposalPricingOption Model Tests
# ============================================================================


@pytest.mark.django_db
class TestProposalPricingOptionModel:
    """Tests for the ProposalPricingOption model."""

    def test_create_pricing_option(self):
        """Test creating a pricing option."""
        option = ProposalPricingOptionFactory()

        assert option.pk is not None
        assert isinstance(option.id, uuid.UUID)
        assert option.price == Decimal('2500.00')
        assert option.is_recommended is False

    def test_str_representation(self):
        """Test the __str__ method."""
        option = ProposalPricingOptionFactory(name='Basic Plan', price=Decimal('999.00'))

        assert str(option) == 'Basic Plan - 999.00'

    def test_ordering_by_order_field(self):
        """Test pricing options are ordered by the order field."""
        proposal = ProposalFactory()
        o3 = ProposalPricingOptionFactory(proposal=proposal, order=3, name='Premium')
        o1 = ProposalPricingOptionFactory(proposal=proposal, order=1, name='Basic')
        o2 = ProposalPricingOptionFactory(proposal=proposal, order=2, name='Standard')

        options = list(proposal.pricing_options.all())
        assert options[0] == o1
        assert options[1] == o2
        assert options[2] == o3

    def test_is_recommended_field(self):
        """Test is_recommended boolean field."""
        option = ProposalPricingOptionFactory(is_recommended=True)

        assert option.is_recommended is True

    def test_features_json_field(self):
        """Test features JSON field stores list data."""
        features = ['Feature A', 'Feature B', 'Feature C']
        option = ProposalPricingOptionFactory(features=features)

        assert option.features == features
        assert len(option.features) == 3

    def test_features_default_is_list(self):
        """Test default features is an empty list."""
        proposal = ProposalFactory()
        option = ProposalPricingOption.objects.create(
            proposal=proposal,
            name='No Features',
            price=Decimal('100.00'),
        )

        assert option.features == []

    def test_cascade_delete_with_proposal(self):
        """Test pricing option is deleted when proposal is deleted."""
        option = ProposalPricingOptionFactory()
        option_id = option.id
        proposal = option.proposal

        proposal.delete()

        assert not ProposalPricingOption.objects.filter(id=option_id).exists()

    def test_description_blank_allowed(self):
        """Test description can be blank."""
        option = ProposalPricingOptionFactory(description='')

        assert option.description == ''

    def test_timestamps_are_set(self):
        """Test that created_at and updated_at are auto-set."""
        option = ProposalPricingOptionFactory()

        assert option.created_at is not None
        assert option.updated_at is not None


# ============================================================================
# ProposalActivity Model Tests
# ============================================================================


@pytest.mark.django_db
class TestProposalActivityModel:
    """Tests for the ProposalActivity model."""

    def test_create_activity(self):
        """Test creating a proposal activity."""
        activity = ProposalActivityFactory()

        assert activity.pk is not None
        assert isinstance(activity.id, uuid.UUID)
        assert activity.activity_type == ProposalActivity.CREATED

    def test_str_representation(self):
        """Test the __str__ method."""
        activity = ProposalActivityFactory(activity_type=ProposalActivity.SENT)

        expected = f"{activity.proposal.proposal_number} - sent"
        assert str(activity) == expected

    def test_activity_type_choices(self):
        """Test all activity type choices are valid."""
        valid_types = [
            ProposalActivity.CREATED,
            ProposalActivity.SENT,
            ProposalActivity.VIEWED,
            ProposalActivity.ACCEPTED,
            ProposalActivity.DECLINED,
            ProposalActivity.EDITED,
            ProposalActivity.CONVERTED,
        ]
        choice_values = [c[0] for c in ProposalActivity.ACTIVITY_TYPE_CHOICES]
        for at in valid_types:
            assert at in choice_values

    def test_ordering_by_created_at_descending(self):
        """Test activities are ordered by -created_at."""
        proposal = ProposalFactory()
        a1 = ProposalActivityFactory(proposal=proposal, activity_type=ProposalActivity.CREATED)
        a2 = ProposalActivityFactory(proposal=proposal, activity_type=ProposalActivity.SENT)
        a3 = ProposalActivityFactory(proposal=proposal, activity_type=ProposalActivity.VIEWED)

        activities = list(proposal.activities.all())
        # Latest created first
        assert activities[0] == a3
        assert activities[1] == a2
        assert activities[2] == a1

    def test_cascade_delete_with_proposal(self):
        """Test activity is deleted when proposal is deleted."""
        activity = ProposalActivityFactory()
        activity_id = activity.id
        proposal = activity.proposal

        proposal.delete()

        assert not ProposalActivity.objects.filter(id=activity_id).exists()

    def test_user_set_null_on_delete(self):
        """Test user is set to null when user is deleted."""
        activity = ProposalActivityFactory()
        user = activity.user

        user.delete()
        activity.refresh_from_db()

        assert activity.user is None

    def test_ip_address_nullable(self):
        """Test ip_address can be null."""
        activity = ProposalActivityFactory(ip_address=None)

        assert activity.ip_address is None

    def test_metadata_default_is_empty_dict(self):
        """Test default metadata is empty dict."""
        proposal = ProposalFactory()
        activity = ProposalActivity.objects.create(
            proposal=proposal,
            activity_type=ProposalActivity.CREATED,
        )

        assert activity.metadata == {}

    def test_metadata_stores_json(self):
        """Test metadata stores JSON data correctly."""
        metadata = {'contract_id': 'abc-123', 'notes': 'converted'}
        activity = ProposalActivityFactory(metadata=metadata)

        assert activity.metadata == metadata
        assert activity.metadata['contract_id'] == 'abc-123'

    def test_created_at_auto_set(self):
        """Test that created_at is auto-set."""
        activity = ProposalActivityFactory()

        assert activity.created_at is not None


# ============================================================================
# Proposal Model Relationships Tests
# ============================================================================


@pytest.mark.django_db
class TestProposalRelationships:
    """Tests for Proposal model relationships (sections, pricing_options, activities)."""

    def test_sections_related_name(self):
        """Test accessing sections via proposal.sections."""
        proposal = ProposalFactory()
        ProposalSectionFactory(proposal=proposal, title='Scope')
        ProposalSectionFactory(proposal=proposal, title='Timeline')

        assert proposal.sections.count() == 2

    def test_pricing_options_related_name(self):
        """Test accessing pricing options via proposal.pricing_options."""
        proposal = ProposalFactory()
        ProposalPricingOptionFactory(proposal=proposal, name='Basic')
        ProposalPricingOptionFactory(proposal=proposal, name='Premium')
        ProposalPricingOptionFactory(proposal=proposal, name='Enterprise')

        assert proposal.pricing_options.count() == 3

    def test_activities_related_name(self):
        """Test accessing activities via proposal.activities."""
        proposal = ProposalFactory()
        ProposalActivityFactory(proposal=proposal, activity_type=ProposalActivity.CREATED)
        ProposalActivityFactory(proposal=proposal, activity_type=ProposalActivity.SENT)

        assert proposal.activities.count() == 2

    def test_client_proposals_related_name(self):
        """Test accessing proposals via client.proposals."""
        client = ClientFactory()
        ProposalFactory(client=client)
        ProposalFactory(client=client)

        assert client.proposals.count() == 2

    def test_owner_proposals_related_name(self):
        """Test accessing proposals via user.owned_proposals."""
        user = UserFactory()
        ProposalFactory(owner=user)
        ProposalFactory(owner=user)

        assert user.owned_proposals.count() == 2
