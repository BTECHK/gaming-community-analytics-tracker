#!/bin/bash
# Database Health Check Script
# Checks database connectivity and basic statistics

set -e

# Configuration
POSTGRES_USER="${POSTGRES_USER:-communitypulse}"
POSTGRES_DB="${POSTGRES_DB:-communitypulse}"

echo "=========================================="
echo "Database Health Check"
echo "=========================================="
echo ""

# Check if Docker container is running
if ! docker compose ps db | grep -q "Up"; then
    echo "ERROR: Database container is not running."
    echo "Run: docker compose up -d db"
    exit 1
fi

echo "[1] Connection Test..."
if docker compose exec -T db pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"; then
    echo "    ✓ Database is accepting connections"
else
    echo "    ✗ Database connection failed"
    exit 1
fi

echo ""
echo "[2] Version Info..."
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT version();"

echo ""
echo "[3] Database Size..."
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
    SELECT pg_size_pretty(pg_database_size('$POSTGRES_DB')) as database_size;
"

echo ""
echo "[4] Table Row Counts..."
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
    SELECT
        'posts' as table_name, COUNT(*) as rows FROM posts
    UNION ALL SELECT
        'sentiment_results', COUNT(*) FROM sentiment_results
    UNION ALL SELECT
        'aggregations', COUNT(*) FROM aggregations
    UNION ALL SELECT
        'feedback', COUNT(*) FROM feedback
    ORDER BY table_name;
"

echo ""
echo "[5] Table Sizes..."
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
    SELECT
        relname as table_name,
        pg_size_pretty(pg_total_relation_size(relid)) as total_size,
        pg_size_pretty(pg_relation_size(relid)) as data_size,
        pg_size_pretty(pg_total_relation_size(relid) - pg_relation_size(relid)) as index_size
    FROM pg_catalog.pg_statio_user_tables
    ORDER BY pg_total_relation_size(relid) DESC;
"

echo ""
echo "[6] Active Connections..."
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
    SELECT
        datname,
        usename,
        state,
        COUNT(*) as connections
    FROM pg_stat_activity
    WHERE datname = '$POSTGRES_DB'
    GROUP BY datname, usename, state
    ORDER BY state;
"

echo ""
echo "[7] Recent Errors (last 24h)..."
docker compose logs --since 24h db 2>&1 | grep -i "error\|fatal" | tail -5 || echo "    No recent errors found"

echo ""
echo "=========================================="
echo "Health check complete!"
echo "=========================================="
