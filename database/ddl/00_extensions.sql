-- PostgreSQL Extensions for gaming-community-analytics-tracker
-- Run this first before any other DDL

-- UUID generation (used for all primary keys)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Full-text search (for future content search)
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Note: Additional extensions can be added here as needed
-- Common ones for future consideration:
-- CREATE EXTENSION IF NOT EXISTS "hstore";     -- Key-value storage
-- CREATE EXTENSION IF NOT EXISTS "citext";     -- Case-insensitive text
