#!/bin/bash
# Table Sizes Report Script
# Shows detailed size breakdown for all tables

set -e

# Configuration
POSTGRES_USER="${POSTGRES_USER:-communitypulse}"
POSTGRES_DB="${POSTGRES_DB:-communitypulse}"

echo "=========================================="
echo "Table Sizes Report"
echo "=========================================="
echo ""

# Check if Docker container is running
if ! docker compose ps db | grep -q "Up"; then
    echo "ERROR: Database container is not running."
    exit 1
fi

docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
    SELECT
        table_name,
        pg_size_pretty(total_bytes) AS total_size,
        pg_size_pretty(table_bytes) AS table_size,
        pg_size_pretty(index_bytes) AS index_size,
        pg_size_pretty(toast_bytes) AS toast_size,
        CASE WHEN total_bytes > 0
            THEN round(100.0 * index_bytes / total_bytes, 1)
            ELSE 0
        END AS index_pct
    FROM (
        SELECT
            relname AS table_name,
            pg_total_relation_size(c.oid) AS total_bytes,
            pg_relation_size(c.oid) AS table_bytes,
            pg_indexes_size(c.oid) AS index_bytes,
            COALESCE(pg_total_relation_size(reltoastrelid), 0) AS toast_bytes
        FROM pg_class c
        LEFT JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE relkind = 'r'
        AND n.nspname = 'public'
    ) a
    ORDER BY total_bytes DESC;
"

echo ""
echo "Database total size:"
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
    SELECT pg_size_pretty(pg_database_size('$POSTGRES_DB')) as total_size;
"
