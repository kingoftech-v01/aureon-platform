"""
Tests for invoicing app views and API endpoints.

Tests cover:
- Invoice CRUD operations
- Invoice filtering and search
- Invoice statistics
- Invoice actions (send, mark paid, generate PDF)
- Invoice items
- Authorization
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from rest_framework import status
from apps.invoicing.models import Invoice, InvoiceItem


# ============================================================================
# Invoice ViewSet Tests
# ============================================================================

@pytest.mark.django_db
class TestInvoiceViewSet:
    """Tests for InvoiceViewSet."""

    def test_list_invoices(self, authenticated_admin_client, invoice_draft, invoice_sent):
        """Test listing invoices."""
        response = authenticated_admin_client.get('/api/api/invoices/')

        assert response.status_code == status.HTTP_200_OK

    def test_list_invoices_unauthenticated(self, api_client):
        """Test listing invoices without authentication."""
        response = api_client.get('/api/api/invoices/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_invoice(self, authenticated_admin_client, invoice_draft):
        """Test retrieving a specific invoice."""
        response = authenticated_admin_client.get(f'/api/api/invoices/{invoice_draft.id}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['invoice_number'] == invoice_draft.invoice_number

    def test_create_invoice(self, authenticated_admin_client, client_company):
        """Test creating an invoice."""
        data = {
            'client': str(client_company.id),
            'status': Invoice.DRAFT,
            'issue_date': str(date.today()),
            'due_date': str(date.today() + timedelta(days=30)),
            'tax_rate': '8.00',
            'currency': 'USD',
            'notes': 'Thank you for your business!',
        }

        response = authenticated_admin_client.post('/api/api/invoices/', data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['invoice_number'].startswith('INV-')

    def test_create_invoice_with_items(self, authenticated_admin_client, client_company):
        """Test creating invoice with items."""
        data = {
            'client': str(client_company.id),
            'status': Invoice.DRAFT,
            'issue_date': str(date.today()),
            'due_date': str(date.today() + timedelta(days=30)),
            'tax_rate': '8.00',
            'items': [
                {
                    'description': 'Web Development',
                    'quantity': '40.00',
                    'unit_price': '150.00',
                },
                {
                    'description': 'Design Services',
                    'quantity': '10.00',
                    'unit_price': '100.00',
                },
            ],
        }

        response = authenticated_admin_client.post(
            '/api/api/invoices/',
            data,
            format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED

    def test_update_invoice(self, authenticated_admin_client, invoice_draft):
        """Test updating an invoice."""
        data = {
            'notes': 'Updated notes here.',
            'tax_rate': '10.00',
        }

        response = authenticated_admin_client.patch(
            f'/api/api/invoices/{invoice_draft.id}/',
            data
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['notes'] == 'Updated notes here.'

    def test_delete_invoice(self, authenticated_admin_client, invoice_draft):
        """Test deleting an invoice."""
        response = authenticated_admin_client.delete(
            f'/api/api/invoices/{invoice_draft.id}/'
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Invoice.objects.filter(id=invoice_draft.id).exists()

    def test_validate_due_date_before_issue_date(
        self, authenticated_admin_client, client_company
    ):
        """Test that due date before issue date is invalid."""
        data = {
            'client': str(client_company.id),
            'issue_date': str(date.today()),
            'due_date': str(date.today() - timedelta(days=10)),
        }

        response = authenticated_admin_client.post('/api/api/invoices/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'due_date' in response.data


# ============================================================================
# Invoice Search and Filter Tests
# ============================================================================

@pytest.mark.django_db
class TestInvoiceSearchFilter:
    """Tests for invoice search and filtering."""

    def test_search_by_invoice_number(self, authenticated_admin_client, invoice_draft):
        """Test searching invoices by invoice number."""
        response = authenticated_admin_client.get(
            f'/api/api/invoices/?search={invoice_draft.invoice_number}'
        )

        assert response.status_code == status.HTTP_200_OK

    def test_filter_by_status(
        self, authenticated_admin_client, invoice_draft, invoice_paid
    ):
        """Test filtering invoices by status."""
        response = authenticated_admin_client.get(
            f'/api/api/invoices/?status={Invoice.DRAFT}'
        )

        assert response.status_code == status.HTTP_200_OK
        for invoice in response.data:
            assert invoice['status'] == Invoice.DRAFT

    def test_ordering_by_total(self, authenticated_admin_client, invoice_draft, invoice_paid):
        """Test ordering invoices by total."""
        response = authenticated_admin_client.get(
            '/api/api/invoices/?ordering=-total'
        )

        assert response.status_code == status.HTTP_200_OK

    def test_ordering_by_due_date(self, authenticated_admin_client, invoice_draft, invoice_sent):
        """Test ordering invoices by due date."""
        response = authenticated_admin_client.get(
            '/api/api/invoices/?ordering=due_date'
        )

        assert response.status_code == status.HTTP_200_OK


# ============================================================================
# Invoice Statistics Tests
# ============================================================================

@pytest.mark.django_db
class TestInvoiceStatistics:
    """Tests for invoice statistics endpoint."""

    def test_stats_endpoint(
        self, authenticated_admin_client, invoice_draft, invoice_sent, invoice_paid
    ):
        """Test the stats endpoint returns correct data."""
        response = authenticated_admin_client.get('/api/api/invoices/stats/')

        assert response.status_code == status.HTTP_200_OK
        assert 'total_invoices' in response.data
        assert 'draft_invoices' in response.data
        assert 'sent_invoices' in response.data
        assert 'paid_invoices' in response.data
        assert 'overdue_invoices' in response.data
        assert 'total_invoiced' in response.data
        assert 'total_paid' in response.data
        assert 'total_outstanding' in response.data


# ============================================================================
# Invoice Action Tests
# ============================================================================

@pytest.mark.django_db
class TestInvoiceActions:
    """Tests for invoice action endpoints."""

    def test_send_invoice(self, authenticated_admin_client, invoice_draft):
        """Test sending an invoice."""
        response = authenticated_admin_client.post(
            f'/api/api/invoices/{invoice_draft.id}/send/'
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == Invoice.SENT

    def test_send_non_draft_invoice_fails(self, authenticated_admin_client, invoice_sent):
        """Test sending non-draft invoice fails."""
        response = authenticated_admin_client.post(
            f'/api/api/invoices/{invoice_sent.id}/send/'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_mark_invoice_paid(self, authenticated_admin_client, invoice_sent):
        """Test marking invoice as paid."""
        data = {
            'payment_amount': str(invoice_sent.total),
            'payment_method': 'card',
            'payment_reference': 'txn_test123',
        }

        response = authenticated_admin_client.post(
            f'/api/api/invoices/{invoice_sent.id}/mark_paid/',
            data
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == Invoice.PAID

    def test_mark_invoice_partially_paid(self, authenticated_admin_client, invoice_sent):
        """Test marking invoice as partially paid."""
        partial_amount = float(invoice_sent.total) / 2
        data = {
            'payment_amount': str(partial_amount),
        }

        response = authenticated_admin_client.post(
            f'/api/api/invoices/{invoice_sent.id}/mark_paid/',
            data
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == Invoice.PARTIALLY_PAID

    def test_generate_pdf(self, authenticated_admin_client, invoice_draft):
        """Test generating PDF for invoice."""
        response = authenticated_admin_client.post(
            f'/api/api/invoices/{invoice_draft.id}/generate_pdf/'
        )

        # Should return success even if PDF generation is not implemented
        assert response.status_code == status.HTTP_200_OK

    def test_recalculate_totals(self, authenticated_admin_client, invoice_draft, invoice_item):
        """Test recalculating invoice totals."""
        response = authenticated_admin_client.post(
            f'/api/api/invoices/{invoice_draft.id}/recalculate/'
        )

        assert response.status_code == status.HTTP_200_OK

    def test_get_invoice_items(self, authenticated_admin_client, invoice_draft, invoice_item):
        """Test getting items for a specific invoice."""
        response = authenticated_admin_client.get(
            f'/api/api/invoices/{invoice_draft.id}/items/'
        )

        assert response.status_code == status.HTTP_200_OK


# ============================================================================
# Invoice Item ViewSet Tests
# ============================================================================

@pytest.mark.django_db
class TestInvoiceItemViewSet:
    """Tests for InvoiceItemViewSet."""

    def test_list_invoice_items(self, authenticated_admin_client, invoice_item):
        """Test listing invoice items."""
        response = authenticated_admin_client.get('/api/api/items/')

        assert response.status_code == status.HTTP_200_OK

    def test_create_invoice_item(self, authenticated_admin_client, invoice_draft):
        """Test creating an invoice item."""
        data = {
            'invoice': str(invoice_draft.id),
            'description': 'New Service',
            'quantity': '2.00',
            'unit_price': '500.00',
        }

        response = authenticated_admin_client.post('/api/api/items/', data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['description'] == 'New Service'

    def test_update_invoice_item(self, authenticated_admin_client, invoice_item):
        """Test updating an invoice item."""
        data = {
            'description': 'Updated Service Description',
        }

        response = authenticated_admin_client.patch(
            f'/api/api/items/{invoice_item.id}/',
            data
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['description'] == 'Updated Service Description'

    def test_delete_invoice_item(self, authenticated_admin_client, invoice_item):
        """Test deleting an invoice item."""
        response = authenticated_admin_client.delete(
            f'/api/api/items/{invoice_item.id}/'
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT


# ============================================================================
# Invoice Authorization Tests
# ============================================================================

@pytest.mark.django_db
class TestInvoiceAuthorization:
    """Tests for invoice authorization."""

    def test_non_staff_filtered_access(
        self, authenticated_contributor_client, invoice_draft
    ):
        """Test non-staff users have filtered access."""
        response = authenticated_contributor_client.get('/api/api/invoices/')

        assert response.status_code == status.HTTP_200_OK


# ============================================================================
# Invoice View Edge Cases
# ============================================================================

@pytest.mark.django_db
class TestInvoiceViewEdgeCases:
    """Edge case tests for invoice views."""

    def test_retrieve_nonexistent_invoice(self, authenticated_admin_client):
        """Test retrieving a nonexistent invoice."""
        import uuid
        fake_id = uuid.uuid4()

        response = authenticated_admin_client.get(f'/api/api/invoices/{fake_id}/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_invoice_with_metadata(self, authenticated_admin_client, client_company):
        """Test creating invoice with metadata."""
        data = {
            'client': str(client_company.id),
            'issue_date': str(date.today()),
            'due_date': str(date.today() + timedelta(days=30)),
            'metadata': {'po_number': 'PO-12345'},
        }

        response = authenticated_admin_client.post(
            '/api/api/invoices/',
            data,
            format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['metadata']['po_number'] == 'PO-12345'

    def test_invoice_with_contract(
        self, authenticated_admin_client, client_company, contract_fixed
    ):
        """Test creating invoice associated with contract."""
        data = {
            'client': str(client_company.id),
            'contract': str(contract_fixed.id),
            'issue_date': str(date.today()),
            'due_date': str(date.today() + timedelta(days=30)),
        }

        response = authenticated_admin_client.post('/api/api/invoices/', data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['contract'] == str(contract_fixed.id)
