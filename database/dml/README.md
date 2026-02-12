# DML - Data Manipulation Language

Data scripts for gaming-community-analytics-tracker database.

## Folders

### seed/
Demo and test data for development and demonstrations.
- `demo_data.sql` - Full demo dataset (topics, posts, sentiment)

### reference/
Static reference data that should exist in all environments.
- Currently none required (enums handle reference values)

## Usage

### Load Demo Data (Recommended: Use Python Script)
```bash
docker compose exec backend python scripts/seed_demo_data.py
```

### Load Demo Data (SQL - for restore scenarios)
```bash
docker compose exec -T db psql -U communitypulse -d communitypulse < database/dml/seed/demo_data.sql
```

### Export Current Data
```bash
# Export data only (no schema)
docker compose exec db pg_dump -U communitypulse -d communitypulse \
    --data-only \
    --exclude-table=alembic_version \
    > database/backups/data_$(date +%Y-%m-%d).sql
```

## Data Loading Order

When restoring from SQL files:
1. DDL must be applied first (tables must exist)
2. Reference data (if any)
3. Seed data or production data backup

## Notes

- Demo data is safe to run multiple times (checks for existing data)
- Python seed script provides more realistic randomized data
- SQL seed script is for pure-SQL restore scenarios
