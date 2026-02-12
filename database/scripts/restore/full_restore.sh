#!/bin/bash
# Full Database Restore from DDL Scripts
# Recreates database schema from scratch using DDL files

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
DDL_DIR="$PROJECT_ROOT/database/ddl"
PERM_DIR="$PROJECT_ROOT/database/permissions"

POSTGRES_USER="${POSTGRES_USER:-communitypulse}"
POSTGRES_DB="${POSTGRES_DB:-communitypulse}"

echo "=========================================="
echo "Full Database Restore from DDL"
echo "=========================================="
echo "Database: $POSTGRES_DB"
echo "User: $POSTGRES_USER"
echo ""

# Check if Docker container is running
if ! docker compose ps db | grep -q "Up"; then
    echo "ERROR: Database container is not running."
    echo "Run: docker compose up -d db"
    exit 1
fi

# Confirm destructive operation
read -p "This will DROP and recreate all tables. Continue? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "Step 1: Dropping existing objects..."
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
    DROP TABLE IF EXISTS feedback CASCADE;
    DROP TABLE IF EXISTS sentiment_results CASCADE;
    DROP TABLE IF EXISTS aggregations CASCADE;
    DROP TABLE IF EXISTS posts CASCADE;
    DROP TABLE IF EXISTS alembic_version CASCADE;
    DROP TYPE IF EXISTS platform_enum CASCADE;
    DROP TYPE IF EXISTS sentiment_label_enum CASCADE;
"

echo "Step 2: Creating extensions..."
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$DDL_DIR/00_extensions.sql"

echo "Step 3: Creating enum types..."
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$DDL_DIR/01_enums/platform_enum.sql"
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$DDL_DIR/01_enums/sentiment_label_enum.sql"

echo "Step 4: Creating tables..."
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$DDL_DIR/02_tables/posts.sql"
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$DDL_DIR/02_tables/sentiment_results.sql"
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$DDL_DIR/02_tables/aggregations.sql"
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$DDL_DIR/02_tables/feedback.sql"
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$DDL_DIR/02_tables/alembic_version.sql"

echo "Step 5: Creating indexes..."
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$DDL_DIR/03_indexes/all_indexes.sql"

echo "Step 6: Creating constraints..."
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$DDL_DIR/04_constraints/foreign_keys.sql"

echo "Step 7: Applying permissions..."
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$PERM_DIR/01_roles.sql" 2>/dev/null || true
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$PERM_DIR/02_grants.sql"

echo ""
echo "=========================================="
echo "Database restore completed!"
echo ""
echo "Tables created:"
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\dt"
echo ""
echo "Next steps:"
echo "  - Load demo data: ./database/scripts/restore/load_demo_data.sh"
echo "  - Or restore from backup: ./database/scripts/restore/restore_from_backup.sh <file>"
echo "=========================================="
