#!/bin/bash
# Load Demo Data Script
# Populates database with sample data for testing/demos

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
DML_DIR="$PROJECT_ROOT/database/dml"

POSTGRES_USER="${POSTGRES_USER:-communitypulse}"
POSTGRES_DB="${POSTGRES_DB:-communitypulse}"

echo "=========================================="
echo "Load Demo Data"
echo "=========================================="
echo "Database: $POSTGRES_DB"
echo ""

# Check if Docker container is running
if ! docker compose ps db | grep -q "Up"; then
    echo "ERROR: Database container is not running."
    echo "Run: docker compose up -d db"
    exit 1
fi

# Check if data already exists
EXISTING=$(docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT COUNT(*) FROM aggregations")
EXISTING=$(echo "$EXISTING" | tr -d '[:space:]')

if [ "$EXISTING" -gt 0 ]; then
    echo "Database already has $EXISTING aggregations."
    read -p "Load demo data anyway? This may create duplicates. (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi
fi

echo "Loading demo data..."

# Prefer Python seed script if available (more complete data)
if docker compose exec -T api python --version &>/dev/null; then
    echo "Using Python seed script for full demo data..."
    docker compose exec -T api python scripts/seed_demo_data.py
else
    # Fallback to SQL
    echo "Using SQL seed script..."
    docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$DML_DIR/seed/demo_data.sql"
fi

echo ""
echo "=========================================="
echo "Demo data loaded!"
echo ""
echo "Record counts:"
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
    SELECT
        (SELECT COUNT(*) FROM aggregations) as topics,
        (SELECT COUNT(*) FROM posts) as posts,
        (SELECT COUNT(*) FROM sentiment_results) as sentiments,
        (SELECT COUNT(*) FROM feedback) as feedback;
"
echo "=========================================="
