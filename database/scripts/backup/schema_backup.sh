#!/bin/bash
# Schema-Only Backup Script
# Creates pg_dump with DDL only (no data)

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
BACKUP_DIR="$PROJECT_ROOT/database/backups"

POSTGRES_USER="${POSTGRES_USER:-communitypulse}"
POSTGRES_DB="${POSTGRES_DB:-communitypulse}"
TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/schema_${POSTGRES_DB}_${TIMESTAMP}.sql"

echo "=========================================="
echo "Schema-Only Backup"
echo "=========================================="
echo "Database: $POSTGRES_DB"
echo "Output: $BACKUP_FILE"
echo ""

mkdir -p "$BACKUP_DIR"

# Check if Docker container is running
if ! docker compose ps db | grep -q "Up"; then
    echo "ERROR: Database container is not running."
    echo "Run: docker compose up -d db"
    exit 1
fi

# Create schema-only backup
echo "Creating schema backup..."
docker compose exec -T db pg_dump \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    --schema-only \
    --clean \
    --if-exists \
    --no-owner \
    --no-privileges \
    > "$BACKUP_FILE"

if [ -f "$BACKUP_FILE" ]; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo ""
    echo "=========================================="
    echo "Schema backup completed!"
    echo "File: $BACKUP_FILE"
    echo "Size: $SIZE"
    echo "=========================================="
else
    echo "ERROR: Backup file was not created"
    exit 1
fi
