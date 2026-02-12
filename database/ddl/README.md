# DDL - Data Definition Language

Schema definitions for gaming-community-analytics-tracker database.

## Execution Order

Scripts must be executed in this order due to dependencies:

1. `00_extensions.sql` - PostgreSQL extensions (uuid-ossp, etc.)
2. `01_enums/*.sql` - Custom enum types
3. `02_tables/*.sql` - Table definitions (no foreign keys)
4. `03_indexes/*.sql` - Index definitions
5. `04_constraints/*.sql` - Foreign keys and constraints

## Running All DDL

```bash
# From project root, in Docker:
docker compose exec -T db psql -U communitypulse -d communitypulse < database/ddl/00_extensions.sql
docker compose exec -T db psql -U communitypulse -d communitypulse < database/ddl/01_enums/platform_enum.sql
docker compose exec -T db psql -U communitypulse -d communitypulse < database/ddl/01_enums/sentiment_label_enum.sql
docker compose exec -T db psql -U communitypulse -d communitypulse < database/ddl/02_tables/posts.sql
docker compose exec -T db psql -U communitypulse -d communitypulse < database/ddl/02_tables/sentiment_results.sql
docker compose exec -T db psql -U communitypulse -d communitypulse < database/ddl/02_tables/aggregations.sql
docker compose exec -T db psql -U communitypulse -d communitypulse < database/ddl/02_tables/feedback.sql
docker compose exec -T db psql -U communitypulse -d communitypulse < database/ddl/03_indexes/all_indexes.sql
docker compose exec -T db psql -U communitypulse -d communitypulse < database/ddl/04_constraints/foreign_keys.sql

# Or use the restore script:
../scripts/restore/apply_ddl.sh
```

## Relationship to Alembic

These SQL files are extracted from Alembic migrations for backup purposes.
During development, use Alembic for schema changes:

```bash
docker compose exec api alembic upgrade head
```

## Schema Diagram

```
┌─────────────────┐     ┌─────────────────────┐
│     posts       │     │  sentiment_results  │
├─────────────────┤     ├─────────────────────┤
│ id (PK)         │◄────│ post_id (FK)        │
│ platform        │     │ id (PK)             │
│ external_id     │     │ label               │
│ title           │     │ confidence          │
│ content         │     │ scores              │
│ author          │     │ topics              │
│ url             │     │ is_toxic            │
│ upvotes         │     │ model_name          │
│ comments_count  │     │ analyzed_at         │
│ published_at    │     └─────────────────────┘
│ fetched_at      │
│ created_at      │
│ updated_at      │
└─────────────────┘

┌─────────────────┐     ┌─────────────────────┐
│  aggregations   │     │      feedback       │
├─────────────────┤     ├─────────────────────┤
│ id (PK)         │     │ id (PK)             │
│ topic_name      │     │ topic_slug          │
│ topic_slug (UQ) │     │ feedback_type       │
│ sentiment_*     │     │ reason              │
│ summary         │     │ details             │
│ quotes          │     │ session_id          │
│ post_count      │     │ created_at          │
│ source_mix      │     └─────────────────────┘
│ period_*        │
│ patch_version   │
│ confidence_*    │
│ explanation     │
│ created_at      │
│ updated_at      │
└─────────────────┘
```
