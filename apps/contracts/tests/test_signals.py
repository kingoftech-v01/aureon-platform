"""
Tests for contracts app signals.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock
from apps.contracts.models import Contract, ContractMilestone


@pytest.mark.django_db
class TestContractMilestoneSignals:
    """Tests for contract milestone signals."""

    def test_update_completion_on_milestone_update(self, contract_fixed, admin_user):
        """Test that updating a milestone triggers contract completion update."""
        # Create two milestones
        m1 = ContractMilestone.objects.create(
            contract=contract_fixed,
            title='Milestone 1',
            due_date=date.today() + timedelta(days=15),
            amount=Decimal('5000.00'),
            status=ContractMilestone.PENDING,
            order=0,
        )
        m2 = ContractMilestone.objects.create(
            contract=contract_fixed,
            title='Milestone 2',
            due_date=date.today() + timedelta(days=30),
            amount=Decimal('5000.00'),
            status=ContractMilestone.PENDING,
            order=1,
        )

        # Complete first milestone (update, not create)
        m1.status = ContractMilestone.COMPLETED
        m1.save()

        contract_fixed.refresh_from_db()
        assert contract_fixed.completion_percentage == 50

    def test_no_update_on_milestone_creation(self, contract_fixed):
        """Test that creating a milestone does NOT trigger completion update (only updates do)."""
        initial_completion = contract_fixed.completion_percentage

        with patch.object(Contract, 'update_completion_percentage') as mock_update:
            ContractMilestone.objects.create(
                contract=contract_fixed,
                title='New Milestone',
                due_date=date.today() + timedelta(days=15),
                amount=Decimal('1000.00'),
                status=ContractMilestone.PENDING,
                order=5,
            )
            # Should not be called on creation
            mock_update.assert_not_called()

    def test_update_completion_on_milestone_delete(self, contract_fixed, admin_user):
        """Test that deleting a milestone triggers contract completion update."""
        m1 = ContractMilestone.objects.create(
            contract=contract_fixed,
            title='Delete Target',
            due_date=date.today() + timedelta(days=15),
            amount=Decimal('5000.00'),
            status=ContractMilestone.COMPLETED,
            order=0,
        )
        m2 = ContractMilestone.objects.create(
            contract=contract_fixed,
            title='Keep This',
            due_date=date.today() + timedelta(days=30),
            amount=Decimal('5000.00'),
            status=ContractMilestone.PENDING,
            order=1,
        )

        # Before delete: 1/2 completed = 50%
        contract_fixed.update_completion_percentage()
        contract_fixed.refresh_from_db()
        assert contract_fixed.completion_percentage == 50

        # Delete completed milestone - should trigger update
        m1.delete()

        contract_fixed.refresh_from_db()
        # Now only m2 remains (pending), so 0% completion
        assert contract_fixed.completion_percentage == 0

    def test_completion_100_percent_all_done(self, contract_fixed, admin_user):
        """Test completion reaches 100% when all milestones completed."""
        m1 = ContractMilestone.objects.create(
            contract=contract_fixed,
            title='Task A',
            due_date=date.today() + timedelta(days=15),
            amount=Decimal('3000.00'),
            status=ContractMilestone.COMPLETED,
            order=0,
        )
        m2 = ContractMilestone.objects.create(
            contract=contract_fixed,
            title='Task B',
            due_date=date.today() + timedelta(days=30),
            amount=Decimal('3000.00'),
            status=ContractMilestone.PENDING,
            order=1,
        )

        # Complete the second milestone (triggers signal on update)
        m2.status = ContractMilestone.COMPLETED
        m2.save()

        contract_fixed.refresh_from_db()
        assert contract_fixed.completion_percentage == 100
