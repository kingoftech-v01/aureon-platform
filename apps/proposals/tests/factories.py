"""
Factory Boy factories for the proposals app.

Provides factories for:
- Proposal
- ProposalSection
- ProposalPricingOption
- ProposalActivity
"""

import factory
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.proposals.models import (
    Proposal,
    ProposalSection,
    ProposalPricingOption,
    ProposalActivity,
)
from apps.clients.models import Client

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for the custom User model."""

    class Meta:
        model = User
        skip_postgeneration_save = True

    id = factory.Faker('uuid4')
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'SecurePass123!')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    role = User.ADMIN
    is_active = True
    is_verified = True
    is_staff = True


class ClientFactory(factory.django.DjangoModelFactory):
    """Factory for the Client model."""

    class Meta:
        model = Client

    client_type = Client.COMPANY
    company_name = factory.Sequence(lambda n: f'Test Company {n}')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.LazyAttribute(
        lambda obj: f'{obj.first_name.lower()}.{obj.last_name.lower()}@company.com'
    )
    lifecycle_stage = Client.ACTIVE
    is_active = True
    owner = factory.SubFactory(UserFactory)


class ProposalFactory(factory.django.DjangoModelFactory):
    """Factory for the Proposal model."""

    class Meta:
        model = Proposal

    client = factory.SubFactory(ClientFactory)
    title = factory.Sequence(lambda n: f'Proposal {n}')
    description = factory.Faker('paragraph')
    status = Proposal.DRAFT
    valid_until = factory.LazyFunction(lambda: date.today() + timedelta(days=30))
    total_value = Decimal('5000.00')
    currency = 'USD'
    owner = factory.SubFactory(UserFactory)
    metadata = factory.LazyFunction(dict)

    # proposal_number is auto-generated in save(), so we leave it blank


class ProposalSectionFactory(factory.django.DjangoModelFactory):
    """Factory for the ProposalSection model."""

    class Meta:
        model = ProposalSection

    proposal = factory.SubFactory(ProposalFactory)
    title = factory.Sequence(lambda n: f'Section {n}')
    content = factory.Faker('paragraph')
    order = factory.Sequence(lambda n: n)
    section_type = ProposalSection.CUSTOM


class ProposalPricingOptionFactory(factory.django.DjangoModelFactory):
    """Factory for the ProposalPricingOption model."""

    class Meta:
        model = ProposalPricingOption

    proposal = factory.SubFactory(ProposalFactory)
    name = factory.Sequence(lambda n: f'Pricing Tier {n}')
    description = factory.Faker('sentence')
    price = Decimal('2500.00')
    is_recommended = False
    features = factory.LazyFunction(lambda: ['Feature A', 'Feature B'])
    order = factory.Sequence(lambda n: n)


class ProposalActivityFactory(factory.django.DjangoModelFactory):
    """Factory for the ProposalActivity model."""

    class Meta:
        model = ProposalActivity

    proposal = factory.SubFactory(ProposalFactory)
    activity_type = ProposalActivity.CREATED
    description = factory.LazyAttribute(
        lambda obj: f'Proposal "{obj.proposal.title}" was created.'
    )
    user = factory.SubFactory(UserFactory)
    ip_address = '127.0.0.1'
    metadata = factory.LazyFunction(dict)
