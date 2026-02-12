-- Database Roles for gaming-community-analytics-tracker
-- Run this to set up role-based access control

-- =============================================================================
-- Application Role (default connection)
-- =============================================================================

-- Main application role (may already exist from Docker setup)
DO $$ BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'communitypulse') THEN
        CREATE ROLE communitypulse WITH LOGIN PASSWORD 'CHANGE_IN_PRODUCTION';
    END IF;
END $$;

COMMENT ON ROLE communitypulse IS 'Primary application user for CommunityPulse API';

-- =============================================================================
-- Read-Only Role (reporting, analytics, dashboards)
-- =============================================================================

DO $$ BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'communitypulse_readonly') THEN
        CREATE ROLE communitypulse_readonly WITH LOGIN PASSWORD 'CHANGE_IN_PRODUCTION';
    END IF;
END $$;

COMMENT ON ROLE communitypulse_readonly IS 'Read-only access for reporting and analytics';

-- =============================================================================
-- Admin Role (migrations, maintenance)
-- =============================================================================

DO $$ BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'communitypulse_admin') THEN
        CREATE ROLE communitypulse_admin WITH LOGIN PASSWORD 'CHANGE_IN_PRODUCTION';
    END IF;
END $$;

COMMENT ON ROLE communitypulse_admin IS 'Admin role for DDL operations and migrations';

-- =============================================================================
-- Service Account Role (background jobs, workers)
-- =============================================================================

DO $$ BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'communitypulse_worker') THEN
        CREATE ROLE communitypulse_worker WITH LOGIN PASSWORD 'CHANGE_IN_PRODUCTION';
    END IF;
END $$;

COMMENT ON ROLE communitypulse_worker IS 'Service account for background workers and jobs';

-- =============================================================================
-- Grant database access to all roles
-- =============================================================================

GRANT CONNECT ON DATABASE communitypulse TO communitypulse;
GRANT CONNECT ON DATABASE communitypulse TO communitypulse_readonly;
GRANT CONNECT ON DATABASE communitypulse TO communitypulse_admin;
GRANT CONNECT ON DATABASE communitypulse TO communitypulse_worker;

-- Grant schema usage
GRANT USAGE ON SCHEMA public TO communitypulse;
GRANT USAGE ON SCHEMA public TO communitypulse_readonly;
GRANT USAGE ON SCHEMA public TO communitypulse_admin;
GRANT USAGE ON SCHEMA public TO communitypulse_worker;
