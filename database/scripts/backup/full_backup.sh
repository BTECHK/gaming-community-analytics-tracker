#!/bin/bash
# Full Database Backup Script
# Creates a complete pg_dump with schema and data

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
BACKUP_DIR="$PROJECT_ROOT/database/backups"

POSTGRES_USER="${POSTGRES_USER:-communitypulse}"
POSTGRES_DB="${POSTGRES_DB:-communitypulse}"
TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/full_${POSTGRES_DB}_${TIMESTAMP}.sql"

echo "=========================================="
echo "Full Database Backup"
echo "=========================================="
echo "Database: $POSTGRES_DB"
echo "User: $POSTGRES_USER"
echo "Output: $BACKUP_FILE"
echo ""

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Check if Docker container is running
if ! docker compose ps db | grep -q "Up"; then
    echo "ERROR: Database container is not running."
    echo "Run: docker compose up -d db"
    exit 1
fi

# Create backup using pg_dump
echo "Creating backup..."
docker compose exec -T db pg_dump \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    --clean \
    --if-exists \
    --create \
    --no-owner \
    --no-privileges \
    > "$BACKUP_FILE"

# Verify backup was created
if [ -f "$BACKUP_FILE" ]; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo ""
    echo "=========================================="
    echo "Backup completed successfully!"
    echo "File: $BACKUP_FILE"
    echo "Size: $SIZE"
    echo "=========================================="
else
    echo "ERROR: Backup file was not created"
    exit 1
fi

# Optional: Create compressed version
echo ""
echo "Creating compressed backup..."
gzip -c "$BACKUP_FILE" > "${BACKUP_FILE}.gz"
GZIP_SIZE=$(du -h "${BACKUP_FILE}.gz" | cut -f1)
echo "Compressed: ${BACKUP_FILE}.gz ($GZIP_SIZE)"
