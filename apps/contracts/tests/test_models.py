"""
Tests for contracts app models.

Tests cover:
- Contract model creation and validation
- Contract properties and methods
- ContractMilestone model
- Auto-generation of contract numbers
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone
from apps.contracts.models import Contract, ContractMilestone


# ============================================================================
# Contract Model Tests
# ============================================================================

@pytest.mark.django_db
class TestContractModel:
    """Tests for the Contract model."""

    def test_create_fixed_price_contract(self, client_company, admin_user):
        """Test creating a fixed-price contract."""
        contract = Contract.objects.create(
            client=client_company,
            title='Fixed Price Project',
            description='A fixed price contract for web development.',
            contract_type=Contract.FIXED_PRICE,
            status=Contract.DRAFT,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=90),
            value=Decimal('10000.00'),
            currency='USD',
            owner=admin_user,
        )

        assert contract.contract_type == Contract.FIXED_PRICE
        assert contract.value == Decimal('10000.00')
        assert contract.status == Contract.DRAFT

    def test_create_hourly_contract(self, client_company, admin_user):
        """Test creating an hourly contract."""
        contract = Contract.objects.create(
            client=client_company,
            title='Hourly Consulting',
            description='Hourly consulting services.',
            contract_type=Contract.HOURLY,
            status=Contract.ACTIVE,
            start_date=date.today(),
            value=Decimal('5000.00'),
            hourly_rate=Decimal('150.00'),
            estimated_hours=Decimal('40.00'),
            currency='USD',
            owner=admin_user,
        )

        assert contract.contract_type == Contract.HOURLY
        assert contract.hourly_rate == Decimal('150.00')

    def test_contract_auto_generate_number(self, client_company, admin_user):
        """Test that contract number is auto-generated."""
        contract = Contract.objects.create(
            client=client_company,
            title='Auto Number Test',
            description='Testing auto number generation.',
            contract_type=Contract.FIXED_PRICE,
            status=Contract.DRAFT,
            start_date=date.today(),
            value=Decimal('1000.00'),
            owner=admin_user,
        )

        assert contract.contract_number is not None
        assert contract.contract_number.startswith('CNT-')

    def test_contract_string_representation(self, contract_fixed):
        """Test contract string representation."""
        expected = f"{contract_fixed.contract_number} - {contract_fixed.title}"
        assert str(contract_fixed) == expected

    def test_contract_uuid_primary_key(self, contract_fixed):
        """Test contract has UUID primary key."""
        import uuid
        assert isinstance(contract_fixed.id, uuid.UUID)


# ============================================================================
# Contract Status Tests
# ============================================================================

@pytest.mark.django_db
class TestContractStatus:
    """Tests for contract status values."""

    def test_all_status_choices_valid(self):
        """Test all status choices are valid."""
        valid_statuses = [
            Contract.DRAFT,
            Contract.PENDING,
            Contract.ACTIVE,
            Contract.COMPLETED,
            Contract.CANCELLED,
            Contract.ON_HOLD,
        ]
        for status in valid_statuses:
            assert status in dict(Contract.STATUS_CHOICES)

    def test_contract_type_choices(self):
        """Test all contract type choices are valid."""
        valid_types = [
            Contract.FIXED_PRICE,
            Contract.HOURLY,
            Contract.RETAINER,
            Contract.MILESTONE,
        ]
        for contract_type in valid_types:
            assert contract_type in dict(Contract.TYPE_CHOICES)


# ============================================================================
# Contract Signature Tests
# ============================================================================

@pytest.mark.django_db
class TestContractSignature:
    """Tests for contract signature functionality."""

    def test_is_signed_both_parties(self, contract_fixed):
        """Test is_signed when both parties have signed."""
        assert contract_fixed.signed_by_client is True
        assert contract_fixed.signed_by_company is True
        assert contract_fixed.is_signed is True

    def test_is_signed_partial(self, contract_draft):
        """Test is_signed when only one party has signed."""
        contract_draft.signed_by_client = True
        contract_draft.signed_by_company = False
        contract_draft.save()

        assert contract_draft.is_signed is False

    def test_is_signed_neither_party(self, contract_draft):
        """Test is_signed when neither party has signed."""
        assert contract_draft.signed_by_client is False
        assert contract_draft.signed_by_company is False
        assert contract_draft.is_signed is False

    def test_signed_at_timestamp(self, contract_fixed):
        """Test signed_at timestamp is set."""
        assert contract_fixed.signed_at is not None


# ============================================================================
# Contract Date Period Tests
# ============================================================================

@pytest.mark.django_db
class TestContractDatePeriod:
    """Tests for contract date period functionality."""

    def test_is_active_period_current(self, contract_fixed):
        """Test is_active_period for current contract."""
        assert contract_fixed.is_active_period is True

    def test_is_active_period_future(self, contract_draft):
        """Test is_active_period for future contract."""
        contract_draft.start_date = date.today() + timedelta(days=7)
        contract_draft.save()

        assert contract_draft.is_active_period is False

    def test_is_active_period_past(self, contract_fixed):
        """Test is_active_period for past contract."""
        contract_fixed.start_date = date.today() - timedelta(days=100)
        contract_fixed.end_date = date.today() - timedelta(days=10)
        contract_fixed.save()

        assert contract_fixed.is_active_period is False

    def test_is_active_period_no_end_date(self, contract_hourly):
        """Test is_active_period with no end date (ongoing)."""
        contract_hourly.end_date = None
        contract_hourly.save()

        assert contract_hourly.is_active_period is True


# ============================================================================
# Contract Financial Tests
# ============================================================================

@pytest.mark.django_db
class TestContractFinancial:
    """Tests for contract financial properties."""

    def test_outstanding_amount(self, contract_fixed):
        """Test outstanding_amount calculation."""
        contract_fixed.invoiced_amount = Decimal('5000.00')
        contract_fixed.paid_amount = Decimal('3000.00')
        contract_fixed.save()

        assert contract_fixed.outstanding_amount == Decimal('2000.00')

    def test_outstanding_amount_fully_paid(self, contract_fixed):
        """Test outstanding_amount when fully paid."""
        contract_fixed.invoiced_amount = Decimal('5000.00')
        contract_fixed.paid_amount = Decimal('5000.00')
        contract_fixed.save()

        assert contract_fixed.outstanding_amount == Decimal('0.00')

    def test_financial_summary_defaults(self, contract_draft):
        """Test financial summary defaults."""
        assert contract_draft.invoiced_amount == Decimal('0')
        assert contract_draft.paid_amount == Decimal('0')
        assert contract_draft.completion_percentage == 0


# ============================================================================
# Contract Milestone Model Tests
# ============================================================================

@pytest.mark.django_db
class TestContractMilestoneModel:
    """Tests for the ContractMilestone model."""

    def test_create_milestone(self, contract_fixed):
        """Test creating a contract milestone."""
        milestone = ContractMilestone.objects.create(
            contract=contract_fixed,
            title='Phase 1',
            description='Complete the first phase.',
            due_date=date.today() + timedelta(days=30),
            amount=Decimal('3000.00'),
            status=ContractMilestone.PENDING,
            order=1,
        )

        assert milestone.title == 'Phase 1'
        assert milestone.amount == Decimal('3000.00')
        assert milestone.contract == contract_fixed

    def test_milestone_string_representation(self, contract_milestone):
        """Test milestone string representation."""
        expected = f"{contract_milestone.contract.contract_number} - {contract_milestone.title}"
        assert str(contract_milestone) == expected

    def test_milestone_status_choices(self):
        """Test all milestone status choices are valid."""
        valid_statuses = [
            ContractMilestone.PENDING,
            ContractMilestone.IN_PROGRESS,
            ContractMilestone.COMPLETED,
            ContractMilestone.CANCELLED,
        ]
        for status in valid_statuses:
            assert status in dict(ContractMilestone.STATUS_CHOICES)

    def test_milestone_uuid_primary_key(self, contract_milestone):
        """Test milestone has UUID primary key."""
        import uuid
        assert isinstance(contract_milestone.id, uuid.UUID)


# ============================================================================
# Milestone Overdue Tests
# ============================================================================

@pytest.mark.django_db
class TestMilestoneOverdue:
    """Tests for milestone overdue functionality."""

    def test_is_overdue_past_due_date(self, contract_fixed):
        """Test is_overdue for past due date."""
        milestone = ContractMilestone.objects.create(
            contract=contract_fixed,
            title='Overdue Milestone',
            description='This is overdue.',
            due_date=date.today() - timedelta(days=5),
            amount=Decimal('1000.00'),
            status=ContractMilestone.PENDING,
        )

        assert milestone.is_overdue is True

    def test_is_overdue_future_due_date(self, contract_milestone):
        """Test is_overdue for future due date."""
        assert contract_milestone.is_overdue is False

    def test_is_overdue_completed_milestone(self, contract_fixed):
        """Test is_overdue for completed milestone."""
        milestone = ContractMilestone.objects.create(
            contract=contract_fixed,
            title='Completed Milestone',
            description='This is completed.',
            due_date=date.today() - timedelta(days=5),
            amount=Decimal('1000.00'),
            status=ContractMilestone.COMPLETED,
        )

        assert milestone.is_overdue is False

    def test_is_overdue_cancelled_milestone(self, contract_fixed):
        """Test is_overdue for cancelled milestone."""
        milestone = ContractMilestone.objects.create(
            contract=contract_fixed,
            title='Cancelled Milestone',
            description='This is cancelled.',
            due_date=date.today() - timedelta(days=5),
            amount=Decimal('1000.00'),
            status=ContractMilestone.CANCELLED,
        )

        assert milestone.is_overdue is False


# ============================================================================
# Milestone Completion Tests
# ============================================================================

@pytest.mark.django_db
class TestMilestoneCompletion:
    """Tests for milestone completion functionality."""

    def test_completed_milestone_fields(self, contract_milestone_completed, admin_user):
        """Test completed milestone has proper fields set."""
        assert contract_milestone_completed.status == ContractMilestone.COMPLETED
        assert contract_milestone_completed.completed_at is not None
        assert contract_milestone_completed.completed_by == admin_user

    def test_invoice_generated_flag(self, contract_milestone):
        """Test invoice_generated flag default."""
        assert contract_milestone.invoice_generated is False

    def test_milestone_deliverables(self, contract_milestone):
        """Test milestone deliverables JSON field."""
        assert isinstance(contract_milestone.deliverables, list)
        assert 'Wireframes' in contract_milestone.deliverables


# ============================================================================
# Contract Completion Percentage Tests
# ============================================================================

@pytest.mark.django_db
class TestContractCompletionPercentage:
    """Tests for contract completion percentage calculation."""

    def test_update_completion_percentage(
        self, contract_fixed, contract_milestone, contract_milestone_completed
    ):
        """Test updating completion percentage from milestones."""
        contract_fixed.update_completion_percentage()

        # 1 completed out of 2 = 50%
        assert contract_fixed.completion_percentage == 50

    def test_completion_percentage_all_completed(self, contract_fixed, admin_user):
        """Test completion percentage when all milestones are completed."""
        # Create all completed milestones
        for i in range(3):
            ContractMilestone.objects.create(
                contract=contract_fixed,
                title=f'Milestone {i}',
                due_date=date.today(),
                amount=Decimal('1000.00'),
                status=ContractMilestone.COMPLETED,
            )

        contract_fixed.update_completion_percentage()

        assert contract_fixed.completion_percentage == 100

    def test_completion_percentage_no_milestones(self, contract_draft):
        """Test completion percentage with no milestones."""
        contract_draft.update_completion_percentage()

        # Should remain unchanged
        assert contract_draft.completion_percentage == 0


# ============================================================================
# Contract Metadata Tests
# ============================================================================

@pytest.mark.django_db
class TestContractMetadata:
    """Tests for contract metadata JSON field."""

    def test_metadata_default_empty_dict(self, contract_draft):
        """Test metadata defaults to empty dict."""
        assert contract_draft.metadata == {}

    def test_metadata_stores_json(self, contract_fixed):
        """Test metadata can store JSON data."""
        contract_fixed.metadata = {
            'project_manager': 'John Doe',
            'priority': 'high',
            'tags': ['urgent', 'client-facing'],
        }
        contract_fixed.save()

        contract_fixed.refresh_from_db()
        assert contract_fixed.metadata['project_manager'] == 'John Doe'
        assert 'urgent' in contract_fixed.metadata['tags']


# ============================================================================
# Contract Edge Cases
# ============================================================================

@pytest.mark.django_db
class TestContractEdgeCases:
    """Edge case tests for Contract model."""

    def test_contract_without_end_date(self, client_company, admin_user):
        """Test contract without end date (ongoing)."""
        contract = Contract.objects.create(
            client=client_company,
            title='Ongoing Contract',
            description='No end date.',
            contract_type=Contract.RETAINER,
            status=Contract.ACTIVE,
            start_date=date.today(),
            end_date=None,
            value=Decimal('2000.00'),
            owner=admin_user,
        )

        assert contract.end_date is None
        assert contract.is_active_period is True

    def test_contract_with_docusign_envelope(self, contract_fixed):
        """Test contract with DocuSign envelope ID."""
        contract_fixed.docusign_envelope_id = 'env-12345-abcde'
        contract_fixed.save()

        contract_fixed.refresh_from_db()
        assert contract_fixed.docusign_envelope_id == 'env-12345-abcde'

    def test_contract_notes(self, contract_fixed):
        """Test contract notes field."""
        contract_fixed.notes = 'Important notes about this contract.'
        contract_fixed.save()

        contract_fixed.refresh_from_db()
        assert 'Important notes' in contract_fixed.notes

    def test_contract_terms_and_conditions(self, contract_fixed):
        """Test contract terms and conditions field."""
        contract_fixed.terms_and_conditions = 'Full T&C text here...'
        contract_fixed.save()

        contract_fixed.refresh_from_db()
        assert contract_fixed.terms_and_conditions == 'Full T&C text here...'

    def test_contract_payment_terms(self, contract_fixed):
        """Test contract payment terms field."""
        assert contract_fixed.payment_terms is not None

    def test_contract_invoice_schedule(self, contract_fixed):
        """Test contract invoice schedule field."""
        assert contract_fixed.invoice_schedule is not None

    def test_milestone_order(self, contract_fixed):
        """Test milestone ordering."""
        m1 = ContractMilestone.objects.create(
            contract=contract_fixed,
            title='First',
            due_date=date.today(),
            amount=Decimal('1000.00'),
            order=1,
        )
        m2 = ContractMilestone.objects.create(
            contract=contract_fixed,
            title='Second',
            due_date=date.today(),
            amount=Decimal('1000.00'),
            order=2,
        )

        milestones = list(contract_fixed.milestones.all())
        # Should be ordered by order field
        orders = [m.order for m in milestones]
        assert orders == sorted(orders)
