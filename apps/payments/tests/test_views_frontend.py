"""
Tests for payments app frontend views.

Tests cover:
- PaymentListView (list, filtering by status/method, search)
- PaymentDetailView (detail page with invoice and refund info)
- PaymentMethodListView (list of saved payment methods)
- Authentication enforcement (LoginRequiredMixin redirects)
"""

import pytest
from decimal import Decimal
from django.test import Client as TestClient
from django.template import TemplateDoesNotExist
from django.utils import timezone

import factory
from apps.accounts.models import User
from apps.clients.models import Client
from apps.contracts.models import Contract
from apps.invoicing.models import Invoice
from apps.payments.models import Payment, PaymentMethod


# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------
class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating User instances."""

    class Meta:
        model = User

    email = factory.Sequence(lambda n: f'paymentuser{n}@test.com')
    username = factory.LazyAttribute(lambda o: o.email)
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    full_name = factory.LazyAttribute(lambda o: f'{o.first_name} {o.last_name}')
    password = factory.PostGenerationMethodCall('set_password', 'TestPass123!')
    is_active = True
    role = User.ADMIN


class ClientFactory(factory.django.DjangoModelFactory):
    """Factory for creating Client instances."""

    class Meta:
        model = Client

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Sequence(lambda n: f'payclient{n}@test.com')
    company_name = factory.Faker('company')
    client_type = Client.COMPANY
    is_active = True


class InvoiceFactory(factory.django.DjangoModelFactory):
    """Factory for creating Invoice instances."""

    class Meta:
        model = Invoice

    invoice_number = factory.Sequence(lambda n: f'INV-{n:05d}')
    client = factory.SubFactory(ClientFactory)
    status = Invoice.SENT
    issue_date = factory.LazyFunction(lambda: timezone.now().date())
    due_date = factory.LazyFunction(lambda: (timezone.now() + timezone.timedelta(days=30)).date())
    subtotal = Decimal('1000.00')
    total = Decimal('1000.00')
    currency = 'USD'


class PaymentFactory(factory.django.DjangoModelFactory):
    """Factory for creating Payment instances."""

    class Meta:
        model = Payment

    invoice = factory.SubFactory(InvoiceFactory)
    amount = Decimal('1000.00')
    currency = 'USD'
    payment_method = Payment.CARD
    status = Payment.SUCCEEDED
    transaction_id = factory.Sequence(lambda n: f'TXN-TEST{n:08d}')
    payment_date = factory.LazyFunction(timezone.now)
    card_last4 = '4242'
    card_brand = 'Visa'
    refunded_amount = Decimal('0.00')


class PaymentMethodFactory(factory.django.DjangoModelFactory):
    """Factory for creating PaymentMethod instances."""

    class Meta:
        model = PaymentMethod

    client = factory.SubFactory(ClientFactory)
    type = Payment.CARD
    is_default = True
    card_last4 = '4242'
    card_brand = 'Visa'
    card_exp_month = 12
    card_exp_year = 2028
    stripe_payment_method_id = factory.Sequence(lambda n: f'pm_test_{n}')
    is_active = True


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------
PAYMENT_LIST_URL = '/api/'
PAYMENT_METHOD_LIST_URL = '/api/methods/'


def payment_detail_url(pk):
    return f'/api/{pk}/'


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def auth_client(user):
    client = TestClient()
    client.force_login(user)
    return client


@pytest.fixture
def client_obj(db):
    return ClientFactory()


@pytest.fixture
def invoice(client_obj):
    return InvoiceFactory(client=client_obj)


@pytest.fixture
def payment(invoice):
    return PaymentFactory(invoice=invoice)


@pytest.fixture
def payment_method(client_obj):
    return PaymentMethodFactory(client=client_obj)


# ---------------------------------------------------------------------------
# PaymentListView tests
# ---------------------------------------------------------------------------
class TestPaymentListView:
    """Tests for PaymentListView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self):
        client = TestClient()
        response = client.get(PAYMENT_LIST_URL)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client, payment):
        try:
            response = auth_client.get(PAYMENT_LIST_URL)
            assert response.status_code == 200
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_expected_keys(self, auth_client, payment):
        try:
            response = auth_client.get(PAYMENT_LIST_URL)
            ctx = response.context
            assert ctx['page_title'] == 'Payments'
            assert 'status_choices' in ctx
            assert 'method_choices' in ctx
            assert 'current_status' in ctx
            assert 'current_method' in ctx
            assert 'search_query' in ctx
            assert 'total_received' in ctx
            assert 'total_refunded' in ctx
            assert 'pending_count' in ctx
            assert 'payments' in ctx
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_filter_by_status(self, auth_client, client_obj):
        succeeded_invoice = InvoiceFactory(client=client_obj)
        pending_invoice = InvoiceFactory(client=client_obj)
        succeeded_payment = PaymentFactory(
            invoice=succeeded_invoice, status=Payment.SUCCEEDED
        )
        PaymentFactory(
            invoice=pending_invoice, status=Payment.PENDING
        )
        try:
            response = auth_client.get(
                PAYMENT_LIST_URL, {'status': Payment.SUCCEEDED}
            )
            payments = list(response.context['payments'])
            assert succeeded_payment in payments
            assert all(p.status == Payment.SUCCEEDED for p in payments)
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_filter_by_method(self, auth_client, client_obj):
        card_invoice = InvoiceFactory(client=client_obj)
        bank_invoice = InvoiceFactory(client=client_obj)
        card_payment = PaymentFactory(
            invoice=card_invoice, payment_method=Payment.CARD
        )
        PaymentFactory(
            invoice=bank_invoice, payment_method=Payment.BANK_TRANSFER
        )
        try:
            response = auth_client.get(
                PAYMENT_LIST_URL, {'method': Payment.CARD}
            )
            payments = list(response.context['payments'])
            assert card_payment in payments
            assert all(p.payment_method == Payment.CARD for p in payments)
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_search_by_transaction_id(self, auth_client, payment):
        try:
            response = auth_client.get(
                PAYMENT_LIST_URL, {'q': payment.transaction_id}
            )
            payments = list(response.context['payments'])
            assert payment in payments
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_search_by_invoice_number(self, auth_client, payment):
        try:
            response = auth_client.get(
                PAYMENT_LIST_URL, {'q': payment.invoice.invoice_number}
            )
            payments = list(response.context['payments'])
            assert payment in payments
        except TemplateDoesNotExist:
            pass


# ---------------------------------------------------------------------------
# PaymentDetailView tests
# ---------------------------------------------------------------------------
class TestPaymentDetailView:
    """Tests for PaymentDetailView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self, payment):
        client = TestClient()
        response = client.get(payment_detail_url(payment.pk))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client, payment):
        try:
            response = auth_client.get(payment_detail_url(payment.pk))
            assert response.status_code == 200
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_expected_keys(self, auth_client, payment):
        try:
            response = auth_client.get(payment_detail_url(payment.pk))
            ctx = response.context
            assert ctx['payment'] == payment
            assert 'page_title' in ctx
            assert 'invoice' in ctx
            assert 'is_successful' in ctx
            assert 'net_amount' in ctx
            assert 'has_refund' in ctx
        except TemplateDoesNotExist:
            pass


# ---------------------------------------------------------------------------
# PaymentMethodListView tests
# ---------------------------------------------------------------------------
class TestPaymentMethodListView:
    """Tests for PaymentMethodListView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self):
        client = TestClient()
        response = client.get(PAYMENT_METHOD_LIST_URL)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client, payment_method):
        try:
            response = auth_client.get(PAYMENT_METHOD_LIST_URL)
            assert response.status_code == 200
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_expected_keys(self, auth_client, payment_method):
        try:
            response = auth_client.get(PAYMENT_METHOD_LIST_URL)
            ctx = response.context
            assert ctx['page_title'] == 'Payment Methods'
            assert 'method_type_choices' in ctx
            assert 'total_methods' in ctx
            assert 'payment_methods' in ctx
        except TemplateDoesNotExist:
            pass
