#!/bin/bash
# Reset Database Script
# DANGEROUS: Drops all data and recreates schema

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

POSTGRES_USER="${POSTGRES_USER:-communitypulse}"
POSTGRES_DB="${POSTGRES_DB:-communitypulse}"

echo "=========================================="
echo "!!! DATABASE RESET !!!"
echo "=========================================="
echo ""
echo "WARNING: This will DELETE ALL DATA!"
echo "Database: $POSTGRES_DB"
echo ""

# Double confirmation
read -p "Are you sure you want to reset the database? (yes/N) " -r
if [[ ! $REPLY == "yes" ]]; then
    echo "Aborted."
    exit 0
fi

read -p "Type the database name to confirm: " -r
if [[ ! $REPLY == "$POSTGRES_DB" ]]; then
    echo "Database name mismatch. Aborted."
    exit 0
fi

echo ""
echo "Resetting database..."

# Drop and recreate
docker compose exec -T db psql -U "$POSTGRES_USER" -d postgres -c "
    SELECT pg_terminate_backend(pid)
    FROM pg_stat_activity
    WHERE datname = '$POSTGRES_DB' AND pid <> pg_backend_pid();
"

docker compose exec -T db psql -U "$POSTGRES_USER" -d postgres -c "DROP DATABASE IF EXISTS $POSTGRES_DB;"
docker compose exec -T db psql -U "$POSTGRES_USER" -d postgres -c "CREATE DATABASE $POSTGRES_DB OWNER $POSTGRES_USER;"

echo ""
echo "Database dropped and recreated."
echo ""
echo "Run one of these to restore schema:"
echo "  ./database/scripts/restore/full_restore.sh"
echo "  docker compose exec api alembic upgrade head"
echo ""
echo "=========================================="
