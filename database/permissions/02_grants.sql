-- Permission Grants for gaming-community-analytics-tracker
-- Run AFTER 01_roles.sql and AFTER DDL scripts

-- =============================================================================
-- Application Role Grants (communitypulse)
-- Full CRUD on all application tables
-- =============================================================================

-- Table permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE posts TO communitypulse;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE sentiment_results TO communitypulse;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE aggregations TO communitypulse;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE feedback TO communitypulse;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE alembic_version TO communitypulse;

-- Sequence permissions (for serial columns if any)
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO communitypulse;

-- =============================================================================
-- Read-Only Role Grants (communitypulse_readonly)
-- SELECT only on all tables
-- =============================================================================

GRANT SELECT ON TABLE posts TO communitypulse_readonly;
GRANT SELECT ON TABLE sentiment_results TO communitypulse_readonly;
GRANT SELECT ON TABLE aggregations TO communitypulse_readonly;
GRANT SELECT ON TABLE feedback TO communitypulse_readonly;
-- Explicitly NO access to alembic_version for readonly

-- =============================================================================
-- Admin Role Grants (communitypulse_admin)
-- Full access including DDL
-- =============================================================================

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO communitypulse_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO communitypulse_admin;

-- Allow creating/dropping objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL PRIVILEGES ON TABLES TO communitypulse_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL PRIVILEGES ON SEQUENCES TO communitypulse_admin;

-- =============================================================================
-- Worker Role Grants (communitypulse_worker)
-- Full CRUD but limited to specific tables
-- =============================================================================

-- Workers can read/write posts and sentiment
GRANT SELECT, INSERT, UPDATE ON TABLE posts TO communitypulse_worker;
GRANT SELECT, INSERT, UPDATE ON TABLE sentiment_results TO communitypulse_worker;
GRANT SELECT, INSERT, UPDATE ON TABLE aggregations TO communitypulse_worker;

-- Workers cannot modify feedback (user-facing only)
GRANT SELECT ON TABLE feedback TO communitypulse_worker;

-- Sequence access
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO communitypulse_worker;

-- =============================================================================
-- Future Tables (apply grants automatically)
-- =============================================================================

-- Application user gets CRUD on future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO communitypulse;

-- Read-only gets SELECT on future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT ON TABLES TO communitypulse_readonly;

-- Worker gets limited access on future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE ON TABLES TO communitypulse_worker;

-- =============================================================================
-- Row Level Security (RLS) - Currently disabled
-- Uncomment if multi-tenant support is needed
-- =============================================================================

-- Example RLS policy for feedback table:
-- ALTER TABLE feedback ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY feedback_session_policy ON feedback
--     USING (session_id = current_setting('app.session_id', true));
