#!/bin/bash
# Restore from Backup File Script
# Restores database from a pg_dump backup file

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

POSTGRES_USER="${POSTGRES_USER:-communitypulse}"
POSTGRES_DB="${POSTGRES_DB:-communitypulse}"

# Check arguments
if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file>"
    echo ""
    echo "Example:"
    echo "  $0 database/backups/full_communitypulse_2026-02-12_143022.sql"
    echo "  $0 database/backups/full_communitypulse_2026-02-12_143022.sql.gz"
    exit 1
fi

BACKUP_FILE="$1"

# Handle relative paths
if [[ ! "$BACKUP_FILE" = /* ]]; then
    BACKUP_FILE="$PROJECT_ROOT/$BACKUP_FILE"
fi

# Check file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "=========================================="
echo "Restore from Backup"
echo "=========================================="
echo "Database: $POSTGRES_DB"
echo "Backup: $BACKUP_FILE"
echo ""

# Check if Docker container is running
if ! docker compose ps db | grep -q "Up"; then
    echo "ERROR: Database container is not running."
    echo "Run: docker compose up -d db"
    exit 1
fi

# Confirm destructive operation
read -p "This will OVERWRITE the current database. Continue? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "Restoring database..."

# Handle gzipped files
if [[ "$BACKUP_FILE" == *.gz ]]; then
    echo "Decompressing and restoring..."
    gunzip -c "$BACKUP_FILE" | docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
else
    docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$BACKUP_FILE"
fi

echo ""
echo "=========================================="
echo "Restore completed!"
echo ""
echo "Verifying tables:"
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
    SELECT table_name,
           (SELECT COUNT(*) FROM information_schema.columns c WHERE c.table_name = t.table_name) as columns
    FROM information_schema.tables t
    WHERE table_schema = 'public'
    ORDER BY table_name;
"
echo "=========================================="
