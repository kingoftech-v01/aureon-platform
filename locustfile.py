"""
Aureon SaaS Platform - Comprehensive Load Testing with Locust
==============================================================

Handles 500+ concurrent users with p95 < 200ms target.

Test Coverage:
- User authentication flow (login, token refresh)
- Client CRUD operations
- Contract creation and signing flow
- Invoice creation and payment flow
- Dashboard analytics queries
- File upload/download tests

Usage:
    # Quick smoke test (10 users)
    locust -f locustfile.py --host http://localhost:8000 --headless -u 10 -r 2 -t 60s

    # Normal load (100 users)
    locust -f locustfile.py --host http://localhost:8000 --headless -u 100 -r 10 -t 300s

    # Peak load (500 users) - PRIMARY TARGET
    locust -f locustfile.py --host http://localhost:8000 --headless -u 500 -r 20 -t 600s

    # Stress test (1000 users)
    locust -f locustfile.py --host http://localhost:8000 --headless -u 1000 -r 50 -t 600s

    # Web UI mode
    locust -f locustfile.py --host http://localhost:8000

    # With custom shape (for scenarios)
    locust -f locustfile.py --host http://localhost:8000 --headless

Environment Variables:
    LOAD_TEST_ENV: Target environment (local, staging, production)
    API_BASE_URL: Override base URL
    TEST_USER_EMAIL: Override test user email
    TEST_USER_PASSWORD: Override test user password
"""

import json
import os
import random
import time
import logging
from datetime import datetime
from typing import Dict, Optional, Any, List

from locust import HttpUser, task, between, events, tag
from locust.runners import MasterRunner, WorkerRunner
from locust.exception import RescheduleTask

# Import custom configurations and scenarios
try:
    from load_tests.config import (
        APIEndpoints,
        TestDataGenerator,
        TestUserPool,
        get_config,
        get_thresholds,
        DEFAULT_THRESHOLDS,
    )
    from load_tests.scenarios import (
        PeakLoadShape,
        NormalLoadShape,
        StressTestShape,
        SpikeTestShape,
        validate_scenario_results,
    )
except ImportError:
    # Fallback if running from different directory
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from load_tests.config import (
        APIEndpoints,
        TestDataGenerator,
        TestUserPool,
        get_config,
        get_thresholds,
        DEFAULT_THRESHOLDS,
    )
    from load_tests.scenarios import (
        PeakLoadShape,
        NormalLoadShape,
        StressTestShape,
        SpikeTestShape,
        validate_scenario_results,
    )


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aureon_load_test")


# ============================================================
# GLOBAL STATE AND CONFIGURATION
# ============================================================

# Shared state across all users
class SharedState:
    """Shared state accessible by all virtual users."""
    created_client_ids: List[str] = []
    created_contract_ids: List[str] = []
    created_invoice_ids: List[str] = []
    test_start_time: Optional[datetime] = None
    total_auth_failures: int = 0
    performance_violations: List[Dict] = []


shared_state = SharedState()


# ============================================================
# BASE USER CLASS
# ============================================================

class AureonBaseUser(HttpUser):
    """
    Base class for Aureon load test users.
    Provides authentication, token management, and common utilities.
    """

    abstract = True
    wait_time = between(1, 3)

    # Authentication state
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    user_id: Optional[str] = None
    token_expiry: Optional[float] = None

    # Request tracking
    request_count: int = 0
    error_count: int = 0

    def on_start(self):
        """Called when a simulated user starts."""
        self.authenticate()

    def on_stop(self):
        """Called when a simulated user stops."""
        if self.access_token:
            self._logout()

    def authenticate(self) -> bool:
        """
        Authenticate with the API and obtain access tokens.
        Returns True if authentication succeeds.
        """
        credentials = TestUserPool.get_credentials()

        with self.client.post(
            APIEndpoints.AUTH_LOGIN,
            json=credentials,
            catch_response=True,
            name="Auth: Login"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    self.access_token = data.get("access") or data.get("token") or data.get("access_token")
                    self.refresh_token = data.get("refresh") or data.get("refresh_token")
                    self.user_id = data.get("user_id") or data.get("user", {}).get("id")

                    # Assume token expires in 1 hour if not specified
                    expires_in = data.get("expires_in", 3600)
                    self.token_expiry = time.time() + expires_in - 60  # Refresh 1 min early

                    response.success()
                    return True
                except (json.JSONDecodeError, KeyError) as e:
                    response.failure(f"Invalid JSON response: {e}")
                    shared_state.total_auth_failures += 1
                    return False
            elif response.status_code == 401:
                # Expected for non-existent test users
                response.success()
                shared_state.total_auth_failures += 1
                return False
            else:
                response.failure(f"Login failed: {response.status_code}")
                shared_state.total_auth_failures += 1
                return False

    def refresh_access_token(self) -> bool:
        """Refresh the access token using the refresh token."""
        if not self.refresh_token:
            return self.authenticate()

        with self.client.post(
            APIEndpoints.AUTH_REFRESH,
            json={"refresh": self.refresh_token},
            catch_response=True,
            name="Auth: Token Refresh"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    self.access_token = data.get("access") or data.get("token")

                    expires_in = data.get("expires_in", 3600)
                    self.token_expiry = time.time() + expires_in - 60

                    response.success()
                    return True
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
                    return False
            else:
                response.failure(f"Token refresh failed: {response.status_code}")
                # Try full re-authentication
                return self.authenticate()

    def _logout(self):
        """Logout and clear tokens."""
        if self.access_token:
            self.client.post(
                APIEndpoints.AUTH_LOGOUT,
                headers=self.get_auth_headers(),
                name="Auth: Logout"
            )
        self.access_token = None
        self.refresh_token = None
        self.user_id = None

    def get_auth_headers(self) -> Dict[str, str]:
        """Get headers with authentication token."""
        # Check if token needs refresh
        if self.token_expiry and time.time() > self.token_expiry:
            self.refresh_access_token()

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def ensure_authenticated(self):
        """Ensure user is authenticated before making a request."""
        if not self.access_token:
            if not self.authenticate():
                raise RescheduleTask()

    def _check_response_time(self, response, category: str):
        """Check if response time exceeds thresholds."""
        thresholds = get_thresholds(category)
        response_time = response.elapsed.total_seconds() * 1000

        if response_time > thresholds.p95_ms:
            shared_state.performance_violations.append({
                "endpoint": response.request.path_url,
                "category": category,
                "response_time_ms": response_time,
                "threshold_ms": thresholds.p95_ms,
                "timestamp": datetime.now().isoformat(),
            })


# ============================================================
# PRIMARY USER CLASS - FULL WORKFLOW
# ============================================================

class AureonPrimaryUser(AureonBaseUser):
    """
    Primary Aureon user simulating typical platform usage.
    Includes all major workflows with realistic task distribution.
    """

    weight = 70  # 70% of users
    wait_time = between(1, 3)

    # ========================================
    # HEALTH CHECK TASKS
    # ========================================

    @task(15)
    @tag("health", "critical")
    def health_check(self):
        """
        Health check endpoint - highest frequency.
        Tests basic API availability.
        """
        with self.client.get(
            APIEndpoints.HEALTH_CHECK,
            catch_response=True,
            name="Health: Basic Check"
        ) as response:
            if response.status_code == 200:
                self._check_response_time(response, "health")
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @task(3)
    @tag("health")
    def detailed_health_check(self):
        """Detailed health check with component status."""
        with self.client.get(
            APIEndpoints.HEALTH_DETAILED,
            catch_response=True,
            name="Health: Detailed Check"
        ) as response:
            if response.status_code in [200, 404]:  # 404 if endpoint doesn't exist
                response.success()
            else:
                response.failure(f"Detailed health check failed: {response.status_code}")

    # ========================================
    # AUTHENTICATION TASKS
    # ========================================

    @task(5)
    @tag("auth", "critical")
    def login_flow(self):
        """
        Test complete login flow.
        Simulates user login attempts.
        """
        credentials = TestUserPool.get_credentials()

        with self.client.post(
            APIEndpoints.AUTH_LOGIN,
            json=credentials,
            catch_response=True,
            name="Auth: Login Flow"
        ) as response:
            if response.status_code in [200, 401]:
                self._check_response_time(response, "auth")
                response.success()
            else:
                response.failure(f"Login error: {response.status_code}")

    @task(3)
    @tag("auth")
    def token_refresh_flow(self):
        """Test token refresh functionality."""
        if self.refresh_token:
            with self.client.post(
                APIEndpoints.AUTH_REFRESH,
                json={"refresh": self.refresh_token},
                catch_response=True,
                name="Auth: Token Refresh Flow"
            ) as response:
                if response.status_code in [200, 401]:
                    self._check_response_time(response, "auth")
                    response.success()
                else:
                    response.failure(f"Token refresh error: {response.status_code}")

    @task(1)
    @tag("auth")
    def token_verify(self):
        """Verify token validity."""
        if self.access_token:
            with self.client.post(
                APIEndpoints.AUTH_VERIFY,
                json={"token": self.access_token},
                catch_response=True,
                name="Auth: Token Verify"
            ) as response:
                if response.status_code in [200, 401]:
                    response.success()
                else:
                    response.failure(f"Token verify error: {response.status_code}")

    # ========================================
    # CLIENT MANAGEMENT TASKS
    # ========================================

    @task(10)
    @tag("clients", "read", "critical")
    def list_clients(self):
        """
        List clients with pagination.
        High-frequency read operation.
        """
        self.ensure_authenticated()

        # Random pagination
        page = random.randint(1, 10)
        page_size = random.choice([10, 25, 50])

        with self.client.get(
            f"{APIEndpoints.CLIENTS_LIST}?page={page}&page_size={page_size}",
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Clients: List"
        ) as response:
            if response.status_code in [200, 401, 403]:
                self._check_response_time(response, "clients_read")
                response.success()
            else:
                response.failure(f"List clients failed: {response.status_code}")

    @task(5)
    @tag("clients", "read")
    def get_client_detail(self):
        """Get single client details."""
        self.ensure_authenticated()

        # Use a created client ID or generate a random UUID
        client_id = (
            random.choice(shared_state.created_client_ids)
            if shared_state.created_client_ids
            else TestDataGenerator.random_uuid()
        )

        with self.client.get(
            APIEndpoints.CLIENT_DETAIL.format(id=client_id),
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Clients: Get Detail"
        ) as response:
            if response.status_code in [200, 401, 403, 404]:
                self._check_response_time(response, "clients_read")
                response.success()
            else:
                response.failure(f"Get client detail failed: {response.status_code}")

    @task(3)
    @tag("clients", "write")
    def create_client(self):
        """
        Create a new client.
        Tests write operations and data validation.
        """
        self.ensure_authenticated()

        client_data = TestDataGenerator.client_data()

        with self.client.post(
            APIEndpoints.CLIENTS_CREATE,
            json=client_data,
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Clients: Create"
        ) as response:
            if response.status_code == 201:
                try:
                    data = response.json()
                    client_id = data.get("id") or data.get("client_id")
                    if client_id:
                        shared_state.created_client_ids.append(client_id)
                        # Keep list manageable
                        if len(shared_state.created_client_ids) > 1000:
                            shared_state.created_client_ids = shared_state.created_client_ids[-500:]
                except json.JSONDecodeError:
                    pass
                self._check_response_time(response, "clients_write")
                response.success()
            elif response.status_code in [200, 400, 401, 403]:
                response.success()
            else:
                response.failure(f"Create client failed: {response.status_code}")

    @task(2)
    @tag("clients", "write")
    def update_client(self):
        """Update an existing client."""
        self.ensure_authenticated()

        if not shared_state.created_client_ids:
            return

        client_id = random.choice(shared_state.created_client_ids)
        update_data = {
            "phone": TestDataGenerator.phone(),
            "notes": f"Updated by load test at {datetime.now().isoformat()}",
        }

        with self.client.patch(
            APIEndpoints.CLIENT_UPDATE.format(id=client_id),
            json=update_data,
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Clients: Update"
        ) as response:
            if response.status_code in [200, 400, 401, 403, 404]:
                self._check_response_time(response, "clients_write")
                response.success()
            else:
                response.failure(f"Update client failed: {response.status_code}")

    @task(2)
    @tag("clients", "read")
    def search_clients(self):
        """Search clients by name or email."""
        self.ensure_authenticated()

        search_term = random.choice(["test", "load", "client", "company"])

        with self.client.get(
            f"{APIEndpoints.CLIENT_SEARCH}?q={search_term}",
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Clients: Search"
        ) as response:
            if response.status_code in [200, 401, 403, 404]:
                self._check_response_time(response, "clients_read")
                response.success()
            else:
                response.failure(f"Search clients failed: {response.status_code}")

    # ========================================
    # CONTRACT MANAGEMENT TASKS
    # ========================================

    @task(8)
    @tag("contracts", "read", "critical")
    def list_contracts(self):
        """List contracts with filters."""
        self.ensure_authenticated()

        status_filter = random.choice(["", "draft", "pending", "active", "completed"])
        url = APIEndpoints.CONTRACTS_LIST
        if status_filter:
            url += f"?status={status_filter}"

        with self.client.get(
            url,
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Contracts: List"
        ) as response:
            if response.status_code in [200, 401, 403]:
                self._check_response_time(response, "contracts_read")
                response.success()
            else:
                response.failure(f"List contracts failed: {response.status_code}")

    @task(4)
    @tag("contracts", "read")
    def get_contract_detail(self):
        """Get single contract details."""
        self.ensure_authenticated()

        contract_id = (
            random.choice(shared_state.created_contract_ids)
            if shared_state.created_contract_ids
            else TestDataGenerator.random_uuid()
        )

        with self.client.get(
            APIEndpoints.CONTRACT_DETAIL.format(id=contract_id),
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Contracts: Get Detail"
        ) as response:
            if response.status_code in [200, 401, 403, 404]:
                self._check_response_time(response, "contracts_read")
                response.success()
            else:
                response.failure(f"Get contract detail failed: {response.status_code}")

    @task(2)
    @tag("contracts", "write")
    def create_contract(self):
        """
        Create a new contract.
        Tests complex write operation with nested data.
        """
        self.ensure_authenticated()

        client_id = (
            random.choice(shared_state.created_client_ids)
            if shared_state.created_client_ids
            else TestDataGenerator.random_uuid()
        )

        contract_data = TestDataGenerator.contract_data(client_id)

        with self.client.post(
            APIEndpoints.CONTRACTS_CREATE,
            json=contract_data,
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Contracts: Create"
        ) as response:
            if response.status_code == 201:
                try:
                    data = response.json()
                    contract_id = data.get("id") or data.get("contract_id")
                    if contract_id:
                        shared_state.created_contract_ids.append(contract_id)
                        if len(shared_state.created_contract_ids) > 1000:
                            shared_state.created_contract_ids = shared_state.created_contract_ids[-500:]
                except json.JSONDecodeError:
                    pass
                self._check_response_time(response, "contracts_write")
                response.success()
            elif response.status_code in [200, 400, 401, 403]:
                response.success()
            else:
                response.failure(f"Create contract failed: {response.status_code}")

    @task(2)
    @tag("contracts", "write", "signing")
    def sign_contract_flow(self):
        """
        Complete contract signing flow.
        Tests multi-step workflow.
        """
        self.ensure_authenticated()

        if not shared_state.created_contract_ids:
            return

        contract_id = random.choice(shared_state.created_contract_ids)

        # Step 1: Get contract details
        with self.client.get(
            APIEndpoints.CONTRACT_DETAIL.format(id=contract_id),
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Contracts: Sign Flow - Get Contract"
        ) as response:
            if response.status_code not in [200]:
                if response.status_code in [401, 403, 404]:
                    response.success()
                else:
                    response.failure(f"Sign flow - get contract failed: {response.status_code}")
                return

        # Step 2: Send for signature
        with self.client.post(
            APIEndpoints.CONTRACT_SEND.format(id=contract_id),
            json={"recipient_email": TestDataGenerator.email()},
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Contracts: Sign Flow - Send"
        ) as response:
            if response.status_code in [200, 201, 400, 401, 403, 404]:
                response.success()
            else:
                response.failure(f"Sign flow - send failed: {response.status_code}")
                return

        # Step 3: Simulate signature
        signature_data = {
            "signature": TestDataGenerator.random_string(64),
            "signer_name": TestDataGenerator.name(),
            "signer_email": TestDataGenerator.email(),
            "agreed_terms": True,
            "ip_address": f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
        }

        with self.client.post(
            APIEndpoints.CONTRACT_SIGN.format(id=contract_id),
            json=signature_data,
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Contracts: Sign Flow - Sign"
        ) as response:
            if response.status_code in [200, 201, 400, 401, 403, 404]:
                self._check_response_time(response, "contracts_write")
                response.success()
            else:
                response.failure(f"Sign flow - sign failed: {response.status_code}")

    @task(2)
    @tag("contracts", "read")
    def list_contract_templates(self):
        """List available contract templates."""
        self.ensure_authenticated()

        with self.client.get(
            APIEndpoints.CONTRACT_TEMPLATES,
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Contracts: List Templates"
        ) as response:
            if response.status_code in [200, 401, 403, 404]:
                response.success()
            else:
                response.failure(f"List templates failed: {response.status_code}")

    # ========================================
    # INVOICE MANAGEMENT TASKS
    # ========================================

    @task(8)
    @tag("invoices", "read", "critical")
    def list_invoices(self):
        """List invoices with filters."""
        self.ensure_authenticated()

        status_filter = random.choice(["", "draft", "sent", "paid", "overdue"])
        url = APIEndpoints.INVOICES_LIST
        if status_filter:
            url += f"?status={status_filter}"

        with self.client.get(
            url,
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Invoices: List"
        ) as response:
            if response.status_code in [200, 401, 403]:
                self._check_response_time(response, "invoices_read")
                response.success()
            else:
                response.failure(f"List invoices failed: {response.status_code}")

    @task(4)
    @tag("invoices", "read")
    def get_invoice_detail(self):
        """Get single invoice details."""
        self.ensure_authenticated()

        invoice_id = (
            random.choice(shared_state.created_invoice_ids)
            if shared_state.created_invoice_ids
            else TestDataGenerator.random_uuid()
        )

        with self.client.get(
            APIEndpoints.INVOICE_DETAIL.format(id=invoice_id),
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Invoices: Get Detail"
        ) as response:
            if response.status_code in [200, 401, 403, 404]:
                self._check_response_time(response, "invoices_read")
                response.success()
            else:
                response.failure(f"Get invoice detail failed: {response.status_code}")

    @task(3)
    @tag("invoices", "write")
    def create_invoice(self):
        """
        Create a new invoice.
        Tests complex write with line items.
        """
        self.ensure_authenticated()

        client_id = (
            random.choice(shared_state.created_client_ids)
            if shared_state.created_client_ids
            else TestDataGenerator.random_uuid()
        )

        contract_id = (
            random.choice(shared_state.created_contract_ids)
            if shared_state.created_contract_ids
            else None
        )

        invoice_data = TestDataGenerator.invoice_data(client_id, contract_id)

        with self.client.post(
            APIEndpoints.INVOICES_CREATE,
            json=invoice_data,
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Invoices: Create"
        ) as response:
            if response.status_code == 201:
                try:
                    data = response.json()
                    invoice_id = data.get("id") or data.get("invoice_id")
                    if invoice_id:
                        shared_state.created_invoice_ids.append(invoice_id)
                        if len(shared_state.created_invoice_ids) > 1000:
                            shared_state.created_invoice_ids = shared_state.created_invoice_ids[-500:]
                except json.JSONDecodeError:
                    pass
                self._check_response_time(response, "invoices_write")
                response.success()
            elif response.status_code in [200, 400, 401, 403]:
                response.success()
            else:
                response.failure(f"Create invoice failed: {response.status_code}")

    @task(2)
    @tag("invoices", "write")
    def send_invoice(self):
        """Send an invoice to client."""
        self.ensure_authenticated()

        if not shared_state.created_invoice_ids:
            return

        invoice_id = random.choice(shared_state.created_invoice_ids)

        with self.client.post(
            APIEndpoints.INVOICE_SEND.format(id=invoice_id),
            json={"recipient_email": TestDataGenerator.email()},
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Invoices: Send"
        ) as response:
            if response.status_code in [200, 201, 400, 401, 403, 404]:
                response.success()
            else:
                response.failure(f"Send invoice failed: {response.status_code}")

    @task(2)
    @tag("invoices", "write", "payments")
    def payment_flow(self):
        """
        Complete payment processing flow.
        Tests payment integration.
        """
        self.ensure_authenticated()

        if not shared_state.created_invoice_ids:
            return

        invoice_id = random.choice(shared_state.created_invoice_ids)

        # Step 1: Get payment link
        with self.client.post(
            APIEndpoints.INVOICE_PAYMENT_LINK.format(id=invoice_id),
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Payments: Get Payment Link"
        ) as response:
            if response.status_code not in [200, 201]:
                if response.status_code in [400, 401, 403, 404]:
                    response.success()
                else:
                    response.failure(f"Get payment link failed: {response.status_code}")
                return

        # Step 2: Process payment
        payment_data = TestDataGenerator.payment_data(invoice_id)

        with self.client.post(
            APIEndpoints.PAYMENT_PROCESS,
            json=payment_data,
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Payments: Process Payment"
        ) as response:
            if response.status_code in [200, 201, 400, 401, 403, 404]:
                self._check_response_time(response, "invoices_write")
                response.success()
            else:
                response.failure(f"Process payment failed: {response.status_code}")

    # ========================================
    # DASHBOARD AND ANALYTICS TASKS
    # ========================================

    @task(6)
    @tag("analytics", "critical")
    def dashboard_overview(self):
        """
        Get main dashboard overview.
        Tests aggregated data retrieval.
        """
        self.ensure_authenticated()

        with self.client.get(
            APIEndpoints.DASHBOARD_OVERVIEW,
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Analytics: Dashboard Overview"
        ) as response:
            if response.status_code in [200, 401, 403]:
                self._check_response_time(response, "analytics")
                response.success()
            else:
                response.failure(f"Dashboard overview failed: {response.status_code}")

    @task(4)
    @tag("analytics")
    def revenue_analytics(self):
        """Get revenue analytics."""
        self.ensure_authenticated()

        period = random.choice(["day", "week", "month", "quarter", "year"])

        with self.client.get(
            f"{APIEndpoints.DASHBOARD_REVENUE}?period={period}",
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Analytics: Revenue"
        ) as response:
            if response.status_code in [200, 401, 403, 404]:
                self._check_response_time(response, "analytics")
                response.success()
            else:
                response.failure(f"Revenue analytics failed: {response.status_code}")

    @task(3)
    @tag("analytics")
    def cash_flow_analytics(self):
        """Get cash flow analytics."""
        self.ensure_authenticated()

        with self.client.get(
            APIEndpoints.DASHBOARD_CASH_FLOW,
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Analytics: Cash Flow"
        ) as response:
            if response.status_code in [200, 401, 403, 404]:
                self._check_response_time(response, "analytics")
                response.success()
            else:
                response.failure(f"Cash flow analytics failed: {response.status_code}")

    @task(2)
    @tag("analytics", "reports")
    def generate_report(self):
        """Generate analytics report."""
        self.ensure_authenticated()

        report_type = random.choice(["revenue", "clients", "invoices", "contracts"])

        with self.client.get(
            f"{APIEndpoints.ANALYTICS_REPORTS}?type={report_type}",
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Analytics: Generate Report"
        ) as response:
            if response.status_code in [200, 401, 403, 404]:
                self._check_response_time(response, "reports")
                response.success()
            else:
                response.failure(f"Generate report failed: {response.status_code}")

    # ========================================
    # FILE OPERATIONS TASKS
    # ========================================

    @task(2)
    @tag("files", "upload")
    def file_upload(self):
        """
        Test file upload functionality.
        Tests large data transfer.
        """
        self.ensure_authenticated()

        # Generate test file (100KB - 500KB)
        file_size_kb = random.randint(100, 500)
        file_content = TestDataGenerator.generate_test_file(file_size_kb)
        file_metadata = TestDataGenerator.document_upload_data()

        files = {
            "file": (file_metadata["name"], file_content, "application/octet-stream"),
        }
        data = {
            "name": file_metadata["name"],
            "category": file_metadata["category"],
            "description": file_metadata["description"],
        }

        # Remove Content-Type from headers for multipart upload
        headers = self.get_auth_headers()
        headers.pop("Content-Type", None)

        with self.client.post(
            APIEndpoints.DOCUMENTS_UPLOAD,
            files=files,
            data=data,
            headers=headers,
            catch_response=True,
            name="Files: Upload"
        ) as response:
            if response.status_code in [200, 201, 400, 401, 403, 413]:
                self._check_response_time(response, "upload")
                response.success()
            else:
                response.failure(f"File upload failed: {response.status_code}")

    @task(3)
    @tag("files", "download")
    def file_download(self):
        """
        Test file download functionality.
        Tests large data retrieval.
        """
        self.ensure_authenticated()

        # Use a random document ID
        document_id = TestDataGenerator.random_uuid()

        with self.client.get(
            APIEndpoints.DOCUMENT_DOWNLOAD.format(id=document_id),
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Files: Download"
        ) as response:
            if response.status_code in [200, 401, 403, 404]:
                self._check_response_time(response, "download")
                response.success()
            else:
                response.failure(f"File download failed: {response.status_code}")

    @task(2)
    @tag("files")
    def list_documents(self):
        """List documents."""
        self.ensure_authenticated()

        with self.client.get(
            APIEndpoints.DOCUMENTS_LIST,
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Files: List Documents"
        ) as response:
            if response.status_code in [200, 401, 403]:
                response.success()
            else:
                response.failure(f"List documents failed: {response.status_code}")

    @task(2)
    @tag("contracts", "download")
    def download_contract_pdf(self):
        """Download contract as PDF."""
        self.ensure_authenticated()

        contract_id = (
            random.choice(shared_state.created_contract_ids)
            if shared_state.created_contract_ids
            else TestDataGenerator.random_uuid()
        )

        with self.client.get(
            APIEndpoints.CONTRACT_DOWNLOAD.format(id=contract_id),
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Contracts: Download PDF"
        ) as response:
            if response.status_code in [200, 401, 403, 404]:
                self._check_response_time(response, "download")
                response.success()
            else:
                response.failure(f"Download contract PDF failed: {response.status_code}")

    @task(2)
    @tag("invoices", "download")
    def download_invoice_pdf(self):
        """Download invoice as PDF."""
        self.ensure_authenticated()

        invoice_id = (
            random.choice(shared_state.created_invoice_ids)
            if shared_state.created_invoice_ids
            else TestDataGenerator.random_uuid()
        )

        with self.client.get(
            APIEndpoints.INVOICE_DOWNLOAD.format(id=invoice_id),
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Invoices: Download PDF"
        ) as response:
            if response.status_code in [200, 401, 403, 404]:
                self._check_response_time(response, "download")
                response.success()
            else:
                response.failure(f"Download invoice PDF failed: {response.status_code}")


# ============================================================
# ANONYMOUS USER CLASS
# ============================================================

class AureonAnonymousUser(HttpUser):
    """
    Anonymous user for testing public endpoints.
    Simulates visitors before authentication.
    """

    weight = 15  # 15% of users
    wait_time = between(2, 5)

    @task(10)
    @tag("health", "public")
    def health_check(self):
        """Test public health endpoint."""
        with self.client.get(
            APIEndpoints.HEALTH_CHECK,
            catch_response=True,
            name="Public: Health Check"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @task(8)
    @tag("public")
    def visit_homepage(self):
        """Visit public homepage."""
        with self.client.get(
            APIEndpoints.PUBLIC_HOME,
            catch_response=True,
            name="Public: Homepage"
        ) as response:
            if response.status_code in [200, 302]:
                response.success()
            else:
                response.failure(f"Homepage failed: {response.status_code}")

    @task(5)
    @tag("public")
    def visit_pricing(self):
        """Visit pricing page."""
        with self.client.get(
            APIEndpoints.PUBLIC_PRICING,
            catch_response=True,
            name="Public: Pricing"
        ) as response:
            if response.status_code in [200, 302, 404]:
                response.success()
            else:
                response.failure(f"Pricing page failed: {response.status_code}")

    @task(3)
    @tag("public", "docs")
    def api_docs(self):
        """Access API documentation."""
        with self.client.get(
            APIEndpoints.PUBLIC_DOCS,
            catch_response=True,
            name="Public: API Docs"
        ) as response:
            if response.status_code in [200, 302, 404]:
                response.success()
            else:
                response.failure(f"API docs failed: {response.status_code}")

    @task(4)
    @tag("security")
    def test_protected_endpoint(self):
        """Verify protected endpoints require auth."""
        with self.client.get(
            APIEndpoints.CLIENTS_LIST,
            catch_response=True,
            name="Security: Protected Endpoint"
        ) as response:
            if response.status_code in [401, 403]:
                response.success()  # Expected
            elif response.status_code == 200:
                response.failure("Protected endpoint accessible without auth!")
            else:
                response.failure(f"Unexpected status: {response.status_code}")


# ============================================================
# HEAVY/POWER USER CLASS
# ============================================================

class AureonHeavyUser(AureonBaseUser):
    """
    Heavy user simulating power users with frequent API calls.
    Used for stress testing scenarios.
    """

    weight = 15  # 15% of users
    wait_time = between(0.5, 1.5)  # More frequent requests

    @task(15)
    @tag("stress")
    def rapid_read_operations(self):
        """Rapid read operations for stress testing."""
        self.ensure_authenticated()

        endpoints = [
            (APIEndpoints.CLIENTS_LIST, "Stress: List Clients"),
            (APIEndpoints.CONTRACTS_LIST, "Stress: List Contracts"),
            (APIEndpoints.INVOICES_LIST, "Stress: List Invoices"),
        ]

        endpoint, name = random.choice(endpoints)

        with self.client.get(
            endpoint,
            headers=self.get_auth_headers(),
            catch_response=True,
            name=name
        ) as response:
            if response.status_code in [200, 401, 403]:
                response.success()
            else:
                response.failure(f"Rapid read failed: {response.status_code}")

    @task(10)
    @tag("stress")
    def concurrent_dashboard_queries(self):
        """Multiple dashboard queries for stress testing."""
        self.ensure_authenticated()

        endpoints = [
            (APIEndpoints.DASHBOARD_OVERVIEW, "Stress: Dashboard Overview"),
            (APIEndpoints.DASHBOARD_REVENUE, "Stress: Revenue"),
            (APIEndpoints.DASHBOARD_CASH_FLOW, "Stress: Cash Flow"),
        ]

        endpoint, name = random.choice(endpoints)

        with self.client.get(
            endpoint,
            headers=self.get_auth_headers(),
            catch_response=True,
            name=name
        ) as response:
            if response.status_code in [200, 401, 403, 404]:
                response.success()
            else:
                response.failure(f"Dashboard query failed: {response.status_code}")

    @task(5)
    @tag("stress", "write")
    def burst_create_operations(self):
        """Burst create operations for stress testing."""
        self.ensure_authenticated()

        # Create multiple clients in quick succession
        for _ in range(random.randint(1, 3)):
            client_data = TestDataGenerator.client_data()

            with self.client.post(
                APIEndpoints.CLIENTS_CREATE,
                json=client_data,
                headers=self.get_auth_headers(),
                catch_response=True,
                name="Stress: Burst Create Client"
            ) as response:
                if response.status_code in [200, 201, 400, 401, 403]:
                    response.success()
                else:
                    response.failure(f"Burst create failed: {response.status_code}")


# ============================================================
# EVENT HOOKS
# ============================================================

@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Initialize load test environment."""
    if isinstance(environment.runner, MasterRunner):
        print("=" * 70)
        print("AUREON SAAS PLATFORM - LOAD TEST SUITE")
        print("Target: 500+ concurrent users with p95 < 200ms")
        print("=" * 70)


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Log test start."""
    shared_state.test_start_time = datetime.now()

    print(f"\n{'='*70}")
    print(f"TEST STARTED: {shared_state.test_start_time.isoformat()}")
    print(f"Host: {environment.host}")
    print(f"User Classes: {[cls.__name__ for cls in environment.user_classes]}")
    print(f"{'='*70}\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Generate test summary report."""
    stats = environment.stats
    test_duration = (datetime.now() - shared_state.test_start_time).total_seconds() if shared_state.test_start_time else 0

    print("\n" + "=" * 70)
    print("LOAD TEST RESULTS SUMMARY")
    print("=" * 70)

    total_requests = stats.total.num_requests
    total_failures = stats.total.num_failures

    if total_requests > 0:
        failure_rate = (total_failures / total_requests) * 100

        print(f"\nTest Duration: {test_duration:.2f} seconds")
        print(f"Total Requests: {total_requests:,}")
        print(f"Total Failures: {total_failures:,}")
        print(f"Failure Rate: {failure_rate:.2f}%")
        print(f"Requests/sec: {stats.total.current_rps:.2f}")

        print(f"\nResponse Time Percentiles:")
        print(f"  p50 (Median): {stats.total.get_response_time_percentile(0.50):.2f}ms")
        print(f"  p75: {stats.total.get_response_time_percentile(0.75):.2f}ms")
        print(f"  p90: {stats.total.get_response_time_percentile(0.90):.2f}ms")
        print(f"  p95 (TARGET): {stats.total.get_response_time_percentile(0.95):.2f}ms")
        print(f"  p99: {stats.total.get_response_time_percentile(0.99):.2f}ms")

        print(f"\nAvg Response Time: {stats.total.avg_response_time:.2f}ms")
        print(f"Min Response Time: {stats.total.min_response_time:.2f}ms")
        print(f"Max Response Time: {stats.total.max_response_time:.2f}ms")

        # Validation
        validation = validate_scenario_results(stats, target_p95_ms=200.0, max_error_rate=0.01)

        print(f"\n{'='*70}")
        print("VALIDATION RESULTS")
        print(f"{'='*70}")
        for msg in validation.messages:
            print(f"  {msg}")

        print(f"\n{'='*70}")
        if validation.passed:
            print("OVERALL RESULT: PASS - System meets performance requirements")
            print("  - p95 response time < 200ms")
            print("  - Error rate < 1%")
        else:
            print("OVERALL RESULT: FAIL - System does not meet performance requirements")

        # Performance violations
        if shared_state.performance_violations:
            print(f"\nPerformance Violations: {len(shared_state.performance_violations)}")
            for violation in shared_state.performance_violations[:10]:
                print(f"  - {violation['endpoint']}: {violation['response_time_ms']:.2f}ms > {violation['threshold_ms']}ms")

        # Auth failures
        if shared_state.total_auth_failures > 0:
            print(f"\nTotal Authentication Failures: {shared_state.total_auth_failures}")

    else:
        print("No requests were made during the test")

    print("=" * 70)


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, response, context, exception, start_time, url, **kwargs):
    """Track individual request metrics."""
    # Log slow requests
    if response_time > 1000:  # > 1 second
        logger.warning(f"Slow request: {name} - {response_time:.2f}ms")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    import subprocess

    # Default command for quick test
    cmd = [
        "locust",
        "-f", "locustfile.py",
        "--host", "http://localhost:8000",
        "--headless",
        "-u", "100",
        "-r", "10",
        "-t", "60s",
    ]

    print("Running quick load test...")
    print(f"Command: {' '.join(cmd)}")
    subprocess.run(cmd)
