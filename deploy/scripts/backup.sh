#!/bin/bash
# ============================================================
# AUREON SaaS Platform - Backup Script
# Rhematek Production Shield
# Database and Media Backup with Rotation Policy
# ============================================================

set -euo pipefail

# ============================================================
# Configuration
# ============================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_DIR/backups}"
COMPOSE_FILE="docker-compose.prod.yml"

# Retention policy
DAILY_RETENTION=7      # Keep 7 daily backups
WEEKLY_RETENTION=4     # Keep 4 weekly backups (30 days worth)
MONTHLY_RETENTION=6    # Keep 6 monthly backups

# S3 configuration (optional)
S3_BUCKET="${S3_BUCKET:-}"
S3_PATH="${S3_PATH:-aureon-backups}"
AWS_REGION="${AWS_REGION:-us-east-1}"

# Notification settings
ADMIN_EMAIL="${ADMIN_EMAIL:-alerts@rhematek-solutions.com}"
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

send_notification() {
    local status="$1"
    local message="$2"

    # Email notification
    if command -v mail &> /dev/null && [ -n "$ADMIN_EMAIL" ]; then
        echo "$message" | mail -s "[AUREON] Backup $status" "$ADMIN_EMAIL" 2>/dev/null || true
    fi

    # Slack notification
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        local color="good"
        [ "$status" = "FAILED" ] && color="danger"
        [ "$status" = "WARNING" ] && color="warning"

        curl -s -X POST -H 'Content-type: application/json' \
            --data "{\"attachments\":[{\"color\":\"$color\",\"title\":\"Aureon Backup $status\",\"text\":\"$message\",\"footer\":\"Rhematek Production Shield\",\"ts\":$(date +%s)}]}" \
            "$SLACK_WEBHOOK_URL" 2>/dev/null || true
    fi
}

get_backup_size() {
    local file="$1"
    if [ -f "$file" ]; then
        du -h "$file" | cut -f1
    else
        echo "0"
    fi
}

cleanup_on_error() {
    log_error "Backup failed!"
    send_notification "FAILED" "Backup failed at $(timestamp). Check logs for details."

    # Clean up partial backup files
    rm -f "$BACKUP_DIR"/*.partial 2>/dev/null || true

    exit 1
}

trap cleanup_on_error ERR

# ============================================================
# Create Backup Directories
# ============================================================
create_backup_dirs() {
    log_info "Creating backup directories..."

    mkdir -p "$BACKUP_DIR/daily"
    mkdir -p "$BACKUP_DIR/weekly"
    mkdir -p "$BACKUP_DIR/monthly"
    mkdir -p "$BACKUP_DIR/media"
    mkdir -p "$BACKUP_DIR/logs"

    log_success "Backup directories ready"
}

# ============================================================
# Database Backup
# ============================================================
backup_database() {
    log_info "Starting database backup..."

    local date_stamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/daily/aureon_db_${date_stamp}.sql.gz"
    local backup_file_partial="${backup_file}.partial"

    cd "$PROJECT_DIR"

    # Get database credentials from environment
    source "$PROJECT_DIR/.env" 2>/dev/null || true

    local db_name="${DB_NAME:-aureon_db}"
    local db_user="${DB_USER:-aureon_user}"

    # Check if database container is running
    if ! docker compose -f "$COMPOSE_FILE" ps db-master --status running --quiet 2>/dev/null | grep -q .; then
        log_error "Database container is not running!"
        return 1
    fi

    # Create backup using pg_dump
    log_info "Dumping database: $db_name"

    docker compose -f "$COMPOSE_FILE" exec -T db-master \
        pg_dump -U "$db_user" -d "$db_name" \
        --format=custom \
        --compress=9 \
        --verbose \
        --no-owner \
        --no-privileges \
        2>"$BACKUP_DIR/logs/pg_dump_${date_stamp}.log" | gzip > "$backup_file_partial"

    # Verify backup
    if [ -s "$backup_file_partial" ]; then
        mv "$backup_file_partial" "$backup_file"
        local size=$(get_backup_size "$backup_file")
        log_success "Database backup completed: $backup_file ($size)"
        echo "$backup_file"
    else
        log_error "Database backup failed - file is empty"
        rm -f "$backup_file_partial"
        return 1
    fi
}

# ============================================================
# Quick Database Backup (for pre-deploy)
# ============================================================
backup_database_quick() {
    log_info "Starting quick database backup..."

    local date_stamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/daily/aureon_db_quick_${date_stamp}.sql.gz"

    cd "$PROJECT_DIR"

    source "$PROJECT_DIR/.env" 2>/dev/null || true

    local db_name="${DB_NAME:-aureon_db}"
    local db_user="${DB_USER:-aureon_user}"

    # Quick backup without verbose logging
    docker compose -f "$COMPOSE_FILE" exec -T db-master \
        pg_dump -U "$db_user" -d "$db_name" \
        --format=custom \
        --compress=6 \
        --no-owner \
        2>/dev/null | gzip > "$backup_file"

    if [ -s "$backup_file" ]; then
        local size=$(get_backup_size "$backup_file")
        log_success "Quick database backup completed: $backup_file ($size)"
    else
        log_warning "Quick database backup may have failed"
        rm -f "$backup_file"
    fi
}

# ============================================================
# Media Files Backup
# ============================================================
backup_media() {
    log_info "Starting media files backup..."

    local date_stamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/media/aureon_media_${date_stamp}.tar.gz"
    local backup_file_partial="${backup_file}.partial"

    cd "$PROJECT_DIR"

    # Get media volume path
    local media_volume=$(docker volume inspect aureon_media_volume --format '{{ .Mountpoint }}' 2>/dev/null || echo "")

    if [ -z "$media_volume" ]; then
        # Try to backup from container
        log_info "Backing up media from container..."

        docker compose -f "$COMPOSE_FILE" run --rm \
            -v "$BACKUP_DIR/media:/backup" \
            web tar czf "/backup/aureon_media_${date_stamp}.tar.gz" -C /app media/ 2>/dev/null

        if [ -f "$BACKUP_DIR/media/aureon_media_${date_stamp}.tar.gz" ]; then
            local size=$(get_backup_size "$BACKUP_DIR/media/aureon_media_${date_stamp}.tar.gz")
            log_success "Media backup completed: $size"
        else
            log_warning "Media backup may have failed"
        fi
    else
        # Direct volume backup
        log_info "Backing up media volume: $media_volume"

        tar czf "$backup_file_partial" -C "$media_volume" . 2>/dev/null

        if [ -s "$backup_file_partial" ]; then
            mv "$backup_file_partial" "$backup_file"
            local size=$(get_backup_size "$backup_file")
            log_success "Media backup completed: $backup_file ($size)"
        else
            log_warning "Media backup may have failed"
            rm -f "$backup_file_partial"
        fi
    fi
}

# ============================================================
# Redis Backup (Optional)
# ============================================================
backup_redis() {
    log_info "Starting Redis backup..."

    local date_stamp=$(date +%Y%m%d_%H%M%S)

    cd "$PROJECT_DIR"

    source "$PROJECT_DIR/.env" 2>/dev/null || true
    local redis_password="${REDIS_PASSWORD:-}"

    # Trigger BGSAVE on each Redis instance
    for redis_service in redis-cache redis-queue redis-result; do
        log_info "Backing up $redis_service..."

        docker compose -f "$COMPOSE_FILE" exec -T "$redis_service" \
            redis-cli -a "$redis_password" BGSAVE 2>/dev/null || true

        # Wait for BGSAVE to complete
        sleep 2

        # Copy RDB file
        local rdb_file="$BACKUP_DIR/daily/aureon_${redis_service}_${date_stamp}.rdb"
        docker compose -f "$COMPOSE_FILE" exec -T "$redis_service" \
            cat /data/dump.rdb > "$rdb_file" 2>/dev/null || true

        if [ -s "$rdb_file" ]; then
            gzip "$rdb_file"
            log_success "$redis_service backup completed"
        else
            rm -f "$rdb_file"
            log_warning "$redis_service backup skipped"
        fi
    done
}

# ============================================================
# Rotation: Daily Backups
# ============================================================
rotate_daily() {
    log_info "Rotating daily backups (keeping $DAILY_RETENTION days)..."

    find "$BACKUP_DIR/daily" -type f -mtime +$DAILY_RETENTION -delete 2>/dev/null || true

    local count=$(find "$BACKUP_DIR/daily" -type f 2>/dev/null | wc -l)
    log_success "Daily backups after rotation: $count files"
}

# ============================================================
# Rotation: Weekly Backups
# ============================================================
rotate_weekly() {
    log_info "Managing weekly backups..."

    # Create weekly backup on Sundays (or if forced)
    local day_of_week=$(date +%u)
    local date_stamp=$(date +%Y%m%d)

    if [ "$day_of_week" = "7" ] || [ "${FORCE_WEEKLY:-false}" = "true" ]; then
        # Find today's database backup
        local latest_daily=$(find "$BACKUP_DIR/daily" -name "aureon_db_${date_stamp}*.sql.gz" -type f 2>/dev/null | head -1)

        if [ -n "$latest_daily" ] && [ -f "$latest_daily" ]; then
            local weekly_file="$BACKUP_DIR/weekly/aureon_db_week_${date_stamp}.sql.gz"
            cp "$latest_daily" "$weekly_file"
            log_success "Created weekly backup: $weekly_file"
        fi
    fi

    # Rotate old weekly backups
    local retention_days=$((WEEKLY_RETENTION * 7))
    find "$BACKUP_DIR/weekly" -type f -mtime +$retention_days -delete 2>/dev/null || true

    local count=$(find "$BACKUP_DIR/weekly" -type f 2>/dev/null | wc -l)
    log_success "Weekly backups after rotation: $count files"
}

# ============================================================
# Rotation: Monthly Backups
# ============================================================
rotate_monthly() {
    log_info "Managing monthly backups..."

    # Create monthly backup on 1st of month (or if forced)
    local day_of_month=$(date +%d)
    local date_stamp=$(date +%Y%m)

    if [ "$day_of_month" = "01" ] || [ "${FORCE_MONTHLY:-false}" = "true" ]; then
        # Find latest database backup
        local latest_backup=$(find "$BACKUP_DIR/daily" -name "aureon_db_*.sql.gz" -type f 2>/dev/null | sort -r | head -1)

        if [ -n "$latest_backup" ] && [ -f "$latest_backup" ]; then
            local monthly_file="$BACKUP_DIR/monthly/aureon_db_month_${date_stamp}.sql.gz"
            cp "$latest_backup" "$monthly_file"
            log_success "Created monthly backup: $monthly_file"
        fi
    fi

    # Rotate old monthly backups
    local retention_days=$((MONTHLY_RETENTION * 30))
    find "$BACKUP_DIR/monthly" -type f -mtime +$retention_days -delete 2>/dev/null || true

    local count=$(find "$BACKUP_DIR/monthly" -type f 2>/dev/null | wc -l)
    log_success "Monthly backups after rotation: $count files"
}

# ============================================================
# Upload to S3 (Optional)
# ============================================================
upload_to_s3() {
    if [ -z "$S3_BUCKET" ]; then
        log_info "S3 upload skipped (S3_BUCKET not configured)"
        return 0
    fi

    log_info "Uploading backups to S3..."

    if ! command -v aws &> /dev/null; then
        log_warning "AWS CLI not installed, skipping S3 upload"
        return 0
    fi

    local date_stamp=$(date +%Y%m%d)

    # Upload today's backups
    for backup_file in "$BACKUP_DIR/daily/aureon_db_${date_stamp}"*.sql.gz; do
        if [ -f "$backup_file" ]; then
            local filename=$(basename "$backup_file")
            aws s3 cp "$backup_file" "s3://$S3_BUCKET/$S3_PATH/daily/$filename" \
                --region "$AWS_REGION" \
                --storage-class STANDARD_IA \
                2>/dev/null && log_success "Uploaded: $filename" || log_warning "Failed to upload: $filename"
        fi
    done

    # Set lifecycle policy for S3 (if not already set)
    # aws s3api put-bucket-lifecycle-configuration ...

    log_success "S3 upload completed"
}

# ============================================================
# Backup Verification
# ============================================================
verify_backup() {
    log_info "Verifying latest backup..."

    local latest_backup=$(find "$BACKUP_DIR/daily" -name "aureon_db_*.sql.gz" -type f 2>/dev/null | sort -r | head -1)

    if [ -z "$latest_backup" ]; then
        log_error "No backup files found!"
        return 1
    fi

    # Check file size (should be at least 1KB)
    local size_bytes=$(stat -c %s "$latest_backup" 2>/dev/null || stat -f %z "$latest_backup" 2>/dev/null || echo 0)
    if [ "$size_bytes" -lt 1024 ]; then
        log_error "Backup file is too small: $size_bytes bytes"
        return 1
    fi

    # Test gzip integrity
    if ! gzip -t "$latest_backup" 2>/dev/null; then
        log_error "Backup file is corrupted!"
        return 1
    fi

    log_success "Backup verification passed: $latest_backup ($(get_backup_size "$latest_backup"))"
}

# ============================================================
# Print Backup Summary
# ============================================================
print_summary() {
    echo ""
    echo "============================================================"
    echo -e "${GREEN}  BACKUP SUMMARY${NC}"
    echo "============================================================"
    echo ""
    echo "  Backup Location: $BACKUP_DIR"
    echo ""
    echo "  Daily Backups:   $(find "$BACKUP_DIR/daily" -type f 2>/dev/null | wc -l) files"
    echo "  Weekly Backups:  $(find "$BACKUP_DIR/weekly" -type f 2>/dev/null | wc -l) files"
    echo "  Monthly Backups: $(find "$BACKUP_DIR/monthly" -type f 2>/dev/null | wc -l) files"
    echo "  Media Backups:   $(find "$BACKUP_DIR/media" -type f 2>/dev/null | wc -l) files"
    echo ""
    echo "  Total Size:      $(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)"
    echo ""
    echo "  Latest Backup:"
    find "$BACKUP_DIR/daily" -name "aureon_db_*.sql.gz" -type f 2>/dev/null | sort -r | head -3 | while read file; do
        echo "    - $(basename "$file") ($(get_backup_size "$file"))"
    done
    echo ""
    echo "  Retention Policy:"
    echo "    - Daily:   $DAILY_RETENTION days"
    echo "    - Weekly:  $WEEKLY_RETENTION weeks"
    echo "    - Monthly: $MONTHLY_RETENTION months"
    echo ""
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
    echo -e "${BLUE}  AUREON BACKUP SYSTEM${NC}"
    echo "  Rhematek Production Shield"
    echo "  $(timestamp)"
    echo "============================================================"
    echo ""

    # Parse arguments
    local quick_mode=false
    local skip_media=false
    local skip_redis=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --quick)
                quick_mode=true
                skip_media=true
                skip_redis=true
                shift
                ;;
            --skip-media)
                skip_media=true
                shift
                ;;
            --skip-redis)
                skip_redis=true
                shift
                ;;
            --force-weekly)
                FORCE_WEEKLY=true
                shift
                ;;
            --force-monthly)
                FORCE_MONTHLY=true
                shift
                ;;
            --help)
                echo "Usage: $0 [options]"
                echo "Options:"
                echo "  --quick          Quick backup (database only, no verification)"
                echo "  --skip-media     Skip media files backup"
                echo "  --skip-redis     Skip Redis backup"
                echo "  --force-weekly   Force weekly backup creation"
                echo "  --force-monthly  Force monthly backup creation"
                echo "  --help           Show this help"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    # Run backup steps
    create_backup_dirs

    if [ "$quick_mode" = true ]; then
        backup_database_quick
    else
        backup_database

        if [ "$skip_media" != true ]; then
            backup_media
        fi

        if [ "$skip_redis" != true ]; then
            backup_redis
        fi

        verify_backup
    fi

    # Run rotation
    rotate_daily
    rotate_weekly
    rotate_monthly

    # Upload to S3 if configured
    upload_to_s3

    # Print summary
    if [ "$quick_mode" != true ]; then
        print_summary
    fi

    local duration=$((SECONDS / 60))
    local duration_seconds=$((SECONDS % 60))
    log_success "Backup completed in ${duration}m ${duration_seconds}s"

    send_notification "SUCCESS" "Backup completed successfully at $(timestamp). Total size: $(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)"

    exit 0
}

# Run main function
main "$@"
