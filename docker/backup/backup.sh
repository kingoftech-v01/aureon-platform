#!/bin/sh
# Aureon by Rhematek Solutions
# PostgreSQL Backup Script
# Automated daily backups with retention policy

set -e

# Configuration
BACKUP_DIR="/backups"
DATE=$(date +"%Y%m%d_%H%M%S")
RETENTION_DAYS=30

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Backup filename
BACKUP_FILE="$BACKUP_DIR/aureon_backup_$DATE.sql.gz"

echo "Starting backup at $(date)"
echo "Backup file: $BACKUP_FILE"

# Create compressed backup
PGPASSWORD=$POSTGRES_PASSWORD pg_dump \
    -h $PGHOST \
    -U $POSTGRES_USER \
    -d $POSTGRES_DB \
    --clean \
    --if-exists \
    --create \
    --verbose \
    | gzip > $BACKUP_FILE

# Verify backup was created
if [ -f "$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "Backup completed successfully: $BACKUP_FILE ($BACKUP_SIZE)"
else
    echo "ERROR: Backup failed!" >&2
    exit 1
fi

# Remove backups older than retention period
echo "Cleaning up old backups (retention: $RETENTION_DAYS days)"
find $BACKUP_DIR -name "aureon_backup_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete

# List current backups
echo "Current backups:"
ls -lh $BACKUP_DIR/aureon_backup_*.sql.gz 2>/dev/null || echo "No backups found"

# Send success notification (optional - requires mail setup)
# echo "Backup completed: $BACKUP_FILE ($BACKUP_SIZE)" | mail -s "Aureon Backup Success" alerts@rhematek-solutions.com

echo "Backup process completed at $(date)"
