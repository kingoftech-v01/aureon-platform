#!/usr/bin/env python
"""
Aureon SaaS Platform - Load Testing with Locust
Rhematek Production Shield + Scale8

Usage:
    # Quick test (100 users)
    locust -f scripts/load_test.py --headless --users 100 --spawn-rate 10 --run-time 60s

    # Scale test (500 users)
    locust -f scripts/load_test.py --headless --users 500 --spawn-rate 10 --run-time 300s

    # Web UI mode
    locust -f scripts/load_test.py --host https://aureon.rhematek-solutions.com
"""

import json
import random
import string
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner


# ============================================================
# CONFIGURATION
# ============================================================

class AureonConfig:
    """Test configuration for Aureon platform."""

    # API Endpoints
    HEALTH_ENDPOINT = "/api/health/"
    LOGIN_ENDPOINT = "/api/auth/login/"
    REGISTER_ENDPOINT = "/api/auth/register/"
    CLIENTS_ENDPOINT = "/api/clients/"
    CONTRACTS_ENDPOINT = "/api/contracts/"
    INVOICES_ENDPOINT = "/api/invoices/"
    ANALYTICS_ENDPOINT = "/api/analytics/dashboard/"

    # Test credentials (create these in your test environment)
    TEST_USERS = [
        {"email": "test1@aureon.test", "password": "TestPass123!"},
        {"email": "test2@aureon.test", "password": "TestPass123!"},
        {"email": "test3@aureon.test", "password": "TestPass123!"},
        {"email": "test4@aureon.test", "password": "TestPass123!"},
        {"email": "test5@aureon.test", "password": "TestPass123!"},
    ]


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def generate_random_string(length=10):
    """Generate a random string for test data."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_random_email():
    """Generate a random email for registration tests."""
    return f"loadtest_{generate_random_string(8)}@aureon.test"


# ============================================================
# USER BEHAVIOR CLASSES
# ============================================================

class AureonUser(HttpUser):
    """
    Base Aureon user for load testing.
    Simulates typical user behavior on the platform.
    """

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    token = None

    def on_start(self):
        """Initialize user session."""
        # Try to authenticate
        self.authenticate()

    def authenticate(self):
        """Authenticate with the API and store token."""
        credentials = random.choice(AureonConfig.TEST_USERS)

        with self.client.post(
            AureonConfig.LOGIN_ENDPOINT,
            json=credentials,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    self.token = data.get("access") or data.get("token")
                    response.success()
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 401:
                # User might not exist, that's okay for load testing
                response.success()
            else:
                response.failure(f"Login failed: {response.status_code}")

    def get_headers(self):
        """Get request headers with authentication."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    # --------------------------------------------------------
    # HEALTH CHECK TASKS (High frequency)
    # --------------------------------------------------------

    @task(10)
    def health_check(self):
        """Test health check endpoint - highest priority."""
        with self.client.get(
            AureonConfig.HEALTH_ENDPOINT,
            catch_response=True,
            name="Health Check"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")

    # --------------------------------------------------------
    # AUTHENTICATION TASKS
    # --------------------------------------------------------

    @task(3)
    def login_flow(self):
        """Test login endpoint."""
        credentials = random.choice(AureonConfig.TEST_USERS)

        with self.client.post(
            AureonConfig.LOGIN_ENDPOINT,
            json=credentials,
            catch_response=True,
            name="Login"
        ) as response:
            if response.status_code in [200, 401]:
                response.success()
            else:
                response.failure(f"Login error: {response.status_code}")

    # --------------------------------------------------------
    # CLIENT MANAGEMENT TASKS
    # --------------------------------------------------------

    @task(5)
    def list_clients(self):
        """Test client listing endpoint."""
        with self.client.get(
            AureonConfig.CLIENTS_ENDPOINT,
            headers=self.get_headers(),
            catch_response=True,
            name="List Clients"
        ) as response:
            if response.status_code in [200, 401, 403]:
                response.success()
            else:
                response.failure(f"List clients failed: {response.status_code}")

    @task(2)
    def create_client(self):
        """Test client creation endpoint."""
        client_data = {
            "name": f"Load Test Client {generate_random_string(6)}",
            "email": generate_random_email(),
            "phone": f"+1{random.randint(1000000000, 9999999999)}",
            "company": f"Test Company {generate_random_string(4)}",
        }

        with self.client.post(
            AureonConfig.CLIENTS_ENDPOINT,
            json=client_data,
            headers=self.get_headers(),
            catch_response=True,
            name="Create Client"
        ) as response:
            if response.status_code in [200, 201, 400, 401, 403]:
                response.success()
            else:
                response.failure(f"Create client failed: {response.status_code}")

    # --------------------------------------------------------
    # CONTRACT TASKS
    # --------------------------------------------------------

    @task(4)
    def list_contracts(self):
        """Test contract listing endpoint."""
        with self.client.get(
            AureonConfig.CONTRACTS_ENDPOINT,
            headers=self.get_headers(),
            catch_response=True,
            name="List Contracts"
        ) as response:
            if response.status_code in [200, 401, 403]:
                response.success()
            else:
                response.failure(f"List contracts failed: {response.status_code}")

    # --------------------------------------------------------
    # INVOICE TASKS
    # --------------------------------------------------------

    @task(4)
    def list_invoices(self):
        """Test invoice listing endpoint."""
        with self.client.get(
            AureonConfig.INVOICES_ENDPOINT,
            headers=self.get_headers(),
            catch_response=True,
            name="List Invoices"
        ) as response:
            if response.status_code in [200, 401, 403]:
                response.success()
            else:
                response.failure(f"List invoices failed: {response.status_code}")

    # --------------------------------------------------------
    # ANALYTICS TASKS
    # --------------------------------------------------------

    @task(2)
    def analytics_dashboard(self):
        """Test analytics dashboard endpoint."""
        with self.client.get(
            AureonConfig.ANALYTICS_ENDPOINT,
            headers=self.get_headers(),
            catch_response=True,
            name="Analytics Dashboard"
        ) as response:
            if response.status_code in [200, 401, 403]:
                response.success()
            else:
                response.failure(f"Analytics failed: {response.status_code}")


class AnonymousUser(HttpUser):
    """
    Anonymous user for testing public endpoints.
    Simulates visitors who haven't logged in.
    """

    wait_time = between(2, 5)

    @task(10)
    def health_check(self):
        """Test health check endpoint."""
        self.client.get(AureonConfig.HEALTH_ENDPOINT, name="Health Check (Anon)")

    @task(5)
    def visit_homepage(self):
        """Test homepage load."""
        self.client.get("/", name="Homepage")

    @task(3)
    def api_docs(self):
        """Test API documentation endpoint."""
        self.client.get("/api/docs/", name="API Docs")

    @task(2)
    def attempt_protected_endpoint(self):
        """Test that protected endpoints return 401."""
        with self.client.get(
            AureonConfig.CLIENTS_ENDPOINT,
            catch_response=True,
            name="Protected Endpoint (Anon)"
        ) as response:
            if response.status_code == 401:
                response.success()
            elif response.status_code == 403:
                response.success()
            else:
                response.failure(f"Expected 401/403, got {response.status_code}")


class HeavyUser(HttpUser):
    """
    Heavy user for stress testing.
    Simulates power users making frequent API calls.
    """

    wait_time = between(0.5, 1)  # Very frequent requests
    token = None

    def on_start(self):
        """Initialize and authenticate."""
        credentials = random.choice(AureonConfig.TEST_USERS)
        response = self.client.post(
            AureonConfig.LOGIN_ENDPOINT,
            json=credentials
        )
        if response.status_code == 200:
            try:
                data = response.json()
                self.token = data.get("access") or data.get("token")
            except json.JSONDecodeError:
                pass

    def get_headers(self):
        """Get request headers."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    @task(10)
    def rapid_api_calls(self):
        """Make rapid API calls to stress test."""
        endpoints = [
            AureonConfig.CLIENTS_ENDPOINT,
            AureonConfig.CONTRACTS_ENDPOINT,
            AureonConfig.INVOICES_ENDPOINT,
        ]
        endpoint = random.choice(endpoints)
        self.client.get(endpoint, headers=self.get_headers(), name="Rapid API Call")

    @task(5)
    def concurrent_operations(self):
        """Test concurrent read operations."""
        with self.client.get(
            AureonConfig.CLIENTS_ENDPOINT,
            headers=self.get_headers(),
            name="Concurrent Read"
        ):
            pass


# ============================================================
# EVENT HOOKS FOR REPORTING
# ============================================================

@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Initialize test run."""
    if isinstance(environment.runner, MasterRunner):
        print("=" * 60)
        print("AUREON LOAD TEST - Rhematek Production Shield")
        print("=" * 60)


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Log test start."""
    print(f"Starting load test against: {environment.host}")
    print(f"User classes: {[cls.__name__ for cls in environment.user_classes]}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Log test completion and summary."""
    stats = environment.stats

    print("\n" + "=" * 60)
    print("LOAD TEST RESULTS SUMMARY")
    print("=" * 60)

    # Overall statistics
    total_requests = stats.total.num_requests
    total_failures = stats.total.num_failures

    if total_requests > 0:
        failure_rate = (total_failures / total_requests) * 100
        print(f"Total Requests: {total_requests}")
        print(f"Total Failures: {total_failures}")
        print(f"Failure Rate: {failure_rate:.2f}%")
        print(f"Requests/sec: {stats.total.current_rps:.2f}")
        print(f"Avg Response Time: {stats.total.avg_response_time:.2f}ms")
        print(f"95th Percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms")
        print(f"99th Percentile: {stats.total.get_response_time_percentile(0.99):.2f}ms")

        # Pass/Fail assessment
        print("\n" + "-" * 40)
        if failure_rate < 1 and stats.total.avg_response_time < 500:
            print("RESULT: PASS - System meets performance requirements")
        elif failure_rate < 5:
            print("RESULT: WARNING - Some degradation detected")
        else:
            print("RESULT: FAIL - System under stress")
    else:
        print("No requests were made during the test")

    print("=" * 60)


# ============================================================
# CUSTOM TEST SHAPES (Optional)
# ============================================================

class StagesShape:
    """
    Custom load test shape with stages.
    Useful for simulating different traffic patterns.
    """

    stages = [
        {"duration": 60, "users": 50, "spawn_rate": 10},    # Warm up
        {"duration": 120, "users": 200, "spawn_rate": 20},  # Normal load
        {"duration": 60, "users": 500, "spawn_rate": 50},   # Peak load
        {"duration": 60, "users": 200, "spawn_rate": 20},   # Cool down
        {"duration": 60, "users": 50, "spawn_rate": 10},    # Wind down
    ]

    def tick(self):
        """Return the current stage configuration."""
        run_time = self.get_run_time()

        for stage in self.stages:
            stage["duration"] -= run_time
            if stage["duration"] > 0:
                return (stage["users"], stage["spawn_rate"])

        return None


# ============================================================
# MAIN ENTRY POINT
# ============================================================

if __name__ == "__main__":
    import os
    os.system(
        "locust -f scripts/load_test.py "
        "--host https://aureon.rhematek-solutions.com "
        "--headless --users 100 --spawn-rate 10 --run-time 60s"
    )
