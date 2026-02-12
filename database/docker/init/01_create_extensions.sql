-- Docker Init Script: Extensions
-- Runs automatically on first container start

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Log completion
DO $$ BEGIN
    RAISE NOTICE 'Extensions created successfully';
END $$;
