#!/bin/bash

# ==============================================
# AUREON by Rhematek Solutions
# Production Deployment Script
# ==============================================
# Usage: ./deploy.sh [environment]
# Environments: production, staging, development
# ==============================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-production}
PROJECT_DIR="/opt/aureon"
COMPOSE_FILE="docker-compose.prod.yml"

# Functions
print_header() {
    echo -e "${BLUE}"
    echo "============================================"
    echo "  AUREON Deployment Script"
    echo "  Rhematek Solutions"
    echo "============================================"
    echo -e "${NC}"
}

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    print_info "Checking prerequisites..."

    # Check if running as root or with sudo
    if [[ $EUID -ne 0 ]]; then
       print_error "This script must be run as root or with sudo"
       exit 1
    fi

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi

    # Check Git
    if ! command -v git &> /dev/null; then
        print_error "Git is not installed"
        exit 1
    fi

    print_info "All prerequisites met ✓"
}

backup_database() {
    print_info "Creating database backup..."

    if [ -f "$PROJECT_DIR/docker/backup/backup.sh" ]; then
        cd $PROJECT_DIR
        docker-compose -f $COMPOSE_FILE exec -T backup /backup.sh
        print_info "Database backup completed ✓"
    else
        print_warning "Backup script not found, skipping backup"
    fi
}

pull_latest_code() {
    print_info "Pulling latest code from Git..."

    cd $PROJECT_DIR

    # Stash any local changes
    if ! git diff-index --quiet HEAD --; then
        print_warning "Local changes detected, stashing..."
        git stash
    fi

    # Pull latest code
    if [ "$ENVIRONMENT" == "production" ]; then
        git fetch origin main
        git checkout main
        git pull origin main
    elif [ "$ENVIRONMENT" == "staging" ]; then
        git fetch origin develop
        git checkout develop
        git pull origin develop
    else
        git pull
    fi

    print_info "Code updated ✓"
}

build_images() {
    print_info "Building Docker images..."

    cd $PROJECT_DIR
    docker-compose -f $COMPOSE_FILE build --no-cache

    print_info "Docker images built ✓"
}

run_migrations() {
    print_info "Running database migrations..."

    cd $PROJECT_DIR
    docker-compose -f $COMPOSE_FILE exec -T web python manage.py migrate --noinput

    print_info "Migrations completed ✓"
}

collect_static() {
    print_info "Collecting static files..."

    cd $PROJECT_DIR
    docker-compose -f $COMPOSE_FILE exec -T web python manage.py collectstatic --noinput

    print_info "Static files collected ✓"
}

restart_services() {
    print_info "Restarting services..."

    cd $PROJECT_DIR
    docker-compose -f $COMPOSE_FILE up -d --force-recreate

    # Wait for services to be healthy
    print_info "Waiting for services to be healthy..."
    sleep 10

    print_info "Services restarted ✓"
}

health_check() {
    print_info "Running health checks..."

    # Check web service
    if docker-compose -f $COMPOSE_FILE ps web | grep -q "Up"; then
        print_info "Web service: healthy ✓"
    else
        print_error "Web service: unhealthy ✗"
        return 1
    fi

    # Check database
    if docker-compose -f $COMPOSE_FILE ps db | grep -q "Up"; then
        print_info "Database service: healthy ✓"
    else
        print_error "Database service: unhealthy ✗"
        return 1
    fi

    # Check Redis
    if docker-compose -f $COMPOSE_FILE ps redis | grep -q "Up"; then
        print_info "Redis service: healthy ✓"
    else
        print_error "Redis service: unhealthy ✗"
        return 1
    fi

    # Check Celery worker
    if docker-compose -f $COMPOSE_FILE ps celery_worker | grep -q "Up"; then
        print_info "Celery worker: healthy ✓"
    else
        print_warning "Celery worker: unhealthy ✗"
    fi

    # HTTP health check
    if curl -f http://localhost/health/ &> /dev/null; then
        print_info "HTTP health check: passed ✓"
    else
        print_warning "HTTP health check: failed ✗"
    fi

    print_info "Health checks completed"
}

cleanup() {
    print_info "Cleaning up old Docker resources..."

    # Remove unused images
    docker image prune -f

    # Remove unused volumes
    docker volume prune -f

    print_info "Cleanup completed ✓"
}

send_notification() {
    local status=$1
    local message=$2

    # Send email notification (requires mail command)
    if command -v mail &> /dev/null; then
        echo "$message" | mail -s "Aureon Deployment: $status" alerts@rhematek-solutions.com
    fi

    # Log to file
    echo "$(date): $status - $message" >> /var/log/aureon-deployments.log
}

rollback() {
    print_warning "Rolling back to previous version..."

    cd $PROJECT_DIR

    # Rollback git
    git reset --hard HEAD~1

    # Restart with old code
    docker-compose -f $COMPOSE_FILE up -d --force-recreate

    print_warning "Rollback completed"
}

# Main deployment process
main() {
    print_header

    print_info "Environment: $ENVIRONMENT"
    print_info "Starting deployment process..."
    echo ""

    # Ask for confirmation
    read -p "Are you sure you want to deploy to $ENVIRONMENT? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        print_warning "Deployment cancelled by user"
        exit 0
    fi

    # Deployment steps
    check_prerequisites

    # Backup before deployment (production only)
    if [ "$ENVIRONMENT" == "production" ]; then
        backup_database
    fi

    pull_latest_code
    build_images
    run_migrations
    collect_static
    restart_services

    # Wait a bit for services to stabilize
    sleep 15

    # Health checks
    if health_check; then
        print_info "${GREEN}Deployment successful!${NC}"
        send_notification "SUCCESS" "Aureon deployed successfully to $ENVIRONMENT"
        cleanup
    else
        print_error "Health checks failed!"
        read -p "Do you want to rollback? (yes/no): " rollback_confirm
        if [ "$rollback_confirm" == "yes" ]; then
            rollback
            send_notification "ROLLBACK" "Aureon deployment failed, rolled back to previous version"
        else
            send_notification "FAILED" "Aureon deployment failed on $ENVIRONMENT"
        fi
        exit 1
    fi

    echo ""
    print_info "Deployment Summary:"
    print_info "- Environment: $ENVIRONMENT"
    print_info "- Date: $(date)"
    print_info "- Git Commit: $(git rev-parse --short HEAD)"
    print_info "- Services: All healthy"
    echo ""
    print_info "${GREEN}Deployment completed successfully!${NC}"
}

# Run main function
main

# Exit
exit 0
