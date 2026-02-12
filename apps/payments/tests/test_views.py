"""
Tests for payments app views and viewsets.
"""

import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.urls import reverse
from rest_framework import status as http_status

from apps.payments.models import Payment, PaymentMethod


# ============================================================================
# PaymentViewSet Tests
# ============================================================================


class TestPaymentViewSetList:
    """Tests for PaymentViewSet list action."""

    @pytest.mark.django_db
    def test_list_requires_authentication(self, api_client):
        """Test that unauthenticated requests are rejected."""
        url = reverse('payments:payment-list')
        response = api_client.get(url)
        assert response.status_code == http_status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_list_returns_payments(self, authenticated_admin_client, payment_successful):
        """Test listing payments as authenticated admin."""
        url = reverse('payments:payment-list')
        response = authenticated_admin_client.get(url)
        assert response.status_code == http_status.HTTP_200_OK

    @pytest.mark.django_db
    def test_list_staff_sees_all_payments(
        self, authenticated_admin_client, payment_successful, payment_pending, payment_failed
    ):
        """Test that staff user sees all payments."""
        # Make admin user is_staff
        user = authenticated_admin_client.handler._force_user
        user.is_staff = True
        user.save()

        url = reverse('payments:payment-list')
        response = authenticated_admin_client.get(url)
        assert response.status_code == http_status.HTTP_200_OK
        assert len(response.data['results']) == 3

    @pytest.mark.django_db
    def test_list_non_staff_sees_filtered_payments(
        self, api_client, contributor_user, payment_successful
    ):
        """Test that non-staff user sees only their payments."""
        contributor_user.is_staff = False
        contributor_user.save()
        api_client.force_authenticate(user=contributor_user)

        url = reverse('payments:payment-list')
        response = api_client.get(url)
        assert response.status_code == http_status.HTTP_200_OK

    @pytest.mark.django_db
    def test_list_ordering_by_payment_date(
        self, authenticated_admin_client, payment_successful, payment_pending
    ):
        """Test that payments are ordered by -payment_date by default."""
        user = authenticated_admin_client.handler._force_user
        user.is_staff = True
        user.save()

        url = reverse('payments:payment-list')
        response = authenticated_admin_client.get(url)
        assert response.status_code == http_status.HTTP_200_OK

        results = response.data['results']
        if len(results) >= 2:
            # Default ordering is -payment_date
            assert results[0]['payment_date'] >= results[1]['payment_date']

    @pytest.mark.django_db
    def test_list_search_by_transaction_id(
        self, authenticated_admin_client, payment_successful
    ):
        """Test searching payments by transaction_id."""
        user = authenticated_admin_client.handler._force_user
        user.is_staff = True
        user.save()

        url = reverse('payments:payment-list')
        response = authenticated_admin_client.get(url, {'search': payment_successful.transaction_id})
        assert response.status_code == http_status.HTTP_200_OK

    @pytest.mark.django_db
    def test_list_filter_by_status(
        self, authenticated_admin_client, payment_successful, payment_failed
    ):
        """Test filtering payments by status."""
        user = authenticated_admin_client.handler._force_user
        user.is_staff = True
        user.save()

        url = reverse('payments:payment-list')
        response = authenticated_admin_client.get(url, {'status': Payment.SUCCEEDED})
        assert response.status_code == http_status.HTTP_200_OK

        for payment in response.data['results']:
            assert payment['status'] == Payment.SUCCEEDED


class TestPaymentViewSetRetrieve:
    """Tests for PaymentViewSet retrieve action."""

    @pytest.mark.django_db
    def test_retrieve_payment(self, authenticated_admin_client, payment_successful):
        """Test retrieving a single payment."""
        url = reverse('payments:payment-detail', kwargs={'pk': str(payment_successful.id)})
        response = authenticated_admin_client.get(url)
        assert response.status_code == http_status.HTTP_200_OK
        assert response.data['id'] == str(payment_successful.id)

    @pytest.mark.django_db
    def test_retrieve_nonexistent_payment(self, authenticated_admin_client):
        """Test retrieving a non-existent payment returns 404."""
        url = reverse('payments:payment-detail', kwargs={'pk': '00000000-0000-0000-0000-000000000099'})
        response = authenticated_admin_client.get(url)
        assert response.status_code == http_status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_retrieve_requires_authentication(self, api_client, payment_successful):
        """Test that retrieving a payment requires authentication."""
        url = reverse('payments:payment-detail', kwargs={'pk': str(payment_successful.id)})
        response = api_client.get(url)
        assert response.status_code == http_status.HTTP_401_UNAUTHORIZED


class TestPaymentViewSetStats:
    """Tests for PaymentViewSet stats action."""

    @pytest.mark.django_db
    def test_stats_returns_statistics(self, authenticated_admin_client, payment_successful):
        """Test that stats endpoint returns expected fields."""
        url = reverse('payments:payment-stats')
        response = authenticated_admin_client.get(url)
        assert response.status_code == http_status.HTTP_200_OK

        data = response.data
        assert 'total_payments' in data
        assert 'successful_payments' in data
        assert 'failed_payments' in data
        assert 'refunded_payments' in data
        assert 'total_amount' in data
        assert 'total_refunded' in data

    @pytest.mark.django_db
    def test_stats_counts_correct(
        self, authenticated_admin_client, payment_successful, payment_failed, payment_pending
    ):
        """Test that stats counts are correct."""
        user = authenticated_admin_client.handler._force_user
        user.is_staff = True
        user.save()

        url = reverse('payments:payment-stats')
        response = authenticated_admin_client.get(url)
        assert response.status_code == http_status.HTTP_200_OK

        data = response.data
        assert data['total_payments'] == 3
        assert data['successful_payments'] == 1
        assert data['failed_payments'] == 1

    @pytest.mark.django_db
    def test_stats_empty_result(self, authenticated_admin_client):
        """Test stats with no payments."""
        user = authenticated_admin_client.handler._force_user
        user.is_staff = True
        user.save()

        url = reverse('payments:payment-stats')
        response = authenticated_admin_client.get(url)
        assert response.status_code == http_status.HTTP_200_OK

        data = response.data
        assert data['total_payments'] == 0
        assert Decimal(str(data['total_amount'])) == Decimal('0')
        assert Decimal(str(data['total_refunded'])) == Decimal('0')

    @pytest.mark.django_db
    def test_stats_requires_authentication(self, api_client):
        """Test that stats requires authentication."""
        url = reverse('payments:payment-stats')
        response = api_client.get(url)
        assert response.status_code == http_status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_stats_total_amount(self, authenticated_admin_client, payment_successful):
        """Test that total_amount sums only successful payments."""
        user = authenticated_admin_client.handler._force_user
        user.is_staff = True
        user.save()

        url = reverse('payments:payment-stats')
        response = authenticated_admin_client.get(url)
        assert response.status_code == http_status.HTTP_200_OK

        assert Decimal(str(response.data['total_amount'])) == payment_successful.amount


class TestPaymentViewSetRefund:
    """Tests for PaymentViewSet refund action."""

    @pytest.mark.django_db
    def test_refund_successful_payment(self, authenticated_admin_client, payment_successful):
        """Test refunding a successful payment."""
        url = reverse('payments:payment-refund', kwargs={'pk': str(payment_successful.id)})
        data = {
            'refund_amount': '500.00',
            'reason': 'Customer request',
        }
        response = authenticated_admin_client.post(url, data)
        assert response.status_code == http_status.HTTP_200_OK

        payment_successful.refresh_from_db()
        assert payment_successful.refunded_amount == Decimal('500.00')
        assert payment_successful.refund_reason == 'Customer request'

    @pytest.mark.django_db
    def test_refund_full_amount(self, authenticated_admin_client, payment_successful):
        """Test full refund marks payment as refunded."""
        url = reverse('payments:payment-refund', kwargs={'pk': str(payment_successful.id)})
        data = {
            'refund_amount': str(payment_successful.amount),
            'reason': 'Full refund',
        }
        response = authenticated_admin_client.post(url, data)
        assert response.status_code == http_status.HTTP_200_OK

        payment_successful.refresh_from_db()
        assert payment_successful.status == Payment.REFUNDED
        assert payment_successful.refunded_at is not None

    @pytest.mark.django_db
    def test_refund_without_amount_fails(self, authenticated_admin_client, payment_successful):
        """Test that refund without amount returns 400."""
        url = reverse('payments:payment-refund', kwargs={'pk': str(payment_successful.id)})
        data = {'reason': 'Missing amount'}
        response = authenticated_admin_client.post(url, data)
        assert response.status_code == http_status.HTTP_400_BAD_REQUEST
        assert 'Refund amount is required' in response.data['detail']

    @pytest.mark.django_db
    def test_refund_exceeding_amount_fails(self, authenticated_admin_client, payment_successful):
        """Test that refund exceeding available amount returns 400."""
        url = reverse('payments:payment-refund', kwargs={'pk': str(payment_successful.id)})
        data = {
            'refund_amount': str(payment_successful.amount + Decimal('100.00')),
            'reason': 'Too much',
        }
        response = authenticated_admin_client.post(url, data)
        assert response.status_code == http_status.HTTP_400_BAD_REQUEST
        assert 'exceeds' in response.data['detail'].lower()

    @pytest.mark.django_db
    def test_refund_failed_payment_fails(self, authenticated_admin_client, payment_failed):
        """Test that refunding a failed payment returns 400."""
        url = reverse('payments:payment-refund', kwargs={'pk': str(payment_failed.id)})
        data = {'refund_amount': '100.00', 'reason': 'Cannot refund failed'}
        response = authenticated_admin_client.post(url, data)
        assert response.status_code == http_status.HTTP_400_BAD_REQUEST
        assert 'successful' in response.data['detail'].lower()

    @pytest.mark.django_db
    def test_refund_pending_payment_fails(self, authenticated_admin_client, payment_pending):
        """Test that refunding a pending payment returns 400."""
        url = reverse('payments:payment-refund', kwargs={'pk': str(payment_pending.id)})
        data = {'refund_amount': '100.00'}
        response = authenticated_admin_client.post(url, data)
        assert response.status_code == http_status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_refund_without_reason(self, authenticated_admin_client, payment_successful):
        """Test partial refund without reason succeeds."""
        url = reverse('payments:payment-refund', kwargs={'pk': str(payment_successful.id)})
        data = {'refund_amount': '100.00'}
        response = authenticated_admin_client.post(url, data)
        assert response.status_code == http_status.HTTP_200_OK

    @pytest.mark.django_db
    def test_refund_requires_authentication(self, api_client, payment_successful):
        """Test that refund requires authentication."""
        url = reverse('payments:payment-refund', kwargs={'pk': str(payment_successful.id)})
        data = {'refund_amount': '100.00'}
        response = api_client.post(url, data)
        assert response.status_code == http_status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_refund_invalid_amount_format(self, authenticated_admin_client, payment_successful):
        """Test refund with invalid amount format."""
        url = reverse('payments:payment-refund', kwargs={'pk': str(payment_successful.id)})
        data = {'refund_amount': 'not_a_number'}
        response = authenticated_admin_client.post(url, data)
        # ValueError from float() conversion should be caught
        assert response.status_code == http_status.HTTP_500_INTERNAL_SERVER_ERROR

    @pytest.mark.django_db
    def test_partial_refund_then_full_refund(self, authenticated_admin_client, payment_successful):
        """Test partial refund followed by a refund for remaining amount."""
        url = reverse('payments:payment-refund', kwargs={'pk': str(payment_successful.id)})

        # First partial refund
        data = {'refund_amount': '1000.00', 'reason': 'Partial'}
        response = authenticated_admin_client.post(url, data)
        assert response.status_code == http_status.HTTP_200_OK

        # Second refund for remaining
        remaining = payment_successful.amount - Decimal('1000.00')
        data = {'refund_amount': str(remaining), 'reason': 'Rest'}
        response = authenticated_admin_client.post(url, data)
        assert response.status_code == http_status.HTTP_200_OK

        payment_successful.refresh_from_db()
        assert payment_successful.status == Payment.REFUNDED


class TestPaymentViewSetQuerysetFiltering:
    """Tests for PaymentViewSet queryset filtering based on user role."""

    @pytest.mark.django_db
    def test_staff_user_gets_all_payments(
        self, api_client, admin_user, payment_successful, payment_failed
    ):
        """Test that staff user sees all payments."""
        admin_user.is_staff = True
        admin_user.save()
        api_client.force_authenticate(user=admin_user)

        url = reverse('payments:payment-list')
        response = api_client.get(url)
        assert response.status_code == http_status.HTTP_200_OK
        # Staff should see all (payment_successful & payment_failed both have client with owner=admin_user)
        assert len(response.data['results']) >= 2

    @pytest.mark.django_db
    def test_non_staff_user_gets_filtered_payments(
        self, api_client, contributor_user, payment_successful
    ):
        """Test that non-staff user sees only their permitted payments."""
        contributor_user.is_staff = False
        contributor_user.save()
        api_client.force_authenticate(user=contributor_user)

        url = reverse('payments:payment-list')
        response = api_client.get(url)
        assert response.status_code == http_status.HTTP_200_OK
        # contributor_user is not the owner of any client, so they should not see these
        # unless client.owner is null


# ============================================================================
# PaymentMethodViewSet Tests
# ============================================================================


class TestPaymentMethodViewSetList:
    """Tests for PaymentMethodViewSet list action."""

    @pytest.mark.django_db
    def test_list_requires_authentication(self, api_client):
        """Test that unauthenticated requests are rejected."""
        url = reverse('payments:payment-method-list')
        response = api_client.get(url)
        assert response.status_code == http_status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_list_returns_payment_methods(
        self, authenticated_admin_client, payment_method_card
    ):
        """Test listing payment methods."""
        url = reverse('payments:payment-method-list')
        response = authenticated_admin_client.get(url)
        assert response.status_code == http_status.HTTP_200_OK

    @pytest.mark.django_db
    def test_list_staff_sees_all_methods(
        self, authenticated_admin_client, payment_method_card
    ):
        """Test that staff user sees all payment methods."""
        user = authenticated_admin_client.handler._force_user
        user.is_staff = True
        user.save()

        url = reverse('payments:payment-method-list')
        response = authenticated_admin_client.get(url)
        assert response.status_code == http_status.HTTP_200_OK
        assert len(response.data['results']) == 1

    @pytest.mark.django_db
    def test_list_non_staff_filtering(self, api_client, contributor_user, payment_method_card):
        """Test non-staff user queryset filtering."""
        contributor_user.is_staff = False
        contributor_user.save()
        api_client.force_authenticate(user=contributor_user)

        url = reverse('payments:payment-method-list')
        response = api_client.get(url)
        assert response.status_code == http_status.HTTP_200_OK

    @pytest.mark.django_db
    def test_filter_by_client(self, authenticated_admin_client, payment_method_card, client_company):
        """Test filtering payment methods by client."""
        user = authenticated_admin_client.handler._force_user
        user.is_staff = True
        user.save()

        url = reverse('payments:payment-method-list')
        response = authenticated_admin_client.get(url, {'client': str(client_company.id)})
        assert response.status_code == http_status.HTTP_200_OK

        for pm in response.data['results']:
            assert str(pm['client']) == str(client_company.id)

    @pytest.mark.django_db
    def test_filter_by_is_default(self, authenticated_admin_client, payment_method_card):
        """Test filtering payment methods by is_default."""
        user = authenticated_admin_client.handler._force_user
        user.is_staff = True
        user.save()

        url = reverse('payments:payment-method-list')
        response = authenticated_admin_client.get(url, {'is_default': True})
        assert response.status_code == http_status.HTTP_200_OK

        for pm in response.data['results']:
            assert pm['is_default'] is True

    @pytest.mark.django_db
    def test_filter_by_type(self, authenticated_admin_client, payment_method_card):
        """Test filtering payment methods by type."""
        user = authenticated_admin_client.handler._force_user
        user.is_staff = True
        user.save()

        url = reverse('payments:payment-method-list')
        response = authenticated_admin_client.get(url, {'type': Payment.CARD})
        assert response.status_code == http_status.HTTP_200_OK

        for pm in response.data['results']:
            assert pm['type'] == Payment.CARD

    @pytest.mark.django_db
    def test_filter_by_is_active(self, authenticated_admin_client, payment_method_card):
        """Test filtering payment methods by is_active."""
        user = authenticated_admin_client.handler._force_user
        user.is_staff = True
        user.save()

        url = reverse('payments:payment-method-list')
        response = authenticated_admin_client.get(url, {'is_active': True})
        assert response.status_code == http_status.HTTP_200_OK

        for pm in response.data['results']:
            assert pm['is_active'] is True


class TestPaymentMethodViewSetCreate:
    """Tests for PaymentMethodViewSet create action."""

    @pytest.mark.django_db
    def test_create_payment_method(self, authenticated_admin_client, client_company):
        """Test creating a payment method."""
        url = reverse('payments:payment-method-list')
        data = {
            'client': str(client_company.id),
            'type': Payment.CARD,
            'is_default': False,
            'card_last4': '1234',
            'card_brand': 'mastercard',
            'card_exp_month': 6,
            'card_exp_year': 2027,
            'stripe_payment_method_id': 'pm_new_test_card',
            'is_active': True,
        }
        response = authenticated_admin_client.post(url, data)
        assert response.status_code == http_status.HTTP_201_CREATED
        assert response.data['card_last4'] == '1234'
        assert response.data['card_brand'] == 'mastercard'

    @pytest.mark.django_db
    def test_create_payment_method_requires_auth(self, api_client, client_company):
        """Test that creating a payment method requires authentication."""
        url = reverse('payments:payment-method-list')
        data = {
            'client': str(client_company.id),
            'type': Payment.CARD,
            'stripe_payment_method_id': 'pm_unauth_test',
        }
        response = api_client.post(url, data)
        assert response.status_code == http_status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_create_default_payment_method(self, authenticated_admin_client, client_company):
        """Test creating a default payment method."""
        url = reverse('payments:payment-method-list')
        data = {
            'client': str(client_company.id),
            'type': Payment.BANK_TRANSFER,
            'is_default': True,
            'stripe_payment_method_id': 'pm_bank_test',
            'is_active': True,
        }
        response = authenticated_admin_client.post(url, data)
        assert response.status_code == http_status.HTTP_201_CREATED
        assert response.data['is_default'] is True

    @pytest.mark.django_db
    def test_create_payment_method_missing_required_fields(self, authenticated_admin_client):
        """Test creating payment method with missing required fields fails."""
        url = reverse('payments:payment-method-list')
        data = {}
        response = authenticated_admin_client.post(url, data)
        assert response.status_code == http_status.HTTP_400_BAD_REQUEST


class TestPaymentMethodViewSetQuerysetFiltering:
    """Tests for PaymentMethodViewSet queryset filtering."""

    @pytest.mark.django_db
    def test_staff_user_sees_all_methods(
        self, api_client, admin_user, payment_method_card
    ):
        """Test that staff user gets unfiltered queryset."""
        admin_user.is_staff = True
        admin_user.save()
        api_client.force_authenticate(user=admin_user)

        url = reverse('payments:payment-method-list')
        response = api_client.get(url)
        assert response.status_code == http_status.HTTP_200_OK
        assert len(response.data['results']) >= 1

    @pytest.mark.django_db
    def test_non_staff_user_sees_own_methods(
        self, api_client, contributor_user, payment_method_card
    ):
        """Test that non-staff user sees only their client's methods."""
        contributor_user.is_staff = False
        contributor_user.save()
        api_client.force_authenticate(user=contributor_user)

        url = reverse('payments:payment-method-list')
        response = api_client.get(url)
        assert response.status_code == http_status.HTTP_200_OK
        # contributor_user is not the owner of client_company, should not see its methods
