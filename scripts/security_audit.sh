#!/bin/bash
# ============================================================
# AUREON SAAS PLATFORM - SECURITY AUDIT SCRIPT
# Rhematek Production Shield
#
# Comprehensive security validation for production deployment
# ============================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_DIR="${PROJECT_DIR:-$(pwd)}"
REPORT_FILE="${PROJECT_DIR}/security_audit_report.txt"
PASSED=0
FAILED=0
WARNINGS=0

# ============================================================
# HELPER FUNCTIONS
# ============================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED++))
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    ((WARNINGS++))
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED++))
}

write_report() {
    echo "$1" >> "$REPORT_FILE"
}

# ============================================================
# SECURITY CHECKS
# ============================================================

check_dependencies() {
    log_info "Checking security dependencies..."

    # Check if bandit is installed
    if command -v bandit &> /dev/null; then
        log_success "bandit is installed"
    else
        log_warning "bandit not installed (pip install bandit)"
    fi

    # Check if safety is installed
    if command -v safety &> /dev/null; then
        log_success "safety is installed"
    else
        log_warning "safety not installed (pip install safety)"
    fi

    # Check if trivy is installed (for Docker scanning)
    if command -v trivy &> /dev/null; then
        log_success "trivy is installed"
    else
        log_warning "trivy not installed (for container scanning)"
    fi
}

check_secret_files() {
    log_info "Checking for exposed secrets..."

    # Check for .env in git
    if git ls-files --error-unmatch .env 2>/dev/null; then
        log_error ".env file is tracked in git!"
    else
        log_success ".env file is not tracked"
    fi

    # Check for private keys
    key_files=$(find "$PROJECT_DIR" -name "*.pem" -o -name "*.key" -o -name "id_rsa" 2>/dev/null | grep -v ".venv" || true)
    if [ -n "$key_files" ]; then
        log_warning "Found potential private key files: $key_files"
    else
        log_success "No exposed private key files found"
    fi

    # Check for hardcoded secrets in Python files
    secrets_pattern="password\s*=\s*['\"]|api_key\s*=\s*['\"]|secret_key\s*=\s*['\"](?!env)"
    if grep -rPn "$secrets_pattern" --include="*.py" "$PROJECT_DIR/apps" 2>/dev/null | grep -v ".venv"; then
        log_warning "Potential hardcoded secrets found in Python files"
    else
        log_success "No obvious hardcoded secrets in Python files"
    fi
}

run_bandit() {
    log_info "Running bandit security scanner..."

    if command -v bandit &> /dev/null; then
        bandit_output=$(bandit -r "$PROJECT_DIR/apps" -f json 2>/dev/null || true)
        high_severity=$(echo "$bandit_output" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len([r for r in d.get('results',[]) if r.get('issue_severity')=='HIGH']))" 2>/dev/null || echo "0")
        medium_severity=$(echo "$bandit_output" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len([r for r in d.get('results',[]) if r.get('issue_severity')=='MEDIUM']))" 2>/dev/null || echo "0")

        if [ "$high_severity" -gt 0 ]; then
            log_error "Bandit found $high_severity HIGH severity issues"
        else
            log_success "No HIGH severity issues found by bandit"
        fi

        if [ "$medium_severity" -gt 5 ]; then
            log_warning "Bandit found $medium_severity MEDIUM severity issues"
        else
            log_success "Acceptable MEDIUM severity issues: $medium_severity"
        fi
    else
        log_warning "Skipping bandit (not installed)"
    fi
}

run_safety_check() {
    log_info "Checking for known vulnerabilities in dependencies..."

    if command -v safety &> /dev/null; then
        if [ -f "$PROJECT_DIR/requirements.txt" ]; then
            safety_output=$(safety check -r "$PROJECT_DIR/requirements.txt" --json 2>/dev/null || true)
            vuln_count=$(echo "$safety_output" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d))" 2>/dev/null || echo "0")

            if [ "$vuln_count" -gt 0 ]; then
                log_warning "Found $vuln_count known vulnerabilities in dependencies"
            else
                log_success "No known vulnerabilities in dependencies"
            fi
        else
            log_warning "requirements.txt not found"
        fi
    else
        log_warning "Skipping safety check (not installed)"
    fi
}

check_django_settings() {
    log_info "Checking Django security settings..."

    settings_file="$PROJECT_DIR/config/settings.py"

    if [ -f "$settings_file" ]; then
        # Check DEBUG setting
        if grep -q "DEBUG = True" "$settings_file"; then
            log_error "DEBUG is set to True in settings"
        else
            log_success "DEBUG setting looks safe"
        fi

        # Check SECRET_KEY
        if grep -q "SECRET_KEY.*insecure" "$settings_file"; then
            log_warning "Using insecure default SECRET_KEY"
        else
            log_success "SECRET_KEY configuration looks safe"
        fi

        # Check for security middleware
        if grep -q "SecurityMiddleware" "$settings_file"; then
            log_success "SecurityMiddleware is configured"
        else
            log_error "SecurityMiddleware not found"
        fi

        # Check for CSP middleware
        if grep -q "CSPMiddleware" "$settings_file"; then
            log_success "CSP middleware is configured"
        else
            log_warning "CSP middleware not configured"
        fi

        # Check for CORS
        if grep -q "CorsMiddleware" "$settings_file"; then
            log_success "CORS middleware is configured"
        else
            log_warning "CORS middleware not configured"
        fi

        # Check for Axes (brute force protection)
        if grep -q "AxesMiddleware" "$settings_file"; then
            log_success "Axes brute force protection is configured"
        else
            log_warning "Axes brute force protection not configured"
        fi

        # Check password validators
        if grep -q "MinimumLengthValidator" "$settings_file"; then
            log_success "Password length validation configured"
        else
            log_warning "No minimum password length configured"
        fi
    else
        log_error "Settings file not found: $settings_file"
    fi
}

check_security_headers() {
    log_info "Checking security headers configuration..."

    # Check settings for security headers
    settings_file="$PROJECT_DIR/config/settings.py"

    security_settings=(
        "SECURE_SSL_REDIRECT"
        "SECURE_HSTS_SECONDS"
        "SECURE_HSTS_INCLUDE_SUBDOMAINS"
        "SECURE_CONTENT_TYPE_NOSNIFF"
        "X_FRAME_OPTIONS"
        "CSRF_COOKIE_SECURE"
        "SESSION_COOKIE_SECURE"
    )

    for setting in "${security_settings[@]}"; do
        if grep -q "$setting" "$settings_file" 2>/dev/null; then
            log_success "$setting is configured"
        else
            log_warning "$setting not found in settings"
        fi
    done
}

check_authentication() {
    log_info "Checking authentication configuration..."

    # Check for JWT configuration
    if grep -rq "rest_framework_simplejwt" "$PROJECT_DIR/config" 2>/dev/null; then
        log_success "JWT authentication configured"
    else
        log_warning "JWT authentication not found"
    fi

    # Check for 2FA configuration
    if grep -rq "pyotp\|totp" "$PROJECT_DIR/apps" 2>/dev/null; then
        log_success "2FA (TOTP) implementation found"
    else
        log_warning "2FA not implemented"
    fi

    # Check for rate limiting
    if grep -rq "throttle\|rate.*limit" "$PROJECT_DIR/config" 2>/dev/null; then
        log_success "Rate limiting configured"
    else
        log_warning "Rate limiting not found"
    fi
}

check_database_security() {
    log_info "Checking database security..."

    # Check for SQL injection vulnerabilities
    # Look for raw() or extra() without proper escaping
    raw_queries=$(grep -rn "\.raw(" --include="*.py" "$PROJECT_DIR/apps" 2>/dev/null | wc -l || echo "0")
    extra_queries=$(grep -rn "\.extra(" --include="*.py" "$PROJECT_DIR/apps" 2>/dev/null | wc -l || echo "0")

    if [ "$raw_queries" -gt 0 ] || [ "$extra_queries" -gt 0 ]; then
        log_warning "Found $raw_queries raw() and $extra_queries extra() queries - verify SQL injection protection"
    else
        log_success "No raw SQL queries found (ORM-based queries are safer)"
    fi

    # Check for database encryption
    if grep -rq "encrypt\|fernet" "$PROJECT_DIR/apps" 2>/dev/null; then
        log_success "Database field encryption found"
    else
        log_warning "No database field encryption found"
    fi
}

check_file_uploads() {
    log_info "Checking file upload security..."

    # Check for file validation
    if grep -rq "validate_file\|file_extension\|content_types" "$PROJECT_DIR/apps" 2>/dev/null; then
        log_success "File validation found"
    else
        log_warning "No file upload validation found"
    fi

    # Check for file size limits
    if grep -rq "MAX_UPLOAD_SIZE\|FILE_UPLOAD_MAX" "$PROJECT_DIR" 2>/dev/null; then
        log_success "File size limits configured"
    else
        log_warning "No file size limits found"
    fi
}

check_docker_security() {
    log_info "Checking Docker security..."

    dockerfile="$PROJECT_DIR/Dockerfile"

    if [ -f "$dockerfile" ]; then
        # Check for non-root user
        if grep -q "USER " "$dockerfile"; then
            log_success "Non-root user configured in Dockerfile"
        else
            log_warning "Running as root in Docker container"
        fi

        # Check for health check
        if grep -q "HEALTHCHECK" "$dockerfile"; then
            log_success "Docker health check configured"
        else
            log_warning "No Docker health check configured"
        fi

        # Check base image
        if grep -q "alpine" "$dockerfile"; then
            log_success "Using minimal Alpine base image"
        else
            log_warning "Consider using minimal base image (alpine)"
        fi
    else
        log_warning "Dockerfile not found"
    fi

    # Run Trivy if available
    if command -v trivy &> /dev/null && [ -f "$dockerfile" ]; then
        log_info "Running Trivy container scan..."
        trivy_output=$(trivy fs --severity HIGH,CRITICAL "$PROJECT_DIR" 2>/dev/null || true)
        if echo "$trivy_output" | grep -q "HIGH\|CRITICAL"; then
            log_warning "Trivy found HIGH/CRITICAL vulnerabilities"
        else
            log_success "No HIGH/CRITICAL vulnerabilities found by Trivy"
        fi
    fi
}

check_logging() {
    log_info "Checking security logging..."

    # Check for audit logging
    if grep -rq "auditlog" "$PROJECT_DIR/config" 2>/dev/null; then
        log_success "Audit logging configured"
    else
        log_warning "Audit logging not configured"
    fi

    # Check for sensitive data in logs
    if grep -rq "password.*log\|credit.*card.*log" "$PROJECT_DIR/apps" 2>/dev/null; then
        log_warning "Potential sensitive data in logging"
    else
        log_success "No obvious sensitive data in logging"
    fi
}

check_api_security() {
    log_info "Checking API security..."

    # Check for API versioning
    if grep -rq "api/v[0-9]\|VERSION" "$PROJECT_DIR/config" 2>/dev/null; then
        log_success "API versioning found"
    else
        log_warning "No API versioning found"
    fi

    # Check for input validation
    if grep -rq "serializer\|Validator" "$PROJECT_DIR/apps" 2>/dev/null; then
        log_success "Input validation (serializers) found"
    else
        log_warning "No input validation found"
    fi

    # Check for permission classes
    if grep -rq "permission_classes\|IsAuthenticated" "$PROJECT_DIR/apps" 2>/dev/null; then
        log_success "Permission classes configured"
    else
        log_warning "No permission classes found"
    fi
}

# ============================================================
# MAIN EXECUTION
# ============================================================

main() {
    echo ""
    echo "============================================================"
    echo "  AUREON SECURITY AUDIT"
    echo "  Rhematek Production Shield"
    echo "  Date: $(date)"
    echo "============================================================"
    echo ""

    # Initialize report
    echo "AUREON SECURITY AUDIT REPORT" > "$REPORT_FILE"
    echo "Generated: $(date)" >> "$REPORT_FILE"
    echo "============================================================" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"

    # Run all checks
    check_dependencies
    echo ""
    check_secret_files
    echo ""
    run_bandit
    echo ""
    run_safety_check
    echo ""
    check_django_settings
    echo ""
    check_security_headers
    echo ""
    check_authentication
    echo ""
    check_database_security
    echo ""
    check_file_uploads
    echo ""
    check_docker_security
    echo ""
    check_logging
    echo ""
    check_api_security

    # Summary
    echo ""
    echo "============================================================"
    echo "  SECURITY AUDIT SUMMARY"
    echo "============================================================"
    echo ""
    echo -e "${GREEN}Passed:${NC}   $PASSED"
    echo -e "${YELLOW}Warnings:${NC} $WARNINGS"
    echo -e "${RED}Failed:${NC}   $FAILED"
    echo ""

    total=$((PASSED + WARNINGS + FAILED))
    if [ $total -gt 0 ]; then
        score=$(( (PASSED * 100) / total ))
        echo "Security Score: ${score}%"

        if [ $FAILED -eq 0 ] && [ $WARNINGS -lt 5 ]; then
            echo -e "${GREEN}RESULT: PASS - Ready for production${NC}"
        elif [ $FAILED -eq 0 ]; then
            echo -e "${YELLOW}RESULT: PASS WITH WARNINGS - Review recommended${NC}"
        else
            echo -e "${RED}RESULT: FAIL - Address critical issues before deployment${NC}"
        fi
    fi

    echo ""
    echo "Full report saved to: $REPORT_FILE"
    echo "============================================================"

    # Write summary to report
    echo "" >> "$REPORT_FILE"
    echo "SUMMARY" >> "$REPORT_FILE"
    echo "Passed: $PASSED" >> "$REPORT_FILE"
    echo "Warnings: $WARNINGS" >> "$REPORT_FILE"
    echo "Failed: $FAILED" >> "$REPORT_FILE"
}

# Run main function
main "$@"
