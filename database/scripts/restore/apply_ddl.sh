#!/bin/bash
# Apply DDL Scripts
# Runs all DDL scripts in order (non-destructive, uses IF NOT EXISTS)

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
DDL_DIR="$PROJECT_ROOT/database/ddl"

POSTGRES_USER="${POSTGRES_USER:-communitypulse}"
POSTGRES_DB="${POSTGRES_DB:-communitypulse}"

echo "=========================================="
echo "Apply DDL Scripts"
echo "=========================================="
echo "Database: $POSTGRES_DB"
echo "DDL Directory: $DDL_DIR"
echo ""

# Check if Docker container is running
if ! docker compose ps db | grep -q "Up"; then
    echo "ERROR: Database container is not running."
    echo "Run: docker compose up -d db"
    exit 1
fi

echo "Applying DDL scripts (non-destructive)..."
echo ""

echo "[1/6] Extensions..."
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$DDL_DIR/00_extensions.sql"

echo "[2/6] Enum types..."
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$DDL_DIR/01_enums/platform_enum.sql"
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$DDL_DIR/01_enums/sentiment_label_enum.sql"

echo "[3/6] Tables..."
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$DDL_DIR/02_tables/posts.sql"
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$DDL_DIR/02_tables/sentiment_results.sql"
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$DDL_DIR/02_tables/aggregations.sql"
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$DDL_DIR/02_tables/feedback.sql"
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$DDL_DIR/02_tables/alembic_version.sql"

echo "[4/6] Indexes..."
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$DDL_DIR/03_indexes/all_indexes.sql"

echo "[5/6] Constraints..."
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$DDL_DIR/04_constraints/foreign_keys.sql"

echo "[6/6] Verifying..."
TABLES=$(docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
TABLES=$(echo "$TABLES" | tr -d '[:space:]')

echo ""
echo "=========================================="
echo "DDL applied successfully!"
echo "Tables in database: $TABLES"
echo "=========================================="
