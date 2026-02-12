#!/bin/bash
# Vacuum and Analyze Script
# Reclaims storage and updates query planner statistics

set -e

# Configuration
POSTGRES_USER="${POSTGRES_USER:-communitypulse}"
POSTGRES_DB="${POSTGRES_DB:-communitypulse}"

echo "=========================================="
echo "Vacuum and Analyze"
echo "=========================================="
echo "Database: $POSTGRES_DB"
echo ""

# Check if Docker container is running
if ! docker compose ps db | grep -q "Up"; then
    echo "ERROR: Database container is not running."
    exit 1
fi

echo "[1] Running VACUUM ANALYZE on all tables..."
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "VACUUM ANALYZE;"

echo ""
echo "[2] Table statistics after vacuum..."
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
    SELECT
        schemaname,
        relname as table_name,
        n_live_tup as live_rows,
        n_dead_tup as dead_rows,
        last_vacuum,
        last_analyze
    FROM pg_stat_user_tables
    ORDER BY relname;
"

echo ""
echo "=========================================="
echo "Vacuum and analyze complete!"
echo "=========================================="
