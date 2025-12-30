"""
Aureon SaaS Platform - Load Test Configuration
Configuration module for API endpoints, test data generators, and performance thresholds.
"""

import os
import random
import string
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


# ============================================================
# ENVIRONMENT CONFIGURATION
# ============================================================

class Environment(Enum):
    """Available test environments."""
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class EnvironmentConfig:
    """Configuration for a specific environment."""
    name: str
    base_url: str
    api_version: str = "v1"
    timeout: int = 30
    verify_ssl: bool = True


ENVIRONMENTS: Dict[Environment, EnvironmentConfig] = {
    Environment.LOCAL: EnvironmentConfig(
        name="Local Development",
        base_url="http://localhost:8000",
        timeout=10,
        verify_ssl=False,
    ),
    Environment.STAGING: EnvironmentConfig(
        name="Staging",
        base_url="https://staging.aureon.rhematek-solutions.com",
        timeout=30,
        verify_ssl=True,
    ),
    Environment.PRODUCTION: EnvironmentConfig(
        name="Production",
        base_url="https://aureon.rhematek-solutions.com",
        timeout=30,
        verify_ssl=True,
    ),
}


def get_environment() -> Environment:
    """Get current environment from environment variable."""
    env_name = os.getenv("LOAD_TEST_ENV", "local").lower()
    try:
        return Environment(env_name)
    except ValueError:
        return Environment.LOCAL


def get_config() -> EnvironmentConfig:
    """Get configuration for current environment."""
    return ENVIRONMENTS[get_environment()]


# ============================================================
# API ENDPOINTS
# ============================================================

class APIEndpoints:
    """Central repository of all API endpoints for load testing."""

    # Authentication endpoints
    AUTH_LOGIN = "/api/auth/login/"
    AUTH_LOGOUT = "/api/auth/logout/"
    AUTH_REGISTER = "/api/auth/register/"
    AUTH_REFRESH = "/api/auth/token/refresh/"
    AUTH_VERIFY = "/api/auth/token/verify/"
    AUTH_PASSWORD_RESET = "/api/auth/password/reset/"
    AUTH_PASSWORD_CHANGE = "/api/auth/password/change/"

    # User profile endpoints
    USER_PROFILE = "/api/users/me/"
    USER_SETTINGS = "/api/users/me/settings/"

    # Client management endpoints
    CLIENTS_LIST = "/api/clients/"
    CLIENTS_CREATE = "/api/clients/"
    CLIENT_DETAIL = "/api/clients/{id}/"
    CLIENT_UPDATE = "/api/clients/{id}/"
    CLIENT_DELETE = "/api/clients/{id}/"
    CLIENT_SEARCH = "/api/clients/search/"
    CLIENT_EXPORT = "/api/clients/export/"

    # Contract management endpoints
    CONTRACTS_LIST = "/api/contracts/"
    CONTRACTS_CREATE = "/api/contracts/"
    CONTRACT_DETAIL = "/api/contracts/{id}/"
    CONTRACT_UPDATE = "/api/contracts/{id}/"
    CONTRACT_DELETE = "/api/contracts/{id}/"
    CONTRACT_SIGN = "/api/contracts/{id}/sign/"
    CONTRACT_SEND = "/api/contracts/{id}/send/"
    CONTRACT_DOWNLOAD = "/api/contracts/{id}/download/"
    CONTRACT_TEMPLATES = "/api/contracts/templates/"
    CONTRACT_TEMPLATE_DETAIL = "/api/contracts/templates/{id}/"

    # Invoice management endpoints
    INVOICES_LIST = "/api/invoices/"
    INVOICES_CREATE = "/api/invoices/"
    INVOICE_DETAIL = "/api/invoices/{id}/"
    INVOICE_UPDATE = "/api/invoices/{id}/"
    INVOICE_DELETE = "/api/invoices/{id}/"
    INVOICE_SEND = "/api/invoices/{id}/send/"
    INVOICE_MARK_PAID = "/api/invoices/{id}/mark-paid/"
    INVOICE_DOWNLOAD = "/api/invoices/{id}/download/"
    INVOICE_PAYMENT_LINK = "/api/invoices/{id}/payment-link/"

    # Payment endpoints
    PAYMENTS_LIST = "/api/payments/"
    PAYMENT_DETAIL = "/api/payments/{id}/"
    PAYMENT_PROCESS = "/api/payments/process/"
    PAYMENT_METHODS = "/api/payments/methods/"
    PAYMENT_WEBHOOK = "/api/payments/webhook/"

    # Dashboard and analytics endpoints
    DASHBOARD_OVERVIEW = "/api/analytics/dashboard/"
    DASHBOARD_REVENUE = "/api/analytics/revenue/"
    DASHBOARD_CLIENTS = "/api/analytics/clients/"
    DASHBOARD_INVOICES = "/api/analytics/invoices/"
    DASHBOARD_CASH_FLOW = "/api/analytics/cash-flow/"
    ANALYTICS_REPORTS = "/api/analytics/reports/"
    ANALYTICS_EXPORT = "/api/analytics/export/"

    # Document management endpoints
    DOCUMENTS_LIST = "/api/documents/"
    DOCUMENTS_UPLOAD = "/api/documents/upload/"
    DOCUMENT_DETAIL = "/api/documents/{id}/"
    DOCUMENT_DOWNLOAD = "/api/documents/{id}/download/"
    DOCUMENT_DELETE = "/api/documents/{id}/"

    # Notification endpoints
    NOTIFICATIONS_LIST = "/api/notifications/"
    NOTIFICATION_MARK_READ = "/api/notifications/{id}/read/"
    NOTIFICATION_PREFERENCES = "/api/notifications/preferences/"

    # Health and system endpoints
    HEALTH_CHECK = "/api/health/"
    HEALTH_DETAILED = "/api/health/detailed/"
    API_STATUS = "/api/status/"

    # Public endpoints
    PUBLIC_HOME = "/"
    PUBLIC_PRICING = "/pricing/"
    PUBLIC_DOCS = "/api/docs/"
    PUBLIC_CLIENT_PORTAL = "/portal/{token}/"


# ============================================================
# PERFORMANCE THRESHOLDS
# ============================================================

@dataclass
class PerformanceThresholds:
    """Performance thresholds for different endpoint categories."""

    # Response time thresholds in milliseconds
    p50_ms: int = 100       # 50th percentile (median)
    p75_ms: int = 150       # 75th percentile
    p90_ms: int = 180       # 90th percentile
    p95_ms: int = 200       # 95th percentile (target)
    p99_ms: int = 500       # 99th percentile
    max_ms: int = 2000      # Maximum acceptable response time

    # Error thresholds
    max_error_rate: float = 0.01       # 1% max error rate
    max_timeout_rate: float = 0.005    # 0.5% max timeout rate

    # Throughput thresholds
    min_requests_per_second: float = 100.0  # Minimum RPS


# Endpoint-specific thresholds
ENDPOINT_THRESHOLDS: Dict[str, PerformanceThresholds] = {
    # Fast endpoints (simple queries)
    "health": PerformanceThresholds(p50_ms=20, p75_ms=30, p90_ms=50, p95_ms=75, p99_ms=100),
    "auth": PerformanceThresholds(p50_ms=50, p75_ms=75, p90_ms=100, p95_ms=150, p99_ms=300),

    # Standard CRUD endpoints
    "clients_read": PerformanceThresholds(p50_ms=50, p75_ms=100, p90_ms=150, p95_ms=200, p99_ms=400),
    "clients_write": PerformanceThresholds(p50_ms=100, p75_ms=150, p90_ms=200, p95_ms=300, p99_ms=600),
    "contracts_read": PerformanceThresholds(p50_ms=75, p75_ms=125, p90_ms=175, p95_ms=250, p99_ms=500),
    "contracts_write": PerformanceThresholds(p50_ms=150, p75_ms=200, p90_ms=300, p95_ms=400, p99_ms=800),
    "invoices_read": PerformanceThresholds(p50_ms=75, p75_ms=125, p90_ms=175, p95_ms=250, p99_ms=500),
    "invoices_write": PerformanceThresholds(p50_ms=150, p75_ms=200, p90_ms=300, p95_ms=400, p99_ms=800),

    # Complex endpoints (aggregations, reports)
    "analytics": PerformanceThresholds(p50_ms=200, p75_ms=300, p90_ms=400, p95_ms=500, p99_ms=1000),
    "reports": PerformanceThresholds(p50_ms=500, p75_ms=750, p90_ms=1000, p95_ms=1500, p99_ms=3000),

    # File operations
    "upload": PerformanceThresholds(p50_ms=500, p75_ms=750, p90_ms=1000, p95_ms=1500, p99_ms=3000),
    "download": PerformanceThresholds(p50_ms=200, p75_ms=300, p90_ms=500, p95_ms=750, p99_ms=1500),
}

# Default thresholds (p95 < 200ms target)
DEFAULT_THRESHOLDS = PerformanceThresholds()


def get_thresholds(endpoint_category: str) -> PerformanceThresholds:
    """Get performance thresholds for an endpoint category."""
    return ENDPOINT_THRESHOLDS.get(endpoint_category, DEFAULT_THRESHOLDS)


# ============================================================
# TEST DATA GENERATORS
# ============================================================

class TestDataGenerator:
    """Generator for realistic test data."""

    # Name components for generating realistic names
    FIRST_NAMES = [
        "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael",
        "Linda", "William", "Elizabeth", "David", "Barbara", "Richard", "Susan",
        "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen", "Christopher",
        "Nancy", "Daniel", "Lisa", "Matthew", "Betty", "Anthony", "Margaret",
    ]

    LAST_NAMES = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
        "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
        "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
        "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    ]

    COMPANY_SUFFIXES = [
        "Inc", "LLC", "Corp", "Co", "Ltd", "Group", "Solutions", "Technologies",
        "Services", "Consulting", "Partners", "Associates", "International",
    ]

    COMPANY_PREFIXES = [
        "Global", "Advanced", "Premier", "Elite", "Strategic", "Innovative",
        "Digital", "Modern", "Future", "Smart", "Dynamic", "Unified", "Apex",
    ]

    INDUSTRIES = [
        "Technology", "Healthcare", "Finance", "Retail", "Manufacturing",
        "Construction", "Education", "Marketing", "Legal", "Real Estate",
    ]

    CONTRACT_TYPES = [
        "Service Agreement", "Consulting Contract", "Project Agreement",
        "Retainer Agreement", "Master Service Agreement", "Statement of Work",
        "Non-Disclosure Agreement", "Employment Contract", "Freelance Agreement",
    ]

    PAYMENT_TERMS = ["Net 15", "Net 30", "Net 45", "Net 60", "Due on Receipt"]

    CURRENCIES = ["USD", "EUR", "GBP", "CAD", "AUD"]

    @staticmethod
    def random_string(length: int = 10) -> str:
        """Generate a random alphanumeric string."""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    @staticmethod
    def random_uuid() -> str:
        """Generate a random UUID."""
        return str(uuid.uuid4())

    @classmethod
    def email(cls, domain: str = "aureon-test.com") -> str:
        """Generate a random email address."""
        username = f"loadtest_{cls.random_string(8)}".lower()
        return f"{username}@{domain}"

    @classmethod
    def phone(cls, country_code: str = "+1") -> str:
        """Generate a random phone number."""
        area_code = random.randint(200, 999)
        exchange = random.randint(200, 999)
        subscriber = random.randint(1000, 9999)
        return f"{country_code}{area_code}{exchange}{subscriber}"

    @classmethod
    def name(cls) -> str:
        """Generate a random full name."""
        return f"{random.choice(cls.FIRST_NAMES)} {random.choice(cls.LAST_NAMES)}"

    @classmethod
    def first_name(cls) -> str:
        """Generate a random first name."""
        return random.choice(cls.FIRST_NAMES)

    @classmethod
    def last_name(cls) -> str:
        """Generate a random last name."""
        return random.choice(cls.LAST_NAMES)

    @classmethod
    def company_name(cls) -> str:
        """Generate a random company name."""
        patterns = [
            lambda: f"{random.choice(cls.LAST_NAMES)} {random.choice(cls.COMPANY_SUFFIXES)}",
            lambda: f"{random.choice(cls.COMPANY_PREFIXES)} {random.choice(cls.INDUSTRIES)} {random.choice(cls.COMPANY_SUFFIXES)}",
            lambda: f"{random.choice(cls.LAST_NAMES)} & {random.choice(cls.LAST_NAMES)} {random.choice(cls.COMPANY_SUFFIXES)}",
            lambda: f"{random.choice(cls.COMPANY_PREFIXES)} {random.choice(cls.LAST_NAMES)}",
        ]
        return random.choice(patterns)()

    @classmethod
    def address(cls) -> Dict[str, str]:
        """Generate a random address."""
        street_numbers = random.randint(100, 9999)
        street_names = ["Main St", "Oak Ave", "Maple Dr", "Park Blvd", "Center St",
                       "Washington Ave", "Liberty St", "Commerce Dr", "Industrial Way"]
        cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
                 "Philadelphia", "San Antonio", "San Diego", "Dallas", "Austin"]
        states = ["NY", "CA", "IL", "TX", "AZ", "PA", "TX", "CA", "TX", "TX"]

        idx = random.randint(0, len(cities) - 1)
        return {
            "street": f"{street_numbers} {random.choice(street_names)}",
            "city": cities[idx],
            "state": states[idx],
            "zip_code": f"{random.randint(10000, 99999)}",
            "country": "USA",
        }

    @classmethod
    def amount(cls, min_val: float = 100, max_val: float = 50000) -> float:
        """Generate a random monetary amount."""
        return round(random.uniform(min_val, max_val), 2)

    @classmethod
    def date_future(cls, days_ahead: int = 365) -> str:
        """Generate a random future date."""
        future = datetime.now() + timedelta(days=random.randint(1, days_ahead))
        return future.strftime("%Y-%m-%d")

    @classmethod
    def date_past(cls, days_back: int = 365) -> str:
        """Generate a random past date."""
        past = datetime.now() - timedelta(days=random.randint(1, days_back))
        return past.strftime("%Y-%m-%d")

    @classmethod
    def client_data(cls) -> Dict[str, Any]:
        """Generate complete client data for API calls."""
        address = cls.address()
        return {
            "name": cls.name(),
            "email": cls.email(),
            "phone": cls.phone(),
            "company": cls.company_name(),
            "address_line1": address["street"],
            "city": address["city"],
            "state": address["state"],
            "postal_code": address["zip_code"],
            "country": address["country"],
            "industry": random.choice(cls.INDUSTRIES),
            "notes": f"Load test client created at {datetime.now().isoformat()}",
            "tags": random.sample(["vip", "enterprise", "startup", "priority", "new"], k=random.randint(1, 3)),
        }

    @classmethod
    def contract_data(cls, client_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate complete contract data for API calls."""
        start_date = datetime.now()
        end_date = start_date + timedelta(days=random.randint(30, 365))

        return {
            "client_id": client_id or cls.random_uuid(),
            "title": f"{random.choice(cls.CONTRACT_TYPES)} - {cls.random_string(6)}",
            "description": f"Contract for {random.choice(cls.INDUSTRIES).lower()} services",
            "contract_type": random.choice(["fixed", "hourly", "retainer", "milestone"]),
            "value": cls.amount(5000, 100000),
            "currency": random.choice(cls.CURRENCIES),
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "payment_terms": random.choice(cls.PAYMENT_TERMS),
            "auto_renew": random.choice([True, False]),
            "milestones": [
                {
                    "name": f"Milestone {i}",
                    "amount": cls.amount(1000, 10000),
                    "due_date": cls.date_future(30 * (i + 1)),
                }
                for i in range(random.randint(1, 4))
            ],
        }

    @classmethod
    def invoice_data(cls, client_id: Optional[str] = None, contract_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate complete invoice data for API calls."""
        due_date = datetime.now() + timedelta(days=random.randint(15, 60))
        line_items = [
            {
                "description": f"Service Item {i + 1}",
                "quantity": random.randint(1, 10),
                "unit_price": cls.amount(100, 1000),
            }
            for i in range(random.randint(1, 5))
        ]

        subtotal = sum(item["quantity"] * item["unit_price"] for item in line_items)
        tax_rate = random.choice([0, 0.05, 0.07, 0.08, 0.10])

        return {
            "client_id": client_id or cls.random_uuid(),
            "contract_id": contract_id,
            "invoice_number": f"INV-{datetime.now().strftime('%Y%m%d')}-{cls.random_string(4).upper()}",
            "issue_date": datetime.now().strftime("%Y-%m-%d"),
            "due_date": due_date.strftime("%Y-%m-%d"),
            "line_items": line_items,
            "subtotal": round(subtotal, 2),
            "tax_rate": tax_rate,
            "tax_amount": round(subtotal * tax_rate, 2),
            "total": round(subtotal * (1 + tax_rate), 2),
            "currency": random.choice(cls.CURRENCIES),
            "payment_terms": random.choice(cls.PAYMENT_TERMS),
            "notes": "Thank you for your business.",
        }

    @classmethod
    def payment_data(cls, invoice_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate payment processing data."""
        return {
            "invoice_id": invoice_id or cls.random_uuid(),
            "amount": cls.amount(100, 10000),
            "currency": random.choice(cls.CURRENCIES),
            "payment_method": random.choice(["card", "bank_transfer", "ach"]),
            "payment_method_id": f"pm_{cls.random_string(24)}",
        }

    @classmethod
    def user_registration_data(cls) -> Dict[str, Any]:
        """Generate user registration data."""
        password = f"Test{cls.random_string(8)}!{random.randint(10, 99)}"
        return {
            "email": cls.email(),
            "password": password,
            "password_confirm": password,
            "first_name": cls.first_name(),
            "last_name": cls.last_name(),
            "company": cls.company_name(),
            "agree_terms": True,
        }

    @classmethod
    def document_upload_data(cls) -> Dict[str, Any]:
        """Generate document metadata for upload tests."""
        file_types = ["pdf", "docx", "xlsx", "png", "jpg"]
        file_type = random.choice(file_types)

        return {
            "name": f"document_{cls.random_string(8)}.{file_type}",
            "file_type": file_type,
            "category": random.choice(["contract", "invoice", "receipt", "attachment", "other"]),
            "description": f"Test document uploaded at {datetime.now().isoformat()}",
        }

    @classmethod
    def generate_test_file(cls, size_kb: int = 100) -> bytes:
        """Generate random file content for upload tests."""
        return os.urandom(size_kb * 1024)


# ============================================================
# TEST USER POOL
# ============================================================

@dataclass
class TestUser:
    """Test user credentials and metadata."""
    email: str
    password: str
    role: str = "user"
    token: Optional[str] = None
    refresh_token: Optional[str] = None


class TestUserPool:
    """Pool of test users for load testing."""

    # Pre-configured test users (create these in your test environment)
    DEFAULT_USERS = [
        TestUser(email="loadtest1@aureon-test.com", password="LoadTest123!Pass", role="admin"),
        TestUser(email="loadtest2@aureon-test.com", password="LoadTest123!Pass", role="user"),
        TestUser(email="loadtest3@aureon-test.com", password="LoadTest123!Pass", role="user"),
        TestUser(email="loadtest4@aureon-test.com", password="LoadTest123!Pass", role="user"),
        TestUser(email="loadtest5@aureon-test.com", password="LoadTest123!Pass", role="user"),
        TestUser(email="loadtest6@aureon-test.com", password="LoadTest123!Pass", role="user"),
        TestUser(email="loadtest7@aureon-test.com", password="LoadTest123!Pass", role="user"),
        TestUser(email="loadtest8@aureon-test.com", password="LoadTest123!Pass", role="user"),
        TestUser(email="loadtest9@aureon-test.com", password="LoadTest123!Pass", role="user"),
        TestUser(email="loadtest10@aureon-test.com", password="LoadTest123!Pass", role="user"),
    ]

    @classmethod
    def get_random_user(cls) -> TestUser:
        """Get a random test user from the pool."""
        return random.choice(cls.DEFAULT_USERS)

    @classmethod
    def get_admin_user(cls) -> TestUser:
        """Get an admin test user."""
        admin_users = [u for u in cls.DEFAULT_USERS if u.role == "admin"]
        return random.choice(admin_users) if admin_users else cls.DEFAULT_USERS[0]

    @classmethod
    def get_credentials(cls) -> Dict[str, str]:
        """Get random user credentials for login."""
        user = cls.get_random_user()
        return {"email": user.email, "password": user.password}


# ============================================================
# LOAD TEST PARAMETERS
# ============================================================

@dataclass
class LoadTestParams:
    """Parameters for load test execution."""

    # User configuration
    total_users: int = 500
    spawn_rate: int = 10  # Users per second

    # Duration configuration
    warmup_duration: int = 60       # Seconds
    test_duration: int = 300        # Seconds
    cooldown_duration: int = 60     # Seconds

    # Wait times between requests (seconds)
    min_wait: float = 1.0
    max_wait: float = 3.0

    # Task weights (relative frequency)
    weights: Dict[str, int] = field(default_factory=lambda: {
        "health_check": 10,
        "login": 3,
        "list_clients": 8,
        "create_client": 2,
        "get_client": 5,
        "list_contracts": 6,
        "create_contract": 1,
        "sign_contract": 1,
        "list_invoices": 6,
        "create_invoice": 2,
        "payment_flow": 1,
        "dashboard": 4,
        "analytics": 2,
        "file_upload": 1,
        "file_download": 2,
    })

    # Retry configuration
    max_retries: int = 3
    retry_delay: float = 1.0

    # Connection pool settings
    connection_timeout: int = 30
    read_timeout: int = 60


# Preset configurations for different scenarios
LOAD_CONFIGS = {
    "smoke": LoadTestParams(total_users=10, spawn_rate=1, test_duration=60),
    "normal": LoadTestParams(total_users=100, spawn_rate=10, test_duration=300),
    "peak": LoadTestParams(total_users=500, spawn_rate=20, test_duration=600),
    "stress": LoadTestParams(total_users=1000, spawn_rate=50, test_duration=600),
    "spike": LoadTestParams(total_users=500, spawn_rate=100, test_duration=180),
    "soak": LoadTestParams(total_users=200, spawn_rate=5, test_duration=3600),
}


def get_load_config(scenario: str) -> LoadTestParams:
    """Get load configuration for a specific scenario."""
    return LOAD_CONFIGS.get(scenario, LOAD_CONFIGS["normal"])
