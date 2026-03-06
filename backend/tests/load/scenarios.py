"""
Aureon SaaS Platform - Load Test Scenarios
Defines different load testing scenarios for various testing purposes.
"""

import time
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable
from enum import Enum
from locust import LoadTestShape


# ============================================================
# SCENARIO TYPES
# ============================================================

class ScenarioType(Enum):
    """Types of load test scenarios."""
    NORMAL = "normal"           # Standard operational load
    PEAK = "peak"               # Peak traffic simulation
    STRESS = "stress"           # Beyond capacity testing
    SPIKE = "spike"             # Sudden traffic burst
    SOAK = "soak"               # Extended duration test
    RAMP_UP = "ramp_up"         # Gradual increase
    STEP = "step"               # Stepped load increases
    BREAKPOINT = "breakpoint"   # Find system limits


@dataclass
class ScenarioStage:
    """Represents a single stage in a load test scenario."""
    duration: int           # Duration in seconds
    users: int              # Target number of users
    spawn_rate: float       # Users spawned per second
    name: str = ""          # Optional stage name


@dataclass
class ScenarioConfig:
    """Configuration for a complete load test scenario."""
    name: str
    description: str
    scenario_type: ScenarioType
    stages: List[ScenarioStage]
    total_duration: int = 0

    def __post_init__(self):
        """Calculate total duration from stages."""
        self.total_duration = sum(stage.duration for stage in self.stages)


# ============================================================
# PREDEFINED SCENARIOS
# ============================================================

# Normal Load Scenario (100 users)
# Simulates typical daily traffic patterns
NORMAL_LOAD_SCENARIO = ScenarioConfig(
    name="Normal Load Test",
    description="Simulates typical operational load with 100 concurrent users",
    scenario_type=ScenarioType.NORMAL,
    stages=[
        ScenarioStage(duration=30, users=25, spawn_rate=5, name="Warm-up"),
        ScenarioStage(duration=60, users=50, spawn_rate=10, name="Ramp-up"),
        ScenarioStage(duration=180, users=100, spawn_rate=15, name="Steady State"),
        ScenarioStage(duration=60, users=50, spawn_rate=10, name="Cool-down"),
        ScenarioStage(duration=30, users=0, spawn_rate=5, name="Wind-down"),
    ],
)


# Peak Load Scenario (500 users)
# Simulates peak business hours traffic
PEAK_LOAD_SCENARIO = ScenarioConfig(
    name="Peak Load Test",
    description="Simulates peak traffic with 500 concurrent users - primary target scenario",
    scenario_type=ScenarioType.PEAK,
    stages=[
        ScenarioStage(duration=60, users=100, spawn_rate=10, name="Warm-up"),
        ScenarioStage(duration=60, users=250, spawn_rate=20, name="Ramp-up Phase 1"),
        ScenarioStage(duration=60, users=400, spawn_rate=25, name="Ramp-up Phase 2"),
        ScenarioStage(duration=300, users=500, spawn_rate=30, name="Peak Steady State"),
        ScenarioStage(duration=60, users=300, spawn_rate=20, name="Cool-down Phase 1"),
        ScenarioStage(duration=60, users=100, spawn_rate=15, name="Cool-down Phase 2"),
        ScenarioStage(duration=60, users=0, spawn_rate=10, name="Wind-down"),
    ],
)


# Stress Test Scenario (1000 users)
# Tests system behavior under extreme load
STRESS_TEST_SCENARIO = ScenarioConfig(
    name="Stress Test",
    description="Tests system under extreme load with 1000 concurrent users",
    scenario_type=ScenarioType.STRESS,
    stages=[
        ScenarioStage(duration=60, users=200, spawn_rate=20, name="Warm-up"),
        ScenarioStage(duration=60, users=400, spawn_rate=30, name="Ramp-up Phase 1"),
        ScenarioStage(duration=60, users=600, spawn_rate=40, name="Ramp-up Phase 2"),
        ScenarioStage(duration=60, users=800, spawn_rate=50, name="Ramp-up Phase 3"),
        ScenarioStage(duration=300, users=1000, spawn_rate=50, name="Stress State"),
        ScenarioStage(duration=60, users=500, spawn_rate=30, name="Recovery Phase 1"),
        ScenarioStage(duration=60, users=200, spawn_rate=20, name="Recovery Phase 2"),
        ScenarioStage(duration=60, users=0, spawn_rate=15, name="Wind-down"),
    ],
)


# Spike Test Scenario (sudden 500 user burst)
# Tests system response to sudden traffic spikes
SPIKE_TEST_SCENARIO = ScenarioConfig(
    name="Spike Test",
    description="Tests system response to sudden traffic bursts (0 to 500 users instantly)",
    scenario_type=ScenarioType.SPIKE,
    stages=[
        ScenarioStage(duration=30, users=50, spawn_rate=10, name="Baseline"),
        ScenarioStage(duration=10, users=500, spawn_rate=100, name="Spike Up"),  # Sudden spike
        ScenarioStage(duration=120, users=500, spawn_rate=50, name="Spike Hold"),
        ScenarioStage(duration=10, users=50, spawn_rate=100, name="Spike Down"),  # Sudden drop
        ScenarioStage(duration=60, users=50, spawn_rate=10, name="Recovery"),
        ScenarioStage(duration=10, users=500, spawn_rate=100, name="Second Spike"),  # Another spike
        ScenarioStage(duration=60, users=500, spawn_rate=50, name="Second Hold"),
        ScenarioStage(duration=30, users=0, spawn_rate=50, name="Wind-down"),
    ],
)


# Soak Test Scenario (200 users for extended duration)
# Tests system stability over long periods
SOAK_TEST_SCENARIO = ScenarioConfig(
    name="Soak Test",
    description="Extended duration test with 200 users over 1 hour to detect memory leaks and degradation",
    scenario_type=ScenarioType.SOAK,
    stages=[
        ScenarioStage(duration=120, users=100, spawn_rate=10, name="Warm-up"),
        ScenarioStage(duration=120, users=200, spawn_rate=15, name="Ramp-up"),
        ScenarioStage(duration=3000, users=200, spawn_rate=5, name="Sustained Load"),  # 50 minutes
        ScenarioStage(duration=120, users=100, spawn_rate=10, name="Cool-down"),
        ScenarioStage(duration=60, users=0, spawn_rate=10, name="Wind-down"),
    ],
)


# Ramp-Up Test Scenario
# Gradually increases load to find optimal performance
RAMP_UP_SCENARIO = ScenarioConfig(
    name="Ramp-Up Test",
    description="Gradually increases load from 0 to 500 users to identify performance thresholds",
    scenario_type=ScenarioType.RAMP_UP,
    stages=[
        ScenarioStage(duration=60, users=50, spawn_rate=5, name="Phase 1: 50 users"),
        ScenarioStage(duration=60, users=100, spawn_rate=5, name="Phase 2: 100 users"),
        ScenarioStage(duration=60, users=150, spawn_rate=5, name="Phase 3: 150 users"),
        ScenarioStage(duration=60, users=200, spawn_rate=5, name="Phase 4: 200 users"),
        ScenarioStage(duration=60, users=250, spawn_rate=5, name="Phase 5: 250 users"),
        ScenarioStage(duration=60, users=300, spawn_rate=5, name="Phase 6: 300 users"),
        ScenarioStage(duration=60, users=350, spawn_rate=5, name="Phase 7: 350 users"),
        ScenarioStage(duration=60, users=400, spawn_rate=5, name="Phase 8: 400 users"),
        ScenarioStage(duration=60, users=450, spawn_rate=5, name="Phase 9: 450 users"),
        ScenarioStage(duration=60, users=500, spawn_rate=5, name="Phase 10: 500 users"),
        ScenarioStage(duration=60, users=0, spawn_rate=10, name="Wind-down"),
    ],
)


# Step Test Scenario
# Increases load in defined steps with holds
STEP_LOAD_SCENARIO = ScenarioConfig(
    name="Step Load Test",
    description="Increases load in 100-user steps with hold periods",
    scenario_type=ScenarioType.STEP,
    stages=[
        ScenarioStage(duration=120, users=100, spawn_rate=20, name="Step 1: 100 users"),
        ScenarioStage(duration=120, users=200, spawn_rate=20, name="Step 2: 200 users"),
        ScenarioStage(duration=120, users=300, spawn_rate=20, name="Step 3: 300 users"),
        ScenarioStage(duration=120, users=400, spawn_rate=20, name="Step 4: 400 users"),
        ScenarioStage(duration=180, users=500, spawn_rate=20, name="Step 5: 500 users"),
        ScenarioStage(duration=60, users=0, spawn_rate=25, name="Wind-down"),
    ],
)


# Breakpoint Test Scenario
# Continuously increases load until system fails
BREAKPOINT_SCENARIO = ScenarioConfig(
    name="Breakpoint Test",
    description="Continuously increases load to find system breaking point",
    scenario_type=ScenarioType.BREAKPOINT,
    stages=[
        ScenarioStage(duration=60, users=100, spawn_rate=10, name="Baseline"),
        ScenarioStage(duration=60, users=250, spawn_rate=15, name="Increase 1"),
        ScenarioStage(duration=60, users=500, spawn_rate=20, name="Increase 2"),
        ScenarioStage(duration=60, users=750, spawn_rate=25, name="Increase 3"),
        ScenarioStage(duration=60, users=1000, spawn_rate=30, name="Increase 4"),
        ScenarioStage(duration=60, users=1250, spawn_rate=35, name="Increase 5"),
        ScenarioStage(duration=60, users=1500, spawn_rate=40, name="Increase 6"),
        ScenarioStage(duration=60, users=1750, spawn_rate=45, name="Increase 7"),
        ScenarioStage(duration=60, users=2000, spawn_rate=50, name="Maximum Load"),
        ScenarioStage(duration=60, users=0, spawn_rate=50, name="Wind-down"),
    ],
)


# Registry of all scenarios
SCENARIOS: Dict[str, ScenarioConfig] = {
    "normal": NORMAL_LOAD_SCENARIO,
    "peak": PEAK_LOAD_SCENARIO,
    "stress": STRESS_TEST_SCENARIO,
    "spike": SPIKE_TEST_SCENARIO,
    "soak": SOAK_TEST_SCENARIO,
    "ramp_up": RAMP_UP_SCENARIO,
    "step": STEP_LOAD_SCENARIO,
    "breakpoint": BREAKPOINT_SCENARIO,
}


def get_scenario(name: str) -> Optional[ScenarioConfig]:
    """Get a scenario configuration by name."""
    return SCENARIOS.get(name.lower())


def list_scenarios() -> List[str]:
    """List all available scenario names."""
    return list(SCENARIOS.keys())


# ============================================================
# LOCUST LOAD TEST SHAPES
# ============================================================

class NormalLoadShape(LoadTestShape):
    """
    Normal load shape: 100 users with gradual ramp-up/down.
    Target: Steady state performance validation.
    """

    stages = [
        {"duration": 30, "users": 25, "spawn_rate": 5},
        {"duration": 90, "users": 50, "spawn_rate": 10},
        {"duration": 270, "users": 100, "spawn_rate": 15},
        {"duration": 330, "users": 50, "spawn_rate": 10},
        {"duration": 360, "users": 0, "spawn_rate": 5},
    ]

    def tick(self) -> Optional[Tuple[int, float]]:
        """Return current user count and spawn rate."""
        run_time = self.get_run_time()

        for stage in self.stages:
            if run_time < stage["duration"]:
                return (stage["users"], stage["spawn_rate"])

        return None


class PeakLoadShape(LoadTestShape):
    """
    Peak load shape: 500 users - PRIMARY TARGET SCENARIO.
    Target: p95 response time < 200ms with 500 concurrent users.
    """

    stages = [
        {"duration": 60, "users": 100, "spawn_rate": 10},
        {"duration": 120, "users": 250, "spawn_rate": 20},
        {"duration": 180, "users": 400, "spawn_rate": 25},
        {"duration": 480, "users": 500, "spawn_rate": 30},
        {"duration": 540, "users": 300, "spawn_rate": 20},
        {"duration": 600, "users": 100, "spawn_rate": 15},
        {"duration": 660, "users": 0, "spawn_rate": 10},
    ]

    def tick(self) -> Optional[Tuple[int, float]]:
        """Return current user count and spawn rate."""
        run_time = self.get_run_time()

        for stage in self.stages:
            if run_time < stage["duration"]:
                return (stage["users"], stage["spawn_rate"])

        return None


class StressTestShape(LoadTestShape):
    """
    Stress test shape: 1000 users to test system limits.
    Target: Identify system breaking points and degradation patterns.
    """

    stages = [
        {"duration": 60, "users": 200, "spawn_rate": 20},
        {"duration": 120, "users": 400, "spawn_rate": 30},
        {"duration": 180, "users": 600, "spawn_rate": 40},
        {"duration": 240, "users": 800, "spawn_rate": 50},
        {"duration": 540, "users": 1000, "spawn_rate": 50},
        {"duration": 600, "users": 500, "spawn_rate": 30},
        {"duration": 660, "users": 200, "spawn_rate": 20},
        {"duration": 720, "users": 0, "spawn_rate": 15},
    ]

    def tick(self) -> Optional[Tuple[int, float]]:
        """Return current user count and spawn rate."""
        run_time = self.get_run_time()

        for stage in self.stages:
            if run_time < stage["duration"]:
                return (stage["users"], stage["spawn_rate"])

        return None


class SpikeTestShape(LoadTestShape):
    """
    Spike test shape: Sudden burst from 50 to 500 users.
    Target: Test system resilience to sudden traffic increases.
    """

    stages = [
        {"duration": 30, "users": 50, "spawn_rate": 10},
        {"duration": 40, "users": 500, "spawn_rate": 100},    # Instant spike
        {"duration": 160, "users": 500, "spawn_rate": 50},
        {"duration": 170, "users": 50, "spawn_rate": 100},    # Instant drop
        {"duration": 230, "users": 50, "spawn_rate": 10},
        {"duration": 240, "users": 500, "spawn_rate": 100},   # Second spike
        {"duration": 300, "users": 500, "spawn_rate": 50},
        {"duration": 330, "users": 0, "spawn_rate": 50},
    ]

    def tick(self) -> Optional[Tuple[int, float]]:
        """Return current user count and spawn rate."""
        run_time = self.get_run_time()

        for stage in self.stages:
            if run_time < stage["duration"]:
                return (stage["users"], stage["spawn_rate"])

        return None


class SoakTestShape(LoadTestShape):
    """
    Soak test shape: 200 users for extended duration (1 hour+).
    Target: Detect memory leaks and performance degradation over time.
    """

    stages = [
        {"duration": 120, "users": 100, "spawn_rate": 10},
        {"duration": 240, "users": 200, "spawn_rate": 15},
        {"duration": 3240, "users": 200, "spawn_rate": 5},    # 50 min sustained
        {"duration": 3360, "users": 100, "spawn_rate": 10},
        {"duration": 3420, "users": 0, "spawn_rate": 10},
    ]

    def tick(self) -> Optional[Tuple[int, float]]:
        """Return current user count and spawn rate."""
        run_time = self.get_run_time()

        for stage in self.stages:
            if run_time < stage["duration"]:
                return (stage["users"], stage["spawn_rate"])

        return None


class StepLoadShape(LoadTestShape):
    """
    Step load shape: Increase users in 100-user increments.
    Target: Identify performance characteristics at each load level.
    """

    stages = [
        {"duration": 120, "users": 100, "spawn_rate": 20},
        {"duration": 240, "users": 200, "spawn_rate": 20},
        {"duration": 360, "users": 300, "spawn_rate": 20},
        {"duration": 480, "users": 400, "spawn_rate": 20},
        {"duration": 660, "users": 500, "spawn_rate": 20},
        {"duration": 720, "users": 0, "spawn_rate": 25},
    ]

    def tick(self) -> Optional[Tuple[int, float]]:
        """Return current user count and spawn rate."""
        run_time = self.get_run_time()

        for stage in self.stages:
            if run_time < stage["duration"]:
                return (stage["users"], stage["spawn_rate"])

        return None


class RampUpShape(LoadTestShape):
    """
    Ramp-up shape: Gradual increase from 0 to 500 users.
    Target: Linear load increase to identify performance thresholds.
    """

    target_users = 500
    ramp_duration = 600  # 10 minutes to reach target
    hold_duration = 300  # 5 minutes at peak
    ramp_down_duration = 120  # 2 minutes ramp down

    def tick(self) -> Optional[Tuple[int, float]]:
        """Return current user count and spawn rate."""
        run_time = self.get_run_time()

        if run_time < self.ramp_duration:
            # Linear ramp up
            current_users = int((run_time / self.ramp_duration) * self.target_users)
            spawn_rate = max(1, self.target_users / self.ramp_duration)
            return (current_users, spawn_rate)

        elif run_time < self.ramp_duration + self.hold_duration:
            # Hold at peak
            return (self.target_users, 10)

        elif run_time < self.ramp_duration + self.hold_duration + self.ramp_down_duration:
            # Ramp down
            time_in_ramp_down = run_time - self.ramp_duration - self.hold_duration
            current_users = int(
                self.target_users * (1 - time_in_ramp_down / self.ramp_down_duration)
            )
            return (max(0, current_users), 10)

        return None


class DoubleWaveShape(LoadTestShape):
    """
    Double wave shape: Two peaks simulating morning and afternoon traffic.
    Target: Simulate realistic daily traffic patterns.
    """

    def tick(self) -> Optional[Tuple[int, float]]:
        """Return current user count using a double sine wave pattern."""
        run_time = self.get_run_time()

        if run_time > 1200:  # 20 minutes total
            return None

        # Create two peaks in the load
        # First wave peaks at 5 minutes, second at 15 minutes
        wave1 = 150 * math.sin(math.pi * run_time / 600) if run_time < 600 else 0
        wave2 = 200 * math.sin(math.pi * (run_time - 600) / 600) if run_time >= 600 else 0

        # Base load + waves
        users = int(100 + max(0, wave1) + max(0, wave2))

        # Calculate appropriate spawn rate
        spawn_rate = max(10, users / 60)

        return (users, spawn_rate)


# Shape registry for easy selection
LOAD_SHAPES: Dict[str, type] = {
    "normal": NormalLoadShape,
    "peak": PeakLoadShape,
    "stress": StressTestShape,
    "spike": SpikeTestShape,
    "soak": SoakTestShape,
    "step": StepLoadShape,
    "ramp_up": RampUpShape,
    "double_wave": DoubleWaveShape,
}


def get_load_shape(name: str) -> Optional[type]:
    """Get a load shape class by name."""
    return LOAD_SHAPES.get(name.lower())


# ============================================================
# SCENARIO VALIDATION
# ============================================================

@dataclass
class ScenarioValidationResult:
    """Results from scenario validation."""
    passed: bool
    p50_ms: float
    p75_ms: float
    p90_ms: float
    p95_ms: float
    p99_ms: float
    error_rate: float
    rps: float
    total_requests: int
    total_failures: int
    messages: List[str] = field(default_factory=list)


def validate_scenario_results(
    stats,
    target_p95_ms: float = 200.0,
    max_error_rate: float = 0.01
) -> ScenarioValidationResult:
    """
    Validate load test results against performance targets.

    Args:
        stats: Locust stats object
        target_p95_ms: Target p95 response time in milliseconds
        max_error_rate: Maximum acceptable error rate (0.01 = 1%)

    Returns:
        ScenarioValidationResult with pass/fail and metrics
    """
    messages = []

    # Extract metrics
    total_requests = stats.total.num_requests
    total_failures = stats.total.num_failures
    error_rate = total_failures / total_requests if total_requests > 0 else 0

    p50 = stats.total.get_response_time_percentile(0.50) or 0
    p75 = stats.total.get_response_time_percentile(0.75) or 0
    p90 = stats.total.get_response_time_percentile(0.90) or 0
    p95 = stats.total.get_response_time_percentile(0.95) or 0
    p99 = stats.total.get_response_time_percentile(0.99) or 0
    rps = stats.total.current_rps or 0

    # Validation checks
    passed = True

    # Check p95 response time
    if p95 > target_p95_ms:
        passed = False
        messages.append(f"FAIL: p95 response time {p95:.2f}ms exceeds target {target_p95_ms}ms")
    else:
        messages.append(f"PASS: p95 response time {p95:.2f}ms within target {target_p95_ms}ms")

    # Check error rate
    if error_rate > max_error_rate:
        passed = False
        messages.append(f"FAIL: Error rate {error_rate*100:.2f}% exceeds maximum {max_error_rate*100:.2f}%")
    else:
        messages.append(f"PASS: Error rate {error_rate*100:.2f}% within acceptable range")

    # Check minimum throughput (assuming at least 10 RPS is expected)
    if rps < 10:
        messages.append(f"WARNING: Low throughput {rps:.2f} RPS")

    return ScenarioValidationResult(
        passed=passed,
        p50_ms=p50,
        p75_ms=p75,
        p90_ms=p90,
        p95_ms=p95,
        p99_ms=p99,
        error_rate=error_rate,
        rps=rps,
        total_requests=total_requests,
        total_failures=total_failures,
        messages=messages,
    )


# ============================================================
# SCENARIO EXECUTION HELPERS
# ============================================================

def get_scenario_command(scenario_name: str, host: str, headless: bool = True) -> str:
    """
    Generate locust command for a specific scenario.

    Args:
        scenario_name: Name of the scenario to run
        host: Target host URL
        headless: Run in headless mode

    Returns:
        Complete locust command string
    """
    scenario = get_scenario(scenario_name)
    if not scenario:
        raise ValueError(f"Unknown scenario: {scenario_name}")

    shape_class = get_load_shape(scenario_name)

    cmd_parts = [
        "locust",
        "-f locustfile.py",
        f"--host {host}",
    ]

    if headless:
        cmd_parts.append("--headless")

    # If using a shape, we don't need --users and --spawn-rate
    if shape_class:
        # Use the shape class name
        cmd_parts.append(f"--shape {shape_class.__name__}")
    else:
        # Use first stage's parameters as starting point
        if scenario.stages:
            stage = scenario.stages[0]
            cmd_parts.extend([
                f"--users {stage.users}",
                f"--spawn-rate {int(stage.spawn_rate)}",
                f"--run-time {scenario.total_duration}s",
            ])

    return " ".join(cmd_parts)


def print_scenario_info(scenario_name: str) -> None:
    """Print detailed information about a scenario."""
    scenario = get_scenario(scenario_name)
    if not scenario:
        print(f"Unknown scenario: {scenario_name}")
        return

    print("=" * 60)
    print(f"SCENARIO: {scenario.name}")
    print("=" * 60)
    print(f"Type: {scenario.scenario_type.value}")
    print(f"Description: {scenario.description}")
    print(f"Total Duration: {scenario.total_duration} seconds ({scenario.total_duration/60:.1f} minutes)")
    print()
    print("Stages:")
    print("-" * 60)

    cumulative_time = 0
    for i, stage in enumerate(scenario.stages, 1):
        cumulative_time += stage.duration
        print(f"  {i}. {stage.name or 'Stage ' + str(i)}")
        print(f"     Duration: {stage.duration}s | Users: {stage.users} | Spawn Rate: {stage.spawn_rate}/s")
        print(f"     Ends at: {cumulative_time}s ({cumulative_time/60:.1f} min)")
        print()

    print("=" * 60)


# Print scenario info when run directly
if __name__ == "__main__":
    print("\nAvailable Load Test Scenarios:")
    print("-" * 40)
    for name in list_scenarios():
        scenario = get_scenario(name)
        if scenario:
            print(f"\n{name.upper()}: {scenario.description}")
            print(f"  Duration: {scenario.total_duration}s | Peak Users: {max(s.users for s in scenario.stages)}")
