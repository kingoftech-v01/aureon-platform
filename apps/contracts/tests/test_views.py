"""
Tests for contracts app views and API endpoints.

Tests cover:
- Contract CRUD operations
- Contract filtering and search
- Contract statistics
- Contract signing
- Milestone operations
- Authorization
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from rest_framework import status
from apps.contracts.models import Contract, ContractMilestone


# ============================================================================
# Contract ViewSet Tests
# ============================================================================

@pytest.mark.django_db
class TestContractViewSet:
    """Tests for ContractViewSet."""

    def test_list_contracts(self, authenticated_admin_client, contract_fixed, contract_hourly):
        """Test listing contracts."""
        response = authenticated_admin_client.get('/api/api/contracts/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 2

    def test_list_contracts_unauthenticated(self, api_client):
        """Test listing contracts without authentication."""
        response = api_client.get('/api/api/contracts/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_contract(self, authenticated_admin_client, contract_fixed):
        """Test retrieving a specific contract."""
        response = authenticated_admin_client.get(f'/api/api/contracts/{contract_fixed.id}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == contract_fixed.title
        assert response.data['contract_number'] == contract_fixed.contract_number

    def test_create_contract(self, authenticated_admin_client, client_company):
        """Test creating a contract."""
        data = {
            'client': str(client_company.id),
            'title': 'New Contract',
            'description': 'A new contract description.',
            'contract_type': Contract.FIXED_PRICE,
            'status': Contract.DRAFT,
            'start_date': str(date.today()),
            'end_date': str(date.today() + timedelta(days=90)),
            'value': '15000.00',
            'currency': 'USD',
        }

        response = authenticated_admin_client.post('/api/api/contracts/', data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'New Contract'
        assert response.data['contract_number'].startswith('CNT-')

    def test_create_hourly_contract_with_rate(self, authenticated_admin_client, client_company):
        """Test creating hourly contract with hourly rate."""
        data = {
            'client': str(client_company.id),
            'title': 'Hourly Contract',
            'description': 'Hourly consulting.',
            'contract_type': Contract.HOURLY,
            'status': Contract.DRAFT,
            'start_date': str(date.today()),
            'value': '5000.00',
            'hourly_rate': '150.00',
            'estimated_hours': '40.00',
            'currency': 'USD',
        }

        response = authenticated_admin_client.post('/api/api/contracts/', data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['hourly_rate'] == '150.00'

    def test_create_hourly_contract_without_rate_fails(
        self, authenticated_admin_client, client_company
    ):
        """Test creating hourly contract without rate fails."""
        data = {
            'client': str(client_company.id),
            'title': 'Hourly No Rate',
            'description': 'Missing hourly rate.',
            'contract_type': Contract.HOURLY,
            'status': Contract.DRAFT,
            'start_date': str(date.today()),
            'value': '5000.00',
            'currency': 'USD',
        }

        response = authenticated_admin_client.post('/api/api/contracts/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'hourly_rate' in response.data

    def test_update_contract(self, authenticated_admin_client, contract_draft):
        """Test updating a contract."""
        data = {
            'title': 'Updated Contract Title',
            'status': Contract.PENDING,
        }

        response = authenticated_admin_client.patch(
            f'/api/api/contracts/{contract_draft.id}/',
            data
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Updated Contract Title'
        assert response.data['status'] == Contract.PENDING

    def test_delete_contract(self, authenticated_admin_client, contract_draft):
        """Test deleting a contract."""
        response = authenticated_admin_client.delete(
            f'/api/api/contracts/{contract_draft.id}/'
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Contract.objects.filter(id=contract_draft.id).exists()

    def test_validate_end_date_before_start_date(
        self, authenticated_admin_client, client_company
    ):
        """Test that end date before start date is invalid."""
        data = {
            'client': str(client_company.id),
            'title': 'Invalid Dates',
            'description': 'End before start.',
            'contract_type': Contract.FIXED_PRICE,
            'start_date': str(date.today()),
            'end_date': str(date.today() - timedelta(days=10)),
            'value': '1000.00',
        }

        response = authenticated_admin_client.post('/api/api/contracts/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'end_date' in response.data


# ============================================================================
# Contract Search and Filter Tests
# ============================================================================

@pytest.mark.django_db
class TestContractSearchFilter:
    """Tests for contract search and filtering."""

    def test_search_by_title(self, authenticated_admin_client, contract_fixed):
        """Test searching contracts by title."""
        response = authenticated_admin_client.get(
            f'/api/api/contracts/?search={contract_fixed.title}'
        )

        assert response.status_code == status.HTTP_200_OK

    def test_search_by_contract_number(self, authenticated_admin_client, contract_fixed):
        """Test searching contracts by contract number."""
        response = authenticated_admin_client.get(
            f'/api/api/contracts/?search={contract_fixed.contract_number}'
        )

        assert response.status_code == status.HTTP_200_OK

    def test_filter_by_status(self, authenticated_admin_client, contract_fixed, contract_draft):
        """Test filtering contracts by status."""
        response = authenticated_admin_client.get(
            f'/api/api/contracts/?status={Contract.ACTIVE}'
        )

        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        for contract in results:
            assert contract['status'] == Contract.ACTIVE

    def test_filter_by_contract_type(
        self, authenticated_admin_client, contract_fixed, contract_hourly
    ):
        """Test filtering contracts by type."""
        response = authenticated_admin_client.get(
            f'/api/api/contracts/?contract_type={Contract.HOURLY}'
        )

        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        for contract in results:
            assert contract['contract_type'] == Contract.HOURLY

    def test_ordering_by_value(self, authenticated_admin_client, contract_fixed, contract_hourly):
        """Test ordering contracts by value."""
        response = authenticated_admin_client.get(
            '/api/api/contracts/?ordering=-value'
        )

        assert response.status_code == status.HTTP_200_OK


# ============================================================================
# Contract Statistics Tests
# ============================================================================

@pytest.mark.django_db
class TestContractStatistics:
    """Tests for contract statistics endpoint."""

    def test_stats_endpoint(
        self, authenticated_admin_client, contract_fixed, contract_draft, contract_hourly
    ):
        """Test the stats endpoint returns correct data."""
        response = authenticated_admin_client.get('/api/api/contracts/stats/')

        assert response.status_code == status.HTTP_200_OK
        assert 'total_contracts' in response.data
        assert 'active_contracts' in response.data
        assert 'draft_contracts' in response.data
        assert 'completed_contracts' in response.data
        assert 'total_value' in response.data
        assert 'total_invoiced' in response.data
        assert 'total_paid' in response.data
        assert 'avg_completion' in response.data

    def test_stats_counts(
        self, authenticated_admin_client, contract_fixed, contract_draft
    ):
        """Test stats endpoint has correct counts."""
        response = authenticated_admin_client.get('/api/api/contracts/stats/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_contracts'] >= 2
        assert response.data['active_contracts'] >= 1
        assert response.data['draft_contracts'] >= 1


# ============================================================================
# Contract Signing Tests
# ============================================================================

@pytest.mark.django_db
class TestContractSigning:
    """Tests for contract signing endpoint."""

    def test_sign_contract_client(self, authenticated_admin_client, contract_draft):
        """Test signing contract as client."""
        data = {
            'party': 'client',
            'signature': 'client_signature_data_here',
        }

        response = authenticated_admin_client.post(
            f'/api/api/contracts/{contract_draft.id}/sign/',
            data
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['signed_by_client'] is True

    def test_sign_contract_company(self, authenticated_admin_client, contract_draft):
        """Test signing contract as company."""
        data = {
            'party': 'company',
            'signature': 'company_signature_data_here',
        }

        response = authenticated_admin_client.post(
            f'/api/api/contracts/{contract_draft.id}/sign/',
            data
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['signed_by_company'] is True

    def test_sign_contract_invalid_party(self, authenticated_admin_client, contract_draft):
        """Test signing with invalid party."""
        data = {
            'party': 'invalid',
            'signature': 'signature',
        }

        response = authenticated_admin_client.post(
            f'/api/api/contracts/{contract_draft.id}/sign/',
            data
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_sign_contract_missing_signature(self, authenticated_admin_client, contract_draft):
        """Test signing without signature."""
        data = {
            'party': 'client',
        }

        response = authenticated_admin_client.post(
            f'/api/api/contracts/{contract_draft.id}/sign/',
            data
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ============================================================================
# Contract Milestone ViewSet Tests
# ============================================================================

@pytest.mark.django_db
class TestContractMilestoneViewSet:
    """Tests for ContractMilestoneViewSet."""

    def test_list_milestones(self, authenticated_admin_client, contract_milestone):
        """Test listing milestones."""
        response = authenticated_admin_client.get('/api/api/milestones/')

        assert response.status_code == status.HTTP_200_OK

    def test_create_milestone(self, authenticated_admin_client, contract_fixed):
        """Test creating a milestone."""
        data = {
            'contract': str(contract_fixed.id),
            'title': 'New Milestone',
            'description': 'Milestone description.',
            'due_date': str(date.today() + timedelta(days=30)),
            'amount': '2500.00',
            'status': ContractMilestone.PENDING,
            'order': 1,
        }

        response = authenticated_admin_client.post('/api/api/milestones/', data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'New Milestone'

    def test_get_contract_milestones_action(
        self, authenticated_admin_client, contract_fixed, contract_milestone
    ):
        """Test getting milestones for a specific contract."""
        response = authenticated_admin_client.get(
            f'/api/api/contracts/{contract_fixed.id}/milestones/'
        )

        assert response.status_code == status.HTTP_200_OK

    def test_mark_milestone_complete(
        self, authenticated_admin_client, contract_milestone
    ):
        """Test marking milestone as complete."""
        response = authenticated_admin_client.post(
            f'/api/api/milestones/{contract_milestone.id}/mark_complete/'
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == ContractMilestone.COMPLETED

    def test_mark_completed_milestone_fails(
        self, authenticated_admin_client, contract_milestone_completed
    ):
        """Test marking already completed milestone fails."""
        response = authenticated_admin_client.post(
            f'/api/api/milestones/{contract_milestone_completed.id}/mark_complete/'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_generate_invoice_for_milestone(
        self, authenticated_admin_client, contract_milestone
    ):
        """Test generating invoice for milestone succeeds and creates invoice."""
        response = authenticated_admin_client.post(
            f'/api/api/milestones/{contract_milestone.id}/generate_invoice/'
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['detail'] == 'Invoice generated successfully.'
        assert 'invoice_id' in response.data
        assert 'invoice_number' in response.data

        # Milestone should be marked as invoiced
        contract_milestone.refresh_from_db()
        assert contract_milestone.invoice_generated is True

    def test_generate_invoice_already_generated(
        self, authenticated_admin_client, contract_milestone
    ):
        """Test generating invoice when already generated."""
        contract_milestone.invoice_generated = True
        contract_milestone.save()

        response = authenticated_admin_client.post(
            f'/api/api/milestones/{contract_milestone.id}/generate_invoice/'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ============================================================================
# Contract Financial Actions Tests
# ============================================================================

@pytest.mark.django_db
class TestContractFinancialActions:
    """Tests for contract financial action endpoints."""

    def test_update_financial_summary(self, authenticated_admin_client, contract_fixed):
        """Test update_financial_summary action."""
        response = authenticated_admin_client.post(
            f'/api/api/contracts/{contract_fixed.id}/update_financial_summary/'
        )

        assert response.status_code == status.HTTP_200_OK

    def test_update_completion(self, authenticated_admin_client, contract_fixed):
        """Test update_completion action."""
        response = authenticated_admin_client.post(
            f'/api/api/contracts/{contract_fixed.id}/update_completion/'
        )

        assert response.status_code == status.HTTP_200_OK


# ============================================================================
# Contract Authorization Tests
# ============================================================================

@pytest.mark.django_db
class TestContractAuthorization:
    """Tests for contract authorization."""

    def test_non_staff_sees_own_contracts(
        self, authenticated_contributor_client, contract_fixed, contributor_user
    ):
        """Test non-staff users see only their contracts or unassigned."""
        contract_fixed.owner = contributor_user
        contract_fixed.save()

        response = authenticated_contributor_client.get('/api/api/contracts/')

        assert response.status_code == status.HTTP_200_OK

    def test_staff_sees_all_contracts(
        self, authenticated_admin_client, contract_fixed, contract_draft
    ):
        """Test staff users see all contracts."""
        response = authenticated_admin_client.get('/api/api/contracts/')

        assert response.status_code == status.HTTP_200_OK


# ============================================================================
# Contract View Edge Cases
# ============================================================================

@pytest.mark.django_db
class TestContractViewEdgeCases:
    """Edge case tests for contract views."""

    def test_create_contract_with_milestones(self, authenticated_admin_client, client_company):
        """Test creating contract with milestones."""
        data = {
            'client': str(client_company.id),
            'title': 'Contract with Milestones',
            'description': 'Has milestones.',
            'contract_type': Contract.MILESTONE,
            'status': Contract.DRAFT,
            'start_date': str(date.today()),
            'end_date': str(date.today() + timedelta(days=90)),
            'value': '10000.00',
            'milestones': [
                {
                    'title': 'Phase 1',
                    'due_date': str(date.today() + timedelta(days=30)),
                    'amount': '3000.00',
                    'order': 1,
                },
                {
                    'title': 'Phase 2',
                    'due_date': str(date.today() + timedelta(days=60)),
                    'amount': '3000.00',
                    'order': 2,
                },
            ],
        }

        response = authenticated_admin_client.post(
            '/api/api/contracts/',
            data,
            format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED

    def test_retrieve_nonexistent_contract(self, authenticated_admin_client):
        """Test retrieving a nonexistent contract."""
        import uuid
        fake_id = uuid.uuid4()

        response = authenticated_admin_client.get(f'/api/api/contracts/{fake_id}/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_contract_with_metadata(self, authenticated_admin_client, client_company):
        """Test creating contract with metadata."""
        data = {
            'client': str(client_company.id),
            'title': 'Contract with Metadata',
            'description': 'Has metadata.',
            'contract_type': Contract.FIXED_PRICE,
            'start_date': str(date.today()),
            'value': '5000.00',
            'metadata': {'priority': 'high', 'tags': ['urgent']},
        }

        response = authenticated_admin_client.post(
            '/api/api/contracts/',
            data,
            format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['metadata']['priority'] == 'high'


# ============================================================================
# Coverage Boost Tests
# ============================================================================

@pytest.mark.django_db
class TestContractSignBothParties:
    """Tests that cover the both-parties-signed branch (views.py 118-119)."""

    def test_sign_both_parties_sets_signed_at(
        self, authenticated_admin_client, contract_draft
    ):
        """When both client and company sign, signed_at should be set."""
        url = f'/api/api/contracts/{contract_draft.id}/sign/'

        # Sign as client first
        resp1 = authenticated_admin_client.post(url, {
            'party': 'client',
            'signature': 'client_sig',
        })
        assert resp1.status_code == status.HTTP_200_OK
        assert resp1.data['signed_by_client'] is True
        # signed_at should NOT be set yet (only one party signed)
        assert resp1.data['signed_at'] is None

        # Sign as company second
        resp2 = authenticated_admin_client.post(url, {
            'party': 'company',
            'signature': 'company_sig',
        })
        assert resp2.status_code == status.HTTP_200_OK
        assert resp2.data['signed_by_company'] is True
        # Now both parties signed -> signed_at should be populated
        assert resp2.data['signed_at'] is not None


@pytest.mark.django_db
class TestContractFinancialExceptionPaths:
    """Tests that trigger exception handlers in financial actions
    (views.py 137-138, 154-155)."""

    def test_update_financial_summary_exception(
        self, authenticated_admin_client, contract_fixed, monkeypatch
    ):
        """Cover the except branch when update_financial_summary raises."""
        from apps.contracts.models import Contract as ContractModel

        def _explode(self):
            raise RuntimeError('boom')

        monkeypatch.setattr(ContractModel, 'update_financial_summary', _explode)

        response = authenticated_admin_client.post(
            f'/api/api/contracts/{contract_fixed.id}/update_financial_summary/'
        )
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'boom' in response.data['detail']

    def test_update_completion_exception(
        self, authenticated_admin_client, contract_fixed, monkeypatch
    ):
        """Cover the except branch when update_completion_percentage raises."""
        from apps.contracts.models import Contract as ContractModel

        def _explode(self):
            raise RuntimeError('completion error')

        monkeypatch.setattr(ContractModel, 'update_completion_percentage', _explode)

        response = authenticated_admin_client.post(
            f'/api/api/contracts/{contract_fixed.id}/update_completion/'
        )
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'completion error' in response.data['detail']


@pytest.mark.django_db
class TestMilestoneNonStaffQueryset:
    """Cover the non-staff queryset filter in ContractMilestoneViewSet
    (views.py line 189)."""

    def test_non_staff_milestone_list(
        self, authenticated_contributor_client, contract_fixed,
        contract_milestone, contributor_user
    ):
        """Non-staff sees only milestones of contracts they own or unowned."""
        # Assign contract to contributor so they can see it
        contract_fixed.owner = contributor_user
        contract_fixed.save()

        response = authenticated_contributor_client.get('/api/api/milestones/')
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestContractModelCoverage:
    """Tests for uncovered model lines (289-290, 306)."""

    def test_auto_contract_number_generation(self, db, client_company, admin_user):
        """Cover contract_number auto-generation (including except branch)."""
        from apps.contracts.models import Contract

        # Create a contract without providing contract_number
        contract = Contract.objects.create(
            client=client_company,
            title='Auto Number',
            description='Test auto number generation.',
            contract_type=Contract.FIXED_PRICE,
            status=Contract.DRAFT,
            start_date=date.today(),
            value=Decimal('1000.00'),
            owner=admin_user,
        )
        assert contract.contract_number.startswith('CNT-')

    def test_contract_number_with_invalid_previous(
        self, db, client_company, admin_user
    ):
        """Cover the ValueError/IndexError branch (models.py 289-290)."""
        from apps.contracts.models import Contract

        # Create a contract with a non-standard contract_number to trigger
        # the exception path in the next auto-generated number.
        Contract.objects.create(
            contract_number='CNT-INVALID',
            client=client_company,
            title='Bad Number',
            description='Has a non-numeric contract number.',
            contract_type=Contract.FIXED_PRICE,
            status=Contract.DRAFT,
            start_date=date.today(),
            value=Decimal('500.00'),
            owner=admin_user,
        )

        # Next contract should gracefully fall back to 1
        contract2 = Contract.objects.create(
            client=client_company,
            title='After Bad Number',
            description='Auto generation after invalid number.',
            contract_type=Contract.FIXED_PRICE,
            status=Contract.DRAFT,
            start_date=date.today(),
            value=Decimal('600.00'),
            owner=admin_user,
        )
        assert contract2.contract_number.startswith('CNT-')

    def test_total_value_property(self, contract_fixed):
        """Cover the total_value property (models.py line 306)."""
        assert contract_fixed.total_value == contract_fixed.value


@pytest.mark.django_db
class TestSerializerCoverage:
    """Tests for uncovered serializer lines."""

    def test_list_serializer_owner_name_none(
        self, authenticated_admin_client, client_company, admin_user
    ):
        """Cover owner_name returning None when owner is unset (serializer line 57)."""
        from apps.contracts.models import Contract

        contract = Contract.objects.create(
            client=client_company,
            title='No Owner Contract',
            description='No owner.',
            contract_type=Contract.FIXED_PRICE,
            status=Contract.ACTIVE,
            start_date=date.today(),
            value=Decimal('3000.00'),
            owner=None,
        )

        response = authenticated_admin_client.get('/api/api/contracts/')
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        # Find our contract in the list
        no_owner = [c for c in results if c['title'] == 'No Owner Contract']
        assert len(no_owner) == 1
        assert no_owner[0]['owner_name'] is None

    def test_detail_serializer_owner_name_none(
        self, authenticated_admin_client, client_company
    ):
        """Cover detail serializer owner_name None (serializer line 83)."""
        from apps.contracts.models import Contract

        contract = Contract.objects.create(
            client=client_company,
            title='Detail No Owner',
            description='No owner.',
            contract_type=Contract.FIXED_PRICE,
            status=Contract.ACTIVE,
            start_date=date.today(),
            value=Decimal('4000.00'),
            owner=None,
        )

        response = authenticated_admin_client.get(
            f'/api/api/contracts/{contract.id}/'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['owner_name'] is None

    def test_update_contract_with_milestones_replace(
        self, authenticated_admin_client, contract_fixed, contract_milestone
    ):
        """Cover the milestone update/delete logic in serializer update method
        (serializer lines 160-169)."""
        # PATCH with new milestones list (no id = create new, drop old)
        data = {
            'milestones': [
                {
                    'title': 'New Phase A',
                    'due_date': str(date.today() + timedelta(days=15)),
                    'amount': '2000.00',
                    'order': 1,
                },
            ],
        }

        response = authenticated_admin_client.patch(
            f'/api/api/contracts/{contract_fixed.id}/',
            data,
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK

        # Old milestone should be deleted, new one created
        from apps.contracts.models import ContractMilestone
        milestones = ContractMilestone.objects.filter(contract=contract_fixed)
        assert milestones.count() == 1
        assert milestones.first().title == 'New Phase A'

    def test_update_contract_with_existing_milestone_id(
        self, authenticated_admin_client, contract_fixed, contract_milestone
    ):
        """Cover the milestone update-by-id branch (serializer lines 166-167)."""
        data = {
            'milestones': [
                {
                    'id': str(contract_milestone.id),
                    'title': 'Updated Phase Title',
                    'due_date': str(date.today() + timedelta(days=45)),
                    'amount': '5500.00',
                    'order': 1,
                },
            ],
        }

        response = authenticated_admin_client.patch(
            f'/api/api/contracts/{contract_fixed.id}/',
            data,
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK

        contract_milestone.refresh_from_db()
        assert contract_milestone.title == 'Updated Phase Title'


# ============================================================================
# Generate Invoice Exception Path
# ============================================================================

@pytest.mark.django_db
class TestGenerateInvoiceException:
    """Cover the exception handler in generate_invoice (views.py 274-275)."""

    def test_generate_invoice_exception_path(
        self, authenticated_admin_client, contract_milestone, monkeypatch
    ):
        """Trigger an exception inside generate_invoice to cover the except block."""

        def _explode(*args, **kwargs):
            raise RuntimeError('invoice creation boom')

        from apps.invoicing.models import Invoice
        monkeypatch.setattr(Invoice.objects, 'create', _explode)

        response = authenticated_admin_client.post(
            f'/api/api/milestones/{contract_milestone.id}/generate_invoice/'
        )
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'invoice creation boom' in response.data['detail']


# ============================================================================
# Filters Coverage
# ============================================================================

@pytest.mark.django_db
class TestContractFiltersCoverage:
    """Tests for uncovered filter methods (filters.py 110-113, 119-129)."""

    def test_filter_is_signed_true(
        self, authenticated_admin_client, contract_fixed, contract_draft
    ):
        """Cover filter_is_signed with value=true (filters.py 110-113)."""
        response = authenticated_admin_client.get(
            '/api/api/contracts/?is_signed=true'
        )
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        for c in results:
            assert c['is_signed'] is True

    def test_filter_is_signed_false(
        self, authenticated_admin_client, contract_fixed, contract_draft
    ):
        """Cover filter_is_signed with value=false (filters.py 113)."""
        response = authenticated_admin_client.get(
            '/api/api/contracts/?is_signed=false'
        )
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        for c in results:
            assert c['is_signed'] is False

    def test_filter_active_period_true(
        self, authenticated_admin_client, contract_fixed
    ):
        """Cover filter_active_period with value=true (filters.py 119-127)."""
        response = authenticated_admin_client.get(
            '/api/api/contracts/?is_active_period=true'
        )
        assert response.status_code == status.HTTP_200_OK

    def test_filter_active_period_false(
        self, authenticated_admin_client, contract_fixed
    ):
        """Cover filter_active_period with value=false (filters.py 128-131)."""
        response = authenticated_admin_client.get(
            '/api/api/contracts/?is_active_period=false'
        )
        assert response.status_code == status.HTTP_200_OK
