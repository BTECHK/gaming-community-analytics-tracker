# Database Objects

Stored functions, triggers, and views.

## Current Status

No stored procedures, triggers, or views are currently used.
This folder is prepared for future use.

## Folders

- `functions/` - Stored functions and procedures
- `triggers/` - Database triggers
- `views/` - Views and materialized views

## Examples (for future use)

### Function Example
```sql
-- functions/update_timestamp.sql
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### Trigger Example
```sql
-- triggers/posts_updated_at.sql
CREATE TRIGGER posts_updated_at_trigger
    BEFORE UPDATE ON posts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
```

### View Example
```sql
-- views/topic_summary.sql
CREATE OR REPLACE VIEW topic_summary AS
SELECT
    topic_name,
    topic_slug,
    post_count,
    sentiment_positive,
    sentiment_negative,
    period_end as last_updated
FROM aggregations
ORDER BY period_end DESC;
```

## Adding Objects

1. Create SQL file in appropriate folder
2. Add to DDL execution order in `../ddl/README.md`
3. Update restore scripts if needed
