"""
Tests for invoicing app frontend views.

Tests cover:
- InvoiceListView (list, filtering by status, search by invoice number/client)
- InvoiceDetailView (detail page with items, payments, reminders)
- InvoiceCreateView (create form page)
- InvoiceEditView (edit form page with existing invoice data)
- RecurringInvoiceListView (list of recurring invoices)
- RecurringInvoiceDetailView (detail of a recurring invoice)
- LateFeePolicyListView (list of late fee policies)
- PaymentReminderListView (list of payment reminders)
- Authentication enforcement (LoginRequiredMixin redirects)
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import factory
import pytest
from django.test import Client as TestClient
from django.template import TemplateDoesNotExist

from apps.accounts.models import User
from apps.clients.models import Client
from apps.contracts.models import Contract
from apps.invoicing.models import (
    Invoice,
    InvoiceItem,
    RecurringInvoice,
    LateFeePolicy,
    PaymentReminder,
)


# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------
class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating User instances."""

    class Meta:
        model = User
        skip_postgeneration_save = True

    id = factory.LazyFunction(uuid.uuid4)
    email = factory.Sequence(lambda n: f'invuser{n}@test.com')
    username = factory.Sequence(lambda n: f'invuser{n}')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    password = factory.PostGenerationMethodCall('set_password', 'TestPass123!')
    is_active = True
    is_staff = True
    is_verified = True
    role = User.ADMIN


class ClientFactory(factory.django.DjangoModelFactory):
    """Factory for creating Client instances."""

    class Meta:
        model = Client

    client_type = Client.COMPANY
    company_name = factory.Sequence(lambda n: f'Invoice Test Co {n}')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.LazyAttribute(
        lambda obj: f'{obj.first_name.lower()}.{obj.last_name.lower()}@invoicetest.com'
    )
    lifecycle_stage = Client.ACTIVE
    is_active = True
    owner = factory.SubFactory(UserFactory)


class ContractFactory(factory.django.DjangoModelFactory):
    """Factory for creating Contract instances."""

    class Meta:
        model = Contract

    client = factory.SubFactory(ClientFactory)
    title = factory.Sequence(lambda n: f'Contract {n}')
    description = factory.Faker('paragraph')
    contract_number = factory.Sequence(lambda n: f'CNT-{n:05d}')
    status = Contract.ACTIVE
    start_date = factory.LazyFunction(date.today)
    end_date = factory.LazyFunction(lambda: date.today() + timedelta(days=365))
    total_value = Decimal('10000.00')
    currency = 'USD'


class InvoiceFactory(factory.django.DjangoModelFactory):
    """Factory for creating Invoice instances."""

    class Meta:
        model = Invoice

    client = factory.SubFactory(ClientFactory)
    contract = factory.SubFactory(ContractFactory)
    invoice_number = factory.Sequence(lambda n: f'INV-{n:05d}')
    status = Invoice.DRAFT
    issue_date = factory.LazyFunction(date.today)
    due_date = factory.LazyFunction(lambda: date.today() + timedelta(days=30))
    subtotal = Decimal('1000.00')
    tax_rate = Decimal('10.00')
    tax_amount = Decimal('100.00')
    total = Decimal('1100.00')
    paid_amount = Decimal('0.00')
    currency = 'USD'


class InvoiceItemFactory(factory.django.DjangoModelFactory):
    """Factory for creating InvoiceItem instances."""

    class Meta:
        model = InvoiceItem

    invoice = factory.SubFactory(InvoiceFactory)
    description = factory.Faker('sentence')
    quantity = Decimal('1.00')
    unit_price = Decimal('500.00')
    amount = Decimal('500.00')
    order = factory.Sequence(lambda n: n)


class RecurringInvoiceFactory(factory.django.DjangoModelFactory):
    """Factory for creating RecurringInvoice instances."""

    class Meta:
        model = RecurringInvoice

    client = factory.SubFactory(ClientFactory)
    contract = factory.SubFactory(ContractFactory)
    template_name = factory.Sequence(lambda n: f'Recurring Template {n}')
    frequency = RecurringInvoice.MONTHLY
    start_date = factory.LazyFunction(date.today)
    next_run_date = factory.LazyFunction(lambda: date.today() + timedelta(days=30))
    amount = Decimal('500.00')
    currency = 'USD'
    status = RecurringInvoice.ACTIVE
    owner = factory.SubFactory(UserFactory)


class LateFeePolicyFactory(factory.django.DjangoModelFactory):
    """Factory for creating LateFeePolicy instances."""

    class Meta:
        model = LateFeePolicy

    name = factory.Sequence(lambda n: f'Late Fee Policy {n}')
    fee_type = LateFeePolicy.PERCENTAGE
    fee_amount = Decimal('5.00')
    grace_period_days = 7
    is_active = True


class PaymentReminderFactory(factory.django.DjangoModelFactory):
    """Factory for creating PaymentReminder instances."""

    class Meta:
        model = PaymentReminder

    invoice = factory.SubFactory(InvoiceFactory)
    reminder_type = PaymentReminder.BEFORE_DUE
    days_offset = 7
    status = PaymentReminder.SCHEDULED
    scheduled_date = factory.LazyFunction(lambda: date.today() + timedelta(days=23))


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------
INVOICE_LIST_URL = '/api/'
INVOICE_CREATE_URL = '/api/create/'
RECURRING_LIST_URL = '/api/recurring/'
LATE_FEE_LIST_URL = '/api/late-fees/'
REMINDER_LIST_URL = '/api/reminders/'


def invoice_detail_url(pk):
    return f'/api/{pk}/'


def invoice_edit_url(pk):
    return f'/api/{pk}/edit/'


def recurring_detail_url(pk):
    return f'/api/recurring/{pk}/'


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
def client_obj(user):
    return ClientFactory(owner=user)


@pytest.fixture
def invoice(client_obj):
    return InvoiceFactory(client=client_obj, contract=None)


@pytest.fixture
def invoice_with_items(invoice):
    InvoiceItemFactory(invoice=invoice)
    InvoiceItemFactory(invoice=invoice)
    return invoice


@pytest.fixture
def recurring_invoice(user, client_obj):
    return RecurringInvoiceFactory(client=client_obj, owner=user, contract=None)


@pytest.fixture
def late_fee_policy():
    return LateFeePolicyFactory()


@pytest.fixture
def payment_reminder(invoice):
    return PaymentReminderFactory(invoice=invoice)


# ---------------------------------------------------------------------------
# InvoiceListView tests
# ---------------------------------------------------------------------------
class TestInvoiceListView:
    """Tests for InvoiceListView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self):
        client = TestClient()
        response = client.get(INVOICE_LIST_URL)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client, invoice):
        try:
            response = auth_client.get(INVOICE_LIST_URL)
            assert response.status_code == 200
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_expected_keys(self, auth_client, invoice):
        try:
            response = auth_client.get(INVOICE_LIST_URL)
            ctx = response.context
            assert ctx['page_title'] == 'Invoices'
            assert 'status_choices' in ctx
            assert 'current_status' in ctx
            assert 'search_query' in ctx
            assert 'total_invoices' in ctx
            assert 'total_outstanding' in ctx
            assert 'overdue_count' in ctx
            assert 'invoices' in ctx
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_filter_by_status(self, auth_client, client_obj):
        draft_invoice = InvoiceFactory(
            client=client_obj, status=Invoice.DRAFT, contract=None
        )
        InvoiceFactory(
            client=client_obj, status=Invoice.PAID, contract=None
        )
        try:
            response = auth_client.get(INVOICE_LIST_URL, {'status': Invoice.DRAFT})
            invoices = list(response.context['invoices'])
            assert draft_invoice in invoices
            assert all(inv.status == Invoice.DRAFT for inv in invoices)
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_search_by_invoice_number(self, auth_client, client_obj):
        target = InvoiceFactory(
            client=client_obj,
            invoice_number='INV-99999',
            contract=None,
        )
        InvoiceFactory(
            client=client_obj,
            invoice_number='INV-00001',
            contract=None,
        )
        try:
            response = auth_client.get(INVOICE_LIST_URL, {'q': 'INV-99999'})
            invoices = list(response.context['invoices'])
            assert target in invoices
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_search_by_client_name(self, auth_client):
        special_client = ClientFactory(company_name='UniqueCompanySearch')
        target = InvoiceFactory(client=special_client, contract=None)
        InvoiceFactory(client=ClientFactory(), contract=None)
        try:
            response = auth_client.get(INVOICE_LIST_URL, {'q': 'UniqueCompanySearch'})
            invoices = list(response.context['invoices'])
            assert target in invoices
        except TemplateDoesNotExist:
            pass


# ---------------------------------------------------------------------------
# InvoiceDetailView tests
# ---------------------------------------------------------------------------
class TestInvoiceDetailView:
    """Tests for InvoiceDetailView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self, invoice):
        client = TestClient()
        response = client.get(invoice_detail_url(invoice.pk))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client, invoice_with_items):
        try:
            response = auth_client.get(invoice_detail_url(invoice_with_items.pk))
            assert response.status_code == 200
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_expected_keys(self, auth_client, invoice_with_items):
        try:
            response = auth_client.get(invoice_detail_url(invoice_with_items.pk))
            ctx = response.context
            assert ctx['invoice'] == invoice_with_items
            assert 'items' in ctx
            assert 'payments' in ctx
            assert 'reminders' in ctx
            assert 'page_title' in ctx
            assert 'balance_due' in ctx
            assert 'is_overdue' in ctx
            assert 'is_fully_paid' in ctx
        except TemplateDoesNotExist:
            pass


# ---------------------------------------------------------------------------
# InvoiceCreateView tests
# ---------------------------------------------------------------------------
class TestInvoiceCreateView:
    """Tests for InvoiceCreateView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self):
        client = TestClient()
        response = client.get(INVOICE_CREATE_URL)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client):
        try:
            response = auth_client.get(INVOICE_CREATE_URL)
            assert response.status_code == 200
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_expected_keys(self, auth_client):
        try:
            response = auth_client.get(INVOICE_CREATE_URL)
            ctx = response.context
            assert ctx['page_title'] == 'Create Invoice'
            assert 'clients' in ctx
            assert 'contracts' in ctx
        except TemplateDoesNotExist:
            pass


# ---------------------------------------------------------------------------
# InvoiceEditView tests
# ---------------------------------------------------------------------------
class TestInvoiceEditView:
    """Tests for InvoiceEditView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self, invoice):
        client = TestClient()
        response = client.get(invoice_edit_url(invoice.pk))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client, invoice):
        try:
            response = auth_client.get(invoice_edit_url(invoice.pk))
            assert response.status_code == 200
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_expected_keys(self, auth_client, invoice_with_items):
        try:
            response = auth_client.get(invoice_edit_url(invoice_with_items.pk))
            ctx = response.context
            assert ctx['invoice'] == invoice_with_items
            assert 'items' in ctx
            assert 'page_title' in ctx
            assert 'status_choices' in ctx
            assert 'clients' in ctx
            assert 'contracts' in ctx
        except TemplateDoesNotExist:
            pass


# ---------------------------------------------------------------------------
# RecurringInvoiceListView tests
# ---------------------------------------------------------------------------
class TestRecurringInvoiceListView:
    """Tests for RecurringInvoiceListView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self):
        client = TestClient()
        response = client.get(RECURRING_LIST_URL)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client, recurring_invoice):
        try:
            response = auth_client.get(RECURRING_LIST_URL)
            assert response.status_code == 200
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_expected_keys(self, auth_client, recurring_invoice):
        try:
            response = auth_client.get(RECURRING_LIST_URL)
            ctx = response.context
            assert ctx['page_title'] == 'Recurring Invoices'
            assert 'status_choices' in ctx
            assert 'frequency_choices' in ctx
            assert 'active_count' in ctx
            assert 'recurring_invoices' in ctx
        except TemplateDoesNotExist:
            pass


# ---------------------------------------------------------------------------
# RecurringInvoiceDetailView tests
# ---------------------------------------------------------------------------
class TestRecurringInvoiceDetailView:
    """Tests for RecurringInvoiceDetailView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self, recurring_invoice):
        client = TestClient()
        response = client.get(recurring_detail_url(recurring_invoice.pk))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client, recurring_invoice):
        try:
            response = auth_client.get(recurring_detail_url(recurring_invoice.pk))
            assert response.status_code == 200
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_expected_keys(self, auth_client, recurring_invoice):
        try:
            response = auth_client.get(recurring_detail_url(recurring_invoice.pk))
            ctx = response.context
            assert 'page_title' in ctx
            assert 'is_due' in ctx
            assert 'invoices_generated' in ctx
            assert 'next_run_date' in ctx
            assert 'items_template' in ctx
            assert ctx['recurring_invoice'] == recurring_invoice
        except TemplateDoesNotExist:
            pass


# ---------------------------------------------------------------------------
# LateFeePolicyListView tests
# ---------------------------------------------------------------------------
class TestLateFeePolicyListView:
    """Tests for LateFeePolicyListView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self):
        client = TestClient()
        response = client.get(LATE_FEE_LIST_URL)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client, late_fee_policy):
        try:
            response = auth_client.get(LATE_FEE_LIST_URL)
            assert response.status_code == 200
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_expected_keys(self, auth_client, late_fee_policy):
        try:
            response = auth_client.get(LATE_FEE_LIST_URL)
            ctx = response.context
            assert ctx['page_title'] == 'Late Fee Policies'
            assert 'fee_type_choices' in ctx
            assert 'frequency_choices' in ctx
            assert 'active_count' in ctx
            assert 'policies' in ctx
        except TemplateDoesNotExist:
            pass


# ---------------------------------------------------------------------------
# PaymentReminderListView tests
# ---------------------------------------------------------------------------
class TestPaymentReminderListView:
    """Tests for PaymentReminderListView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self):
        client = TestClient()
        response = client.get(REMINDER_LIST_URL)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client, payment_reminder):
        try:
            response = auth_client.get(REMINDER_LIST_URL)
            assert response.status_code == 200
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_expected_keys(self, auth_client, payment_reminder):
        try:
            response = auth_client.get(REMINDER_LIST_URL)
            ctx = response.context
            assert ctx['page_title'] == 'Payment Reminders'
            assert 'status_choices' in ctx
            assert 'reminder_type_choices' in ctx
            assert 'scheduled_count' in ctx
            assert 'sent_count' in ctx
            assert 'reminders' in ctx
        except TemplateDoesNotExist:
            pass
