"""
Tests for contracts app URL configuration.
"""

import pytest
import uuid
from django.urls import reverse, resolve
from apps.contracts.views import ContractViewSet, ContractMilestoneViewSet


class TestContractURLs:
    """Tests for contract URL resolution."""

    def test_contract_list_url_resolves(self):
        """Test contract-list URL resolves to ContractViewSet."""
        url = reverse('contracts:contract-list')
        assert '/api/contracts/' in url
        resolver = resolve(url)
        assert resolver.func.cls == ContractViewSet

    def test_contract_detail_url_resolves(self):
        """Test contract-detail URL resolves correctly."""
        pk = uuid.uuid4()
        url = reverse('contracts:contract-detail', kwargs={'pk': pk})
        assert f'/api/contracts/{pk}/' in url
        resolver = resolve(url)
        assert resolver.func.cls == ContractViewSet

    def test_contract_stats_url_resolves(self):
        """Test contract stats action URL resolves."""
        url = reverse('contracts:contract-stats')
        assert '/api/contracts/stats/' in url

    def test_contract_sign_url_resolves(self):
        """Test contract sign action URL resolves."""
        pk = uuid.uuid4()
        url = reverse('contracts:contract-sign', kwargs={'pk': pk})
        assert f'/api/contracts/{pk}/sign/' in url

    def test_contract_update_financial_summary_url_resolves(self):
        """Test update_financial_summary action URL resolves."""
        pk = uuid.uuid4()
        url = reverse('contracts:contract-update-financial-summary', kwargs={'pk': pk})
        assert f'/api/contracts/{pk}/update_financial_summary/' in url

    def test_contract_update_completion_url_resolves(self):
        """Test update_completion action URL resolves."""
        pk = uuid.uuid4()
        url = reverse('contracts:contract-update-completion', kwargs={'pk': pk})
        assert f'/api/contracts/{pk}/update_completion/' in url

    def test_contract_milestones_url_resolves(self):
        """Test milestones action URL resolves."""
        pk = uuid.uuid4()
        url = reverse('contracts:contract-milestones', kwargs={'pk': pk})
        assert f'/api/contracts/{pk}/milestones/' in url

    def test_milestone_list_url_resolves(self):
        """Test contract-milestone-list URL resolves to ContractMilestoneViewSet."""
        url = reverse('contracts:contract-milestone-list')
        assert '/api/milestones/' in url
        resolver = resolve(url)
        assert resolver.func.cls == ContractMilestoneViewSet

    def test_milestone_detail_url_resolves(self):
        """Test contract-milestone-detail URL resolves correctly."""
        pk = uuid.uuid4()
        url = reverse('contracts:contract-milestone-detail', kwargs={'pk': pk})
        assert f'/api/milestones/{pk}/' in url
        resolver = resolve(url)
        assert resolver.func.cls == ContractMilestoneViewSet

    def test_milestone_mark_complete_url_resolves(self):
        """Test milestone mark_complete action URL resolves."""
        pk = uuid.uuid4()
        url = reverse('contracts:contract-milestone-mark-complete', kwargs={'pk': pk})
        assert f'/api/milestones/{pk}/mark_complete/' in url

    def test_milestone_generate_invoice_url_resolves(self):
        """Test milestone generate_invoice action URL resolves."""
        pk = uuid.uuid4()
        url = reverse('contracts:contract-milestone-generate-invoice', kwargs={'pk': pk})
        assert f'/api/milestones/{pk}/generate_invoice/' in url

    def test_app_name(self):
        """Test the app_name is set to 'contracts'."""
        from apps.contracts import urls
        assert urls.app_name == 'contracts'
