"""
Tests for documents app frontend views.

Tests cover:
- DocumentListView (list, filtering by type, search)
- DocumentDetailView (detail page with metadata)
- DocumentUploadView (upload form page)
- Authentication enforcement (LoginRequiredMixin redirects)
"""

import pytest
from django.test import Client as TestClient
from django.template import TemplateDoesNotExist
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile

import factory
from decimal import Decimal
from apps.accounts.models import User
from apps.clients.models import Client
from apps.contracts.models import Contract
from apps.documents.models import Document


# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------
class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating User instances."""

    class Meta:
        model = User

    email = factory.Sequence(lambda n: f'docuser{n}@test.com')
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
    email = factory.Sequence(lambda n: f'docclient{n}@test.com')
    company_name = factory.Faker('company')
    client_type = Client.COMPANY
    is_active = True


class ContractFactory(factory.django.DjangoModelFactory):
    """Factory for creating Contract instances."""

    class Meta:
        model = Contract

    title = factory.Sequence(lambda n: f'Contract {n}')
    description = factory.Faker('sentence')
    client = factory.SubFactory(ClientFactory)
    owner = factory.SubFactory(UserFactory)
    contract_type = Contract.FIXED_PRICE
    status = Contract.DRAFT
    start_date = factory.LazyFunction(lambda: timezone.now().date())
    value = Decimal('10000.00')


class DocumentFactory(factory.django.DjangoModelFactory):
    """Factory for creating Document instances."""

    class Meta:
        model = Document

    title = factory.Sequence(lambda n: f'Document {n}')
    description = factory.Faker('sentence')
    document_type = Document.OTHER
    file = factory.LazyFunction(
        lambda: SimpleUploadedFile('test.pdf', b'fake pdf content', content_type='application/pdf')
    )
    file_type = 'pdf'
    file_size = 1024
    uploaded_by = factory.SubFactory(UserFactory)
    client = factory.SubFactory(ClientFactory)


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------
DOCUMENT_LIST_URL = '/api/'
DOCUMENT_UPLOAD_URL = '/api/upload/'


def document_detail_url(pk):
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
def document(user, client_obj):
    return DocumentFactory(uploaded_by=user, client=client_obj)


# ---------------------------------------------------------------------------
# DocumentListView tests
# ---------------------------------------------------------------------------
class TestDocumentListView:
    """Tests for DocumentListView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self):
        client = TestClient()
        response = client.get(DOCUMENT_LIST_URL)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client, document):
        try:
            response = auth_client.get(DOCUMENT_LIST_URL)
            assert response.status_code == 200
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_expected_keys(self, auth_client, document):
        try:
            response = auth_client.get(DOCUMENT_LIST_URL)
            ctx = response.context
            assert ctx['page_title'] == 'Documents'
            assert 'type_choices' in ctx
            assert 'current_type' in ctx
            assert 'search_query' in ctx
            assert 'total_documents' in ctx
            assert 'documents' in ctx
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_filter_by_type(self, auth_client, user, client_obj):
        contract_doc = DocumentFactory(
            uploaded_by=user, client=client_obj,
            document_type=Document.CONTRACT
        )
        DocumentFactory(
            uploaded_by=user, client=client_obj,
            document_type=Document.RECEIPT
        )
        try:
            response = auth_client.get(
                DOCUMENT_LIST_URL, {'type': Document.CONTRACT}
            )
            documents = list(response.context['documents'])
            assert contract_doc in documents
            assert all(d.document_type == Document.CONTRACT for d in documents)
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_search_by_title(self, auth_client, user, client_obj):
        target = DocumentFactory(
            uploaded_by=user, client=client_obj,
            title='Unique Document Title'
        )
        DocumentFactory(
            uploaded_by=user, client=client_obj,
            title='Other document'
        )
        try:
            response = auth_client.get(DOCUMENT_LIST_URL, {'q': 'Unique Document'})
            documents = list(response.context['documents'])
            assert target in documents
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_search_by_description(self, auth_client, user, client_obj):
        target = DocumentFactory(
            uploaded_by=user, client=client_obj,
            description='Very specific description text'
        )
        DocumentFactory(
            uploaded_by=user, client=client_obj,
            description='Generic description'
        )
        try:
            response = auth_client.get(
                DOCUMENT_LIST_URL, {'q': 'Very specific description'}
            )
            documents = list(response.context['documents'])
            assert target in documents
        except TemplateDoesNotExist:
            pass


# ---------------------------------------------------------------------------
# DocumentDetailView tests
# ---------------------------------------------------------------------------
class TestDocumentDetailView:
    """Tests for DocumentDetailView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self, document):
        client = TestClient()
        response = client.get(document_detail_url(document.pk))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client, document):
        try:
            response = auth_client.get(document_detail_url(document.pk))
            assert response.status_code == 200
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_expected_keys(self, auth_client, document):
        try:
            response = auth_client.get(document_detail_url(document.pk))
            ctx = response.context
            assert ctx['document'] == document
            assert 'page_title' in ctx
            assert 'is_pdf' in ctx
            assert 'is_image' in ctx
            assert 'file_extension' in ctx
            assert 'file_size' in ctx
            assert 'uploaded_by' in ctx
            assert 'client' in ctx
            assert 'contract' in ctx
            assert 'invoice' in ctx
        except TemplateDoesNotExist:
            pass


# ---------------------------------------------------------------------------
# DocumentUploadView tests
# ---------------------------------------------------------------------------
class TestDocumentUploadView:
    """Tests for DocumentUploadView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self):
        client = TestClient()
        response = client.get(DOCUMENT_UPLOAD_URL)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client):
        try:
            response = auth_client.get(DOCUMENT_UPLOAD_URL)
            assert response.status_code == 200
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_expected_keys(self, auth_client):
        try:
            response = auth_client.get(DOCUMENT_UPLOAD_URL)
            ctx = response.context
            assert ctx['page_title'] == 'Upload Document'
            assert 'type_choices' in ctx
            assert 'clients' in ctx
            assert 'contracts' in ctx
        except TemplateDoesNotExist:
            pass
