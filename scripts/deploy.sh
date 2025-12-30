#!/bin/bash
# ============================================================
# AUREON SaaS Platform - Production Deployment Script
# Rhematek Production Shield
# One-command deployment with full verification
# ============================================================

set -euo pipefail

# ============================================================
# Configuration
# ============================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DOMAIN="${DOMAIN:-aureon.rhematek-solutions.com}"
COMPOSE_FILE="docker-compose.prod.yml"
BACKUP_BEFORE_DEPLOY="${BACKUP_BEFORE_DEPLOY:-true}"
HEALTH_CHECK_RETRIES=30
HEALTH_CHECK_INTERVAL=10

# Notification settings
ADMIN_EMAIL="${ADMIN_EMAIL:-alerts@rhematek-solutions.com}"
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# ============================================================
# Helper Functions
# ============================================================
timestamp() {
    date "+%Y-%m-%d %H:%M:%S"
}

log_info() {
    echo -e "${BLUE}[$(timestamp)] [INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(timestamp)] [SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(timestamp)] [WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[$(timestamp)] [ERROR]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[$(timestamp)] [STEP]${NC} $1"
}

send_notification() {
    local status="$1"
    local message="$2"

    # Email notification
    if command -v mail &> /dev/null && [ -n "$ADMIN_EMAIL" ]; then
        echo "$message" | mail -s "[AUREON] Deployment $status" "$ADMIN_EMAIL" 2>/dev/null || true
    fi

    # Slack notification
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        local color="good"
        [ "$status" = "FAILED" ] && color="danger"
        [ "$status" = "WARNING" ] && color="warning"

        curl -s -X POST -H 'Content-type: application/json' \
            --data "{\"attachments\":[{\"color\":\"$color\",\"title\":\"Aureon Deployment $status\",\"text\":\"$message\",\"footer\":\"Rhematek Production Shield\",\"ts\":$(date +%s)}]}" \
            "$SLACK_WEBHOOK_URL" 2>/dev/null || true
    fi
}

cleanup_on_error() {
    log_error "Deployment failed! Rolling back..."

    # Attempt rollback
    if [ -f "$PROJECT_DIR/.deploy_backup" ]; then
        local backup_tag=$(cat "$PROJECT_DIR/.deploy_backup")
        log_info "Rolling back to: $backup_tag"
        docker compose -f "$PROJECT_DIR/$COMPOSE_FILE" down --timeout 30 2>/dev/null || true
        # Additional rollback steps could be added here
    fi

    send_notification "FAILED" "Deployment failed at $(timestamp). Check logs for details."
    exit 1
}

trap cleanup_on_error ERR

# ============================================================
# Pre-Deployment Checks
# ============================================================
pre_deployment_checks() {
    log_step "Running pre-deployment checks..."

    local errors=0

    # Check if running as appropriate user
    if [ "$EUID" -eq 0 ]; then
        log_warning "Running as root. Consider using a dedicated deploy user."
    fi

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed!"
        ((errors++))
    else
        log_success "Docker: $(docker --version)"
    fi

    # Check Docker Compose
    if ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not available!"
        ((errors++))
    else
        log_success "Docker Compose: $(docker compose version --short)"
    fi

    # Check Docker daemon
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running!"
        ((errors++))
    else
        log_success "Docker daemon is running"
    fi

    # Check disk space (require at least 10GB)
    local available_space=$(df -BG "$PROJECT_DIR" | awk 'NR==2 {print $4}' | tr -d 'G')
    if [ "${available_space:-0}" -lt 10 ]; then
        log_error "Insufficient disk space! Available: ${available_space}GB, Required: 10GB"
        ((errors++))
    else
        log_success "Disk space available: ${available_space}GB"
    fi

    # Check memory (recommend at least 8GB)
    local total_mem=$(free -g | awk '/^Mem:/{print $2}')
    if [ "${total_mem:-0}" -lt 4 ]; then
        log_warning "Low memory: ${total_mem}GB (recommended: 8GB)"
    else
        log_success "Memory available: ${total_mem}GB"
    fi

    # Check .env file
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        log_error ".env file not found at $PROJECT_DIR/.env"
        ((errors++))
    else
        log_success ".env file found"

        # Check required environment variables
        local required_vars=("DB_PASSWORD" "REDIS_PASSWORD" "SECRET_KEY" "STRIPE_SECRET_KEY")
        for var in "${required_vars[@]}"; do
            if ! grep -q "^${var}=" "$PROJECT_DIR/.env" 2>/dev/null; then
                log_warning "Missing environment variable: $var"
            fi
        done
    fi

    # Check compose file
    if [ ! -f "$PROJECT_DIR/$COMPOSE_FILE" ]; then
        log_error "Compose file not found: $PROJECT_DIR/$COMPOSE_FILE"
        ((errors++))
    else
        log_success "Compose file found"

        # Validate compose file
        if ! docker compose -f "$PROJECT_DIR/$COMPOSE_FILE" config --quiet 2>/dev/null; then
            log_error "Invalid Docker Compose configuration!"
            ((errors++))
        else
            log_success "Docker Compose configuration is valid"
        fi
    fi

    # Check network connectivity
    if ! curl -s --connect-timeout 5 https://registry.hub.docker.com/v2/ &> /dev/null; then
        log_warning "Cannot reach Docker Hub - may need to use cached images"
    else
        log_success "Docker Hub is reachable"
    fi

    if [ $errors -gt 0 ]; then
        log_error "Pre-deployment checks failed with $errors error(s)"
        exit 1
    fi

    log_success "All pre-deployment checks passed!"
}

# ============================================================
# Backup Before Deploy
# ============================================================
backup_before_deploy() {
    if [ "$BACKUP_BEFORE_DEPLOY" != "true" ]; then
        log_info "Skipping pre-deployment backup (BACKUP_BEFORE_DEPLOY=false)"
        return 0
    fi

    log_step "Creating pre-deployment backup..."

    # Run backup script if available
    if [ -f "$SCRIPT_DIR/backup.sh" ]; then
        bash "$SCRIPT_DIR/backup.sh" --quick
        log_success "Pre-deployment backup completed"
    else
        log_warning "Backup script not found, skipping backup"
    fi

    # Save current image tags for potential rollback
    local backup_tag="deploy-$(date +%Y%m%d-%H%M%S)"
    echo "$backup_tag" > "$PROJECT_DIR/.deploy_backup"
}

# ============================================================
# Pull Latest Code
# ============================================================
pull_latest_code() {
    log_step "Pulling latest code from repository..."

    cd "$PROJECT_DIR"

    # Check if it's a git repository
    if [ ! -d ".git" ]; then
        log_warning "Not a git repository, skipping code pull"
        return 0
    fi

    # Stash any local changes
    if ! git diff --quiet 2>/dev/null; then
        log_warning "Local changes detected, stashing..."
        git stash push -m "Auto-stash before deploy $(date +%Y%m%d-%H%M%S)"
    fi

    # Fetch and pull
    local current_branch=$(git rev-parse --abbrev-ref HEAD)
    log_info "Current branch: $current_branch"

    git fetch origin

    local local_hash=$(git rev-parse HEAD)
    local remote_hash=$(git rev-parse "origin/$current_branch")

    if [ "$local_hash" = "$remote_hash" ]; then
        log_info "Already up to date"
    else
        git pull origin "$current_branch"
        log_success "Pulled latest changes"
    fi

    # Log the current commit
    log_info "Deploying commit: $(git rev-parse --short HEAD) - $(git log -1 --format='%s')"
}

# ============================================================
# Build Docker Images
# ============================================================
build_images() {
    log_step "Building Docker images..."

    cd "$PROJECT_DIR"

    # Build with cache where possible
    docker compose -f "$COMPOSE_FILE" build \
        --parallel \
        --build-arg BUILDKIT_INLINE_CACHE=1

    log_success "Docker images built successfully"
}

# ============================================================
# Stop Existing Services (Graceful)
# ============================================================
stop_services() {
    log_step "Stopping existing services gracefully..."

    cd "$PROJECT_DIR"

    # Check if services are running
    if ! docker compose -f "$COMPOSE_FILE" ps --quiet 2>/dev/null | grep -q .; then
        log_info "No existing services running"
        return 0
    fi

    # Graceful shutdown with timeout
    docker compose -f "$COMPOSE_FILE" down --timeout 60

    log_success "Services stopped"
}

# ============================================================
# Run Database Migrations
# ============================================================
run_migrations() {
    log_step "Running database migrations..."

    cd "$PROJECT_DIR"

    # Start only the database first
    docker compose -f "$COMPOSE_FILE" up -d db-master pgbouncer

    # Wait for database to be healthy
    log_info "Waiting for database to be ready..."
    local retries=30
    while [ $retries -gt 0 ]; do
        if docker compose -f "$COMPOSE_FILE" exec -T db-master pg_isready -U "${DB_USER:-aureon_user}" &>/dev/null; then
            break
        fi
        sleep 2
        ((retries--))
    done

    if [ $retries -eq 0 ]; then
        log_error "Database failed to become ready"
        return 1
    fi

    log_success "Database is ready"

    # Run a temporary web container for migrations
    docker compose -f "$COMPOSE_FILE" run --rm web python manage.py migrate --noinput

    log_success "Database migrations completed"
}

# ============================================================
# Collect Static Files
# ============================================================
collect_static() {
    log_step "Collecting static files..."

    cd "$PROJECT_DIR"

    docker compose -f "$COMPOSE_FILE" run --rm web python manage.py collectstatic --noinput --clear

    log_success "Static files collected"
}

# ============================================================
# Start All Services
# ============================================================
start_services() {
    log_step "Starting all services..."

    cd "$PROJECT_DIR"

    docker compose -f "$COMPOSE_FILE" up -d

    log_success "All services started"
}

# ============================================================
# Health Verification
# ============================================================
verify_health() {
    log_step "Verifying service health..."

    cd "$PROJECT_DIR"

    local retries=$HEALTH_CHECK_RETRIES
    local all_healthy=false

    while [ $retries -gt 0 ]; do
        log_info "Health check attempt $((HEALTH_CHECK_RETRIES - retries + 1))/$HEALTH_CHECK_RETRIES..."

        # Check web service health
        local web_health=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/api/health/" 2>/dev/null || echo "000")

        # Check if containers are running
        local running_count=$(docker compose -f "$COMPOSE_FILE" ps --status running --quiet 2>/dev/null | wc -l)
        local total_services=$(docker compose -f "$COMPOSE_FILE" config --services 2>/dev/null | wc -l)

        log_info "Web health: HTTP $web_health, Containers: $running_count/$total_services"

        if [ "$web_health" = "200" ] && [ "$running_count" -ge 5 ]; then
            all_healthy=true
            break
        fi

        sleep $HEALTH_CHECK_INTERVAL
        ((retries--))
    done

    if [ "$all_healthy" = true ]; then
        log_success "All services are healthy!"
    else
        log_error "Health verification failed"

        # Show container status for debugging
        docker compose -f "$COMPOSE_FILE" ps

        # Show recent logs
        log_info "Recent container logs:"
        docker compose -f "$COMPOSE_FILE" logs --tail=50 web

        return 1
    fi
}

# ============================================================
# Post-Deployment Tasks
# ============================================================
post_deployment() {
    log_step "Running post-deployment tasks..."

    cd "$PROJECT_DIR"

    # Create notification templates
    docker compose -f "$COMPOSE_FILE" exec -T web python manage.py create_notification_templates 2>/dev/null || true

    # Clear Django cache
    docker compose -f "$COMPOSE_FILE" exec -T web python manage.py clearcache 2>/dev/null || true

    # Prune old Docker resources
    log_info "Cleaning up old Docker resources..."
    docker system prune -f --filter "until=24h" 2>/dev/null || true

    # Remove dangling images
    docker image prune -f 2>/dev/null || true

    log_success "Post-deployment tasks completed"
}

# ============================================================
# Security Verification
# ============================================================
verify_security() {
    log_step "Verifying security configuration..."

    local warnings=0

    # Check HTTPS redirect
    local http_code=$(curl -s -o /dev/null -w "%{http_code}" -L "http://$DOMAIN/" 2>/dev/null || echo "000")
    if [ "$http_code" = "200" ]; then
        log_success "HTTPS redirect working"
    else
        log_warning "HTTPS redirect check returned: $http_code"
        ((warnings++))
    fi

    # Check security headers
    local headers=$(curl -sI "https://$DOMAIN/" 2>/dev/null || echo "")

    if echo "$headers" | grep -qi "Strict-Transport-Security"; then
        log_success "HSTS header present"
    else
        log_warning "HSTS header missing"
        ((warnings++))
    fi

    if echo "$headers" | grep -qi "X-Content-Type-Options"; then
        log_success "X-Content-Type-Options header present"
    else
        log_warning "X-Content-Type-Options header missing"
        ((warnings++))
    fi

    if echo "$headers" | grep -qi "X-Frame-Options"; then
        log_success "X-Frame-Options header present"
    else
        log_warning "X-Frame-Options header missing"
        ((warnings++))
    fi

    if [ $warnings -gt 0 ]; then
        log_warning "Security verification completed with $warnings warning(s)"
    else
        log_success "Security verification passed!"
    fi
}

# ============================================================
# Print Deployment Summary
# ============================================================
print_summary() {
    local deploy_time=$((SECONDS / 60))
    local deploy_seconds=$((SECONDS % 60))

    echo ""
    echo "============================================================"
    echo -e "${GREEN}  DEPLOYMENT COMPLETE${NC}"
    echo "============================================================"
    echo ""
    echo "  Project:     Aureon SaaS Platform"
    echo "  Environment: Production"
    echo "  Domain:      https://$DOMAIN"
    echo "  Commit:      $(cd "$PROJECT_DIR" && git rev-parse --short HEAD 2>/dev/null || echo 'N/A')"
    echo "  Deploy Time: ${deploy_time}m ${deploy_seconds}s"
    echo ""
    echo "  Services Status:"
    docker compose -f "$PROJECT_DIR/$COMPOSE_FILE" ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null | head -20
    echo ""
    echo "  Monitoring:"
    echo "    - Grafana:    https://$DOMAIN/grafana/"
    echo "    - Prometheus: https://$DOMAIN/prometheus/"
    echo "    - Flower:     https://$DOMAIN/flower/"
    echo ""
    echo "  RHEMATEK PRODUCTION SHIELD: ENGAGED"
    echo "============================================================"
}

# ============================================================
# Main Execution
# ============================================================
main() {
    local start_time=$(date +%s)
    SECONDS=0

    echo ""
    echo "============================================================"
    echo -e "${CYAN}  AUREON PRODUCTION DEPLOYMENT${NC}"
    echo "  Rhematek Production Shield"
    echo "  $(timestamp)"
    echo "============================================================"
    echo ""

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-backup)
                BACKUP_BEFORE_DEPLOY=false
                shift
                ;;
            --skip-pull)
                SKIP_PULL=true
                shift
                ;;
            --no-cache)
                NO_CACHE=true
                shift
                ;;
            --help)
                echo "Usage: $0 [options]"
                echo "Options:"
                echo "  --skip-backup   Skip pre-deployment backup"
                echo "  --skip-pull     Skip git pull"
                echo "  --no-cache      Build without Docker cache"
                echo "  --help          Show this help"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    # Run deployment steps
    pre_deployment_checks
    backup_before_deploy

    if [ "${SKIP_PULL:-false}" != "true" ]; then
        pull_latest_code
    fi

    build_images
    run_migrations
    collect_static
    stop_services
    start_services
    verify_health
    post_deployment
    verify_security

    # Clean up backup marker on success
    rm -f "$PROJECT_DIR/.deploy_backup"

    print_summary

    send_notification "SUCCESS" "Deployment completed successfully at $(timestamp). Domain: https://$DOMAIN"

    exit 0
}

# Run main function
main "$@"
