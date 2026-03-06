#!/bin/bash
#
# Aureon SaaS Platform - Load Test Runner Script
# ================================================
# Comprehensive script to run various load test scenarios.
#
# Usage:
#   ./scripts/run_load_test.sh [scenario] [options]
#
# Scenarios:
#   smoke     - Quick validation (10 users, 60s)
#   normal    - Normal load (100 users, 5min)
#   peak      - Peak load (500 users, 10min) - PRIMARY TARGET
#   stress    - Stress test (1000 users, 10min)
#   spike     - Spike test (sudden 500 user burst)
#   soak      - Endurance test (200 users, 1 hour)
#   custom    - Custom parameters (use with options)
#
# Options:
#   -h, --host      Target host URL (default: http://localhost:8000)
#   -u, --users     Number of users (for custom scenario)
#   -r, --rate      Spawn rate (for custom scenario)
#   -t, --time      Test duration (for custom scenario)
#   -w, --web       Run with web UI
#   --html          Generate HTML report
#   --csv           Generate CSV report
#   --tags          Run only tasks with specific tags
#   --help          Show this help message
#
# Examples:
#   ./scripts/run_load_test.sh smoke
#   ./scripts/run_load_test.sh peak --host https://staging.aureon.com
#   ./scripts/run_load_test.sh custom -u 300 -r 15 -t 5m --html
#   ./scripts/run_load_test.sh peak --tags critical
#

set -e

# Default configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOCUSTFILE="${PROJECT_ROOT}/locustfile.py"
DEFAULT_HOST="http://localhost:8000"
REPORTS_DIR="${PROJECT_ROOT}/load_test_reports"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Scenario configurations
declare -A SCENARIOS
SCENARIOS[smoke]="10 2 60s"
SCENARIOS[normal]="100 10 300s"
SCENARIOS[peak]="500 20 600s"
SCENARIOS[stress]="1000 50 600s"
SCENARIOS[spike]="500 100 330s"
SCENARIOS[soak]="200 5 3600s"

# Print functions
print_header() {
    echo -e "\n${BLUE}================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Help message
show_help() {
    head -50 "$0" | grep "^#" | sed 's/^# *//'
    exit 0
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."

    # Check if locust is installed
    if ! command -v locust &> /dev/null; then
        print_error "Locust is not installed. Install it with: pip install locust"
        exit 1
    fi

    # Check if locustfile exists
    if [[ ! -f "$LOCUSTFILE" ]]; then
        print_error "Locustfile not found at: $LOCUSTFILE"
        exit 1
    fi

    # Check Python
    if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
        print_error "Python is not installed"
        exit 1
    fi

    print_success "Prerequisites check passed"
}

# Create reports directory
setup_reports_dir() {
    if [[ ! -d "$REPORTS_DIR" ]]; then
        mkdir -p "$REPORTS_DIR"
        print_info "Created reports directory: $REPORTS_DIR"
    fi
}

# Parse command line arguments
parse_args() {
    SCENARIO="${1:-smoke}"
    shift || true

    HOST="$DEFAULT_HOST"
    USERS=""
    SPAWN_RATE=""
    DURATION=""
    WEB_UI=false
    HTML_REPORT=false
    CSV_REPORT=false
    TAGS=""
    EXTRA_ARGS=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--host)
                HOST="$2"
                shift 2
                ;;
            -u|--users)
                USERS="$2"
                shift 2
                ;;
            -r|--rate)
                SPAWN_RATE="$2"
                shift 2
                ;;
            -t|--time)
                DURATION="$2"
                shift 2
                ;;
            -w|--web)
                WEB_UI=true
                shift
                ;;
            --html)
                HTML_REPORT=true
                shift
                ;;
            --csv)
                CSV_REPORT=true
                shift
                ;;
            --tags)
                TAGS="$2"
                shift 2
                ;;
            --help)
                show_help
                ;;
            *)
                EXTRA_ARGS="$EXTRA_ARGS $1"
                shift
                ;;
        esac
    done
}

# Get scenario parameters
get_scenario_params() {
    local scenario=$1

    if [[ "$scenario" == "custom" ]]; then
        if [[ -z "$USERS" || -z "$SPAWN_RATE" || -z "$DURATION" ]]; then
            print_error "Custom scenario requires --users, --rate, and --time options"
            exit 1
        fi
        echo "$USERS $SPAWN_RATE $DURATION"
    elif [[ -v "SCENARIOS[$scenario]" ]]; then
        echo "${SCENARIOS[$scenario]}"
    else
        print_error "Unknown scenario: $scenario"
        print_info "Available scenarios: smoke, normal, peak, stress, spike, soak, custom"
        exit 1
    fi
}

# Build locust command
build_command() {
    local scenario=$1
    local params=$(get_scenario_params "$scenario")
    read -r users rate duration <<< "$params"

    CMD="locust -f $LOCUSTFILE --host $HOST"

    if [[ "$WEB_UI" == false ]]; then
        CMD="$CMD --headless"
        CMD="$CMD --users $users"
        CMD="$CMD --spawn-rate $rate"
        CMD="$CMD --run-time $duration"
    fi

    # Reports
    local timestamp=$(date +%Y%m%d_%H%M%S)

    if [[ "$HTML_REPORT" == true ]]; then
        CMD="$CMD --html ${REPORTS_DIR}/${scenario}_report_${timestamp}.html"
    fi

    if [[ "$CSV_REPORT" == true ]]; then
        CMD="$CMD --csv ${REPORTS_DIR}/${scenario}_${timestamp}"
    fi

    # Tags
    if [[ -n "$TAGS" ]]; then
        CMD="$CMD --tags $TAGS"
    fi

    # Extra arguments
    if [[ -n "$EXTRA_ARGS" ]]; then
        CMD="$CMD $EXTRA_ARGS"
    fi

    echo "$CMD"
}

# Run the load test
run_load_test() {
    local scenario=$1
    local params=$(get_scenario_params "$scenario")
    read -r users rate duration <<< "$params"

    print_header "AUREON LOAD TEST - $scenario"

    echo "Configuration:"
    echo "  Scenario:    $scenario"
    echo "  Host:        $HOST"
    echo "  Users:       $users"
    echo "  Spawn Rate:  $rate users/sec"
    echo "  Duration:    $duration"
    echo "  Web UI:      $WEB_UI"
    echo "  HTML Report: $HTML_REPORT"
    echo "  CSV Report:  $CSV_REPORT"
    if [[ -n "$TAGS" ]]; then
        echo "  Tags:        $TAGS"
    fi
    echo ""

    local cmd=$(build_command "$scenario")
    print_info "Executing: $cmd"
    echo ""

    # Run the command
    eval "$cmd"
    local exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        print_success "Load test completed successfully"
    else
        print_error "Load test failed with exit code: $exit_code"
        exit $exit_code
    fi
}

# Run quick validation
run_smoke_test() {
    print_header "SMOKE TEST - Quick Validation"

    local cmd="locust -f $LOCUSTFILE --host $HOST --headless -u 10 -r 2 -t 30s"
    print_info "Executing: $cmd"

    if eval "$cmd"; then
        print_success "Smoke test passed - system is operational"
        return 0
    else
        print_error "Smoke test failed - system may have issues"
        return 1
    fi
}

# Run performance baseline
run_baseline() {
    print_header "BASELINE TEST - Performance Measurement"

    setup_reports_dir
    local timestamp=$(date +%Y%m%d_%H%M%S)

    local cmd="locust -f $LOCUSTFILE --host $HOST --headless"
    cmd="$cmd -u 50 -r 5 -t 120s"
    cmd="$cmd --html ${REPORTS_DIR}/baseline_${timestamp}.html"
    cmd="$cmd --csv ${REPORTS_DIR}/baseline_${timestamp}"

    print_info "Executing: $cmd"

    if eval "$cmd"; then
        print_success "Baseline test completed"
        print_info "Reports saved to: ${REPORTS_DIR}/"
        return 0
    else
        print_error "Baseline test failed"
        return 1
    fi
}

# Run full test suite
run_full_suite() {
    print_header "FULL TEST SUITE"

    setup_reports_dir
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local suite_dir="${REPORTS_DIR}/suite_${timestamp}"
    mkdir -p "$suite_dir"

    local scenarios=("smoke" "normal" "peak")
    local failed=0

    for scenario in "${scenarios[@]}"; do
        print_info "Running $scenario test..."

        local params=$(get_scenario_params "$scenario")
        read -r users rate duration <<< "$params"

        local cmd="locust -f $LOCUSTFILE --host $HOST --headless"
        cmd="$cmd -u $users -r $rate -t $duration"
        cmd="$cmd --html ${suite_dir}/${scenario}_report.html"
        cmd="$cmd --csv ${suite_dir}/${scenario}"

        if eval "$cmd"; then
            print_success "$scenario test passed"
        else
            print_error "$scenario test failed"
            ((failed++))
        fi

        # Cool down between tests
        if [[ "$scenario" != "${scenarios[-1]}" ]]; then
            print_info "Cooling down for 30 seconds..."
            sleep 30
        fi
    done

    echo ""
    print_header "TEST SUITE RESULTS"
    echo "Tests run: ${#scenarios[@]}"
    echo "Tests passed: $((${#scenarios[@]} - failed))"
    echo "Tests failed: $failed"
    echo "Reports saved to: $suite_dir/"

    if [[ $failed -gt 0 ]]; then
        exit 1
    fi
}

# Distributed mode helper
run_distributed() {
    local mode=$1
    local workers=${2:-4}

    if [[ "$mode" == "master" ]]; then
        print_header "STARTING DISTRIBUTED TEST - MASTER"

        local cmd="locust -f $LOCUSTFILE --master --host $HOST"
        if [[ "$WEB_UI" == false ]]; then
            cmd="$cmd --headless --expect-workers $workers"
            cmd="$cmd -u ${USERS:-500} -r ${SPAWN_RATE:-20} -t ${DURATION:-600s}"
        fi

        print_info "Executing: $cmd"
        print_info "Waiting for $workers workers to connect..."
        eval "$cmd"

    elif [[ "$mode" == "worker" ]]; then
        print_header "STARTING DISTRIBUTED TEST - WORKER"

        local master_host=${3:-127.0.0.1}
        local cmd="locust -f $LOCUSTFILE --worker --master-host $master_host"

        print_info "Executing: $cmd"
        print_info "Connecting to master at $master_host..."
        eval "$cmd"
    else
        print_error "Invalid distributed mode. Use 'master' or 'worker'"
        exit 1
    fi
}

# Main execution
main() {
    check_prerequisites

    # Handle special commands
    case "${1:-}" in
        --help|help)
            show_help
            ;;
        baseline)
            run_baseline
            ;;
        suite|full)
            shift || true
            parse_args "peak" "$@"
            run_full_suite
            ;;
        distributed)
            shift || true
            local mode="${1:-master}"
            shift || true
            parse_args "peak" "$@"
            run_distributed "$mode" "${1:-4}" "${2:-127.0.0.1}"
            ;;
        *)
            parse_args "$@"
            setup_reports_dir
            run_load_test "$SCENARIO"
            ;;
    esac
}

# Run main
main "$@"
