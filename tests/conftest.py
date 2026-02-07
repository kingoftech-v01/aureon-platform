"""
Pytest configuration and fixtures for Aureon SaaS Platform tests.

This module provides shared fixtures for all test modules including:
- Database fixtures (user, client, contract, invoice, payment)
- API client fixtures
- Factory fixtures
- Security test fixtures
"""

import pytest
import uuid
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


# ============================================================================
# Django Settings Overrides for Tests
# ============================================================================

@pytest.fixture(autouse=True)
def override_test_settings(settings):
    """Override Django settings for the test environment."""
    # Use LocMemCache for all cache backends (Redis may not be available)
    _locmem_cache = {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'TIMEOUT': 300,
    }
    settings.CACHES = {
        'default': {**_locmem_cache, 'LOCATION': 'test-default'},
        'sessions': {**_locmem_cache, 'LOCATION': 'test-sessions'},
        'locks': {**_locmem_cache, 'LOCATION': 'test-locks'},
        'throttle': {**_locmem_cache, 'LOCATION': 'test-throttle'},
        'local': {**_locmem_cache, 'LOCATION': 'test-local'},
    }
    # Disable SSL redirect in tests
    settings.SECURE_SSL_REDIRECT = False
    # Ensure testserver is in allowed hosts
    if 'testserver' not in settings.ALLOWED_HOSTS:
        settings.ALLOWED_HOSTS.append('testserver')
    # Add testserver to trusted origins for CSRF middleware
    settings.CSRF_TRUSTED_ORIGINS = [
        'http://testserver',
        'https://testserver',
        'http://localhost',
        'https://localhost',
    ]


# ============================================================================
# User Fixtures
# ============================================================================

@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    user = User.objects.create_user(
        username='admin',
        email='admin@testorg.com',
        password='SecurePass123!',
        first_name='Admin',
        last_name='User',
        role=User.ADMIN,
        is_verified=True,
        is_active=True,
    )
    return user


@pytest.fixture
def manager_user(db):
    """Create a manager user."""
    user = User.objects.create_user(
        username='manager',
        email='manager@testorg.com',
        password='SecurePass123!',
        first_name='Manager',
        last_name='User',
        role=User.MANAGER,
        is_verified=True,
        is_active=True,
    )
    return user


@pytest.fixture
def contributor_user(db):
    """Create a contributor user."""
    user = User.objects.create_user(
        username='contributor',
        email='contributor@testorg.com',
        password='SecurePass123!',
        first_name='Contributor',
        last_name='User',
        role=User.CONTRIBUTOR,
        is_verified=True,
        is_active=True,
    )
    return user


@pytest.fixture
def client_user(db):
    """Create a client user (portal access)."""
    user = User.objects.create_user(
        username='clientuser',
        email='client@external.com',
        password='SecurePass123!',
        first_name='Client',
        last_name='User',
        role=User.CLIENT,
        is_verified=True,
        is_active=True,
    )
    return user


@pytest.fixture
def superuser(db):
    """Create a superuser."""
    user = User.objects.create_superuser(
        username='superadmin',
        email='superadmin@aureon.com',
        password='SuperSecurePass123!',
        first_name='Super',
        last_name='Admin',
    )
    return user


@pytest.fixture
def inactive_user(db):
    """Create an inactive user."""
    user = User.objects.create_user(
        username='inactive',
        email='inactive@testorg.com',
        password='SecurePass123!',
        first_name='Inactive',
        last_name='User',
        role=User.CONTRIBUTOR,
        is_active=False,
    )
    return user


@pytest.fixture
def user_invitation(db, admin_user):
    """Create a user invitation."""
    from apps.accounts.models import UserInvitation
    import secrets

    invitation = UserInvitation.objects.create(
        email='invitee@external.com',
        role=User.CONTRIBUTOR,
        invited_by=admin_user,
        invitation_token=secrets.token_urlsafe(32),
        expires_at=timezone.now() + timedelta(days=7),
        status=UserInvitation.PENDING,
    )
    return invitation


@pytest.fixture
def api_key(db, admin_user):
    """Create an API key."""
    from apps.accounts.models import ApiKey
    import secrets

    key = secrets.token_urlsafe(32)
    api_key = ApiKey.objects.create(
        user=admin_user,
        name='Test API Key',
        key=key,
        prefix=key[:8],
        scopes=['read', 'write'],
        is_active=True,
    )
    return api_key


# ============================================================================
# Backward-compatible tenant fixture (no-op)
# ============================================================================

@pytest.fixture
def tenant(db):
    """No-op tenant fixture for backward compatibility.

    Multi-tenancy has been removed. This fixture exists so that test files
    that still declare ``tenant`` as a dependency don't break immediately.
    It returns ``None``.
    """
    return None


@pytest.fixture
def tenant_with_trial(db):
    """No-op tenant_with_trial fixture for backward compatibility."""
    return None


@pytest.fixture
def domain(db):
    """No-op domain fixture for backward compatibility."""
    return None


# ============================================================================
# Client Fixtures
# ============================================================================

@pytest.fixture
def client_company(db, admin_user):
    """Create a company client."""
    from apps.clients.models import Client

    client = Client.objects.create(
        client_type=Client.COMPANY,
        company_name='Test Company Inc.',
        first_name='John',
        last_name='Doe',
        email='contact@testcompany.com',
        phone='+1234567890',
        address_line1='456 Client Street',
        city='Client City',
        state='Client State',
        postal_code='54321',
        country='United States',
        industry='Technology',
        company_size='11-50',
        lifecycle_stage=Client.ACTIVE,
        source='Website',
        tags=['enterprise', 'priority'],
        owner=admin_user,
        portal_access_enabled=True,
        is_active=True,
    )
    return client


@pytest.fixture
def client_individual(db, admin_user):
    """Create an individual client."""
    from apps.clients.models import Client

    client = Client.objects.create(
        client_type=Client.INDIVIDUAL,
        first_name='Jane',
        last_name='Smith',
        email='jane.smith@email.com',
        phone='+0987654321',
        lifecycle_stage=Client.PROSPECT,
        source='Referral',
        tags=['freelance'],
        owner=admin_user,
        is_active=True,
    )
    return client


@pytest.fixture
def client_lead(db):
    """Create a lead client without owner."""
    from apps.clients.models import Client

    client = Client.objects.create(
        client_type=Client.INDIVIDUAL,
        first_name='Lead',
        last_name='Contact',
        email='lead@potential.com',
        lifecycle_stage=Client.LEAD,
        source='Cold Outreach',
        is_active=True,
    )
    return client


@pytest.fixture
def client_note(db, client_company, admin_user):
    """Create a client note."""
    from apps.clients.models import ClientNote

    note = ClientNote.objects.create(
        client=client_company,
        author=admin_user,
        note_type='meeting',
        subject='Initial Discovery Call',
        content='Discussed project requirements and timeline.',
    )
    return note


# ============================================================================
# Contract Fixtures
# ============================================================================

@pytest.fixture
def contract_fixed(db, client_company, admin_user):
    """Create a fixed-price contract."""
    from apps.contracts.models import Contract

    contract = Contract.objects.create(
        client=client_company,
        title='Website Development Project',
        description='Full website development including design and implementation.',
        contract_type=Contract.FIXED_PRICE,
        status=Contract.ACTIVE,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=90),
        value=Decimal('15000.00'),
        currency='USD',
        payment_terms='50% upfront, 50% on completion',
        invoice_schedule='Upon milestone completion',
        owner=admin_user,
        signed_by_client=True,
        signed_by_company=True,
        signed_at=timezone.now(),
    )
    return contract


@pytest.fixture
def contract_hourly(db, client_company, admin_user):
    """Create an hourly contract."""
    from apps.contracts.models import Contract

    contract = Contract.objects.create(
        client=client_company,
        title='Consulting Services',
        description='Ongoing consulting and advisory services.',
        contract_type=Contract.HOURLY,
        status=Contract.ACTIVE,
        start_date=date.today(),
        value=Decimal('5000.00'),
        hourly_rate=Decimal('150.00'),
        estimated_hours=Decimal('40.00'),
        currency='USD',
        owner=admin_user,
    )
    return contract


@pytest.fixture
def contract_draft(db, client_individual, manager_user):
    """Create a draft contract."""
    from apps.contracts.models import Contract

    contract = Contract.objects.create(
        client=client_individual,
        title='Draft Project',
        description='A project that is still in draft status.',
        contract_type=Contract.MILESTONE,
        status=Contract.DRAFT,
        start_date=date.today() + timedelta(days=7),
        end_date=date.today() + timedelta(days=37),
        value=Decimal('8000.00'),
        currency='USD',
        owner=manager_user,
    )
    return contract


@pytest.fixture
def contract_milestone(db, contract_fixed):
    """Create a contract milestone."""
    from apps.contracts.models import ContractMilestone

    milestone = ContractMilestone.objects.create(
        contract=contract_fixed,
        title='Design Phase',
        description='Complete all design mockups and get client approval.',
        due_date=date.today() + timedelta(days=30),
        amount=Decimal('5000.00'),
        status=ContractMilestone.PENDING,
        order=1,
        deliverables=['Wireframes', 'UI Mockups', 'Style Guide'],
    )
    return milestone


@pytest.fixture
def contract_milestone_completed(db, contract_fixed, admin_user):
    """Create a completed milestone."""
    from apps.contracts.models import ContractMilestone

    milestone = ContractMilestone.objects.create(
        contract=contract_fixed,
        title='Project Kickoff',
        description='Initial project setup and kickoff meeting.',
        due_date=date.today() - timedelta(days=7),
        amount=Decimal('2500.00'),
        status=ContractMilestone.COMPLETED,
        completed_at=timezone.now() - timedelta(days=3),
        completed_by=admin_user,
        order=0,
    )
    return milestone


# ============================================================================
# Invoice Fixtures
# ============================================================================

@pytest.fixture
def invoice_draft(db, client_company, contract_fixed):
    """Create a draft invoice."""
    from apps.invoicing.models import Invoice

    invoice = Invoice.objects.create(
        client=client_company,
        contract=contract_fixed,
        status=Invoice.DRAFT,
        issue_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        subtotal=Decimal('5000.00'),
        tax_rate=Decimal('8.00'),
        tax_amount=Decimal('400.00'),
        total=Decimal('5400.00'),
        currency='USD',
        notes='Thank you for your business!',
        terms='Payment due within 30 days.',
    )
    return invoice


@pytest.fixture
def invoice_sent(db, client_company, contract_fixed):
    """Create a sent invoice."""
    from apps.invoicing.models import Invoice

    invoice = Invoice.objects.create(
        client=client_company,
        contract=contract_fixed,
        status=Invoice.SENT,
        issue_date=date.today() - timedelta(days=5),
        due_date=date.today() + timedelta(days=25),
        subtotal=Decimal('7500.00'),
        tax_rate=Decimal('8.00'),
        tax_amount=Decimal('600.00'),
        total=Decimal('8100.00'),
        sent_at=timezone.now() - timedelta(days=5),
        currency='USD',
    )
    return invoice


@pytest.fixture
def invoice_paid(db, client_company, contract_fixed):
    """Create a paid invoice."""
    from apps.invoicing.models import Invoice

    invoice = Invoice.objects.create(
        client=client_company,
        contract=contract_fixed,
        status=Invoice.PAID,
        issue_date=date.today() - timedelta(days=30),
        due_date=date.today() - timedelta(days=5),
        subtotal=Decimal('2500.00'),
        tax_rate=Decimal('8.00'),
        tax_amount=Decimal('200.00'),
        total=Decimal('2700.00'),
        paid_amount=Decimal('2700.00'),
        paid_at=timezone.now() - timedelta(days=10),
        payment_method='card',
        payment_reference='pi_test123',
        currency='USD',
    )
    return invoice


@pytest.fixture
def invoice_overdue(db, client_individual):
    """Create an overdue invoice."""
    from apps.invoicing.models import Invoice

    invoice = Invoice.objects.create(
        client=client_individual,
        status=Invoice.OVERDUE,
        issue_date=date.today() - timedelta(days=45),
        due_date=date.today() - timedelta(days=15),
        subtotal=Decimal('1500.00'),
        tax_rate=Decimal('0.00'),
        tax_amount=Decimal('0.00'),
        total=Decimal('1500.00'),
        paid_amount=Decimal('0.00'),
        sent_at=timezone.now() - timedelta(days=45),
        currency='USD',
    )
    return invoice


@pytest.fixture
def invoice_item(db, invoice_draft):
    """Create an invoice item."""
    from apps.invoicing.models import InvoiceItem

    item = InvoiceItem.objects.create(
        invoice=invoice_draft,
        description='Web Development Services',
        quantity=Decimal('1.00'),
        unit_price=Decimal('5000.00'),
        amount=Decimal('5000.00'),
        order=0,
    )
    return item


# ============================================================================
# Payment Fixtures
# ============================================================================

@pytest.fixture
def payment_successful(db, invoice_paid):
    """Create a successful payment."""
    from apps.payments.models import Payment

    payment = Payment.objects.create(
        invoice=invoice_paid,
        amount=Decimal('2700.00'),
        currency='USD',
        payment_method=Payment.CARD,
        status=Payment.SUCCEEDED,
        payment_date=timezone.now() - timedelta(days=10),
        stripe_payment_intent_id='pi_test_successful',
        stripe_charge_id='ch_test_successful',
        card_last4='4242',
        card_brand='visa',
        receipt_url='https://stripe.com/receipts/test',
        receipt_sent=True,
    )
    return payment


@pytest.fixture
def payment_pending(db, invoice_sent):
    """Create a pending payment."""
    from apps.payments.models import Payment

    payment = Payment.objects.create(
        invoice=invoice_sent,
        amount=Decimal('8100.00'),
        currency='USD',
        payment_method=Payment.CARD,
        status=Payment.PENDING,
        payment_date=timezone.now(),
        stripe_payment_intent_id='pi_test_pending',
    )
    return payment


@pytest.fixture
def payment_failed(db, invoice_overdue):
    """Create a failed payment."""
    from apps.payments.models import Payment

    payment = Payment.objects.create(
        invoice=invoice_overdue,
        amount=Decimal('1500.00'),
        currency='USD',
        payment_method=Payment.CARD,
        status=Payment.FAILED,
        payment_date=timezone.now() - timedelta(days=10),
        failure_code='card_declined',
        failure_message='Your card was declined.',
    )
    return payment


@pytest.fixture
def payment_method_card(db, client_company):
    """Create a saved payment method."""
    from apps.payments.models import PaymentMethod, Payment

    pm = PaymentMethod.objects.create(
        client=client_company,
        type=Payment.CARD,
        is_default=True,
        card_last4='4242',
        card_brand='visa',
        card_exp_month=12,
        card_exp_year=2025,
        stripe_payment_method_id='pm_test_card',
        is_active=True,
    )
    return pm


# ============================================================================
# API Client Fixtures
# ============================================================================

@pytest.fixture
def api_client():
    """Create an API test client."""
    client = APIClient()
    client.defaults['HTTP_ORIGIN'] = 'http://testserver'
    client.defaults['SERVER_NAME'] = 'testserver'
    return client


@pytest.fixture
def authenticated_admin_client(api_client, admin_user):
    """Create an authenticated API client with admin user."""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def authenticated_manager_client(api_client, manager_user):
    """Create an authenticated API client with manager user."""
    api_client.force_authenticate(user=manager_user)
    return api_client


@pytest.fixture
def authenticated_contributor_client(api_client, contributor_user):
    """Create an authenticated API client with contributor user."""
    api_client.force_authenticate(user=contributor_user)
    return api_client


@pytest.fixture
def authenticated_client_user(api_client, client_user):
    """Create an authenticated API client with client user."""
    api_client.force_authenticate(user=client_user)
    return api_client


@pytest.fixture
def authenticated_superuser_client(api_client, superuser):
    """Create an authenticated API client with superuser."""
    api_client.force_authenticate(user=superuser)
    return api_client


# ============================================================================
# Security Test Fixtures
# ============================================================================

@pytest.fixture
def xss_payloads():
    """Common XSS attack payloads for testing."""
    return [
        '<script>alert("XSS")</script>',
        '<img src=x onerror=alert("XSS")>',
        '"><script>alert("XSS")</script>',
        "';alert('XSS');//",
        '<svg onload=alert("XSS")>',
        '{{constructor.constructor("alert(1)")()}}',
        '${7*7}',
        '<iframe src="javascript:alert(1)">',
        '<body onload=alert("XSS")>',
        '"><img src=x onerror=alert(1)>',
    ]


@pytest.fixture
def sql_injection_payloads():
    """Common SQL injection payloads for testing."""
    return [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "1' OR '1'='1' --",
        "1; SELECT * FROM users",
        "' UNION SELECT * FROM users --",
        "admin'--",
        "1' AND '1'='1",
        "' OR 1=1--",
        "'; EXEC xp_cmdshell('dir'); --",
        "1' ORDER BY 1--",
    ]


@pytest.fixture
def malicious_file_names():
    """Malicious file names for testing file upload security."""
    return [
        '../../../etc/passwd',
        '....//....//....//etc/passwd',
        'test.php',
        'test.php.jpg',
        'test.jsp',
        'test.aspx',
        '.htaccess',
        'shell.sh',
        'config.py',
        'test\x00.jpg',
    ]


@pytest.fixture
def rate_limit_data():
    """Data for rate limit testing."""
    return {
        'requests_per_second': 100,
        'burst_requests': 1000,
        'time_window': 60,  # seconds
    }


# ============================================================================
# Helper Fixtures
# ============================================================================

@pytest.fixture
def valid_password():
    """Return a valid password that meets requirements."""
    return 'SecureTestPass123!'


@pytest.fixture
def weak_passwords():
    """Return list of weak passwords for validation testing."""
    return [
        '123',
        'password',
        '12345678',
        'abcdefgh',
        'test',
        '',
    ]


@pytest.fixture
def sample_metadata():
    """Sample metadata for JSON fields."""
    return {
        'source': 'api',
        'version': '1.0',
        'custom_field': 'value',
        'nested': {
            'key': 'value',
        },
    }
