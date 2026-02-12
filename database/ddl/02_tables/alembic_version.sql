-- Alembic Version Table
-- Tracks applied database migrations

CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

COMMENT ON TABLE alembic_version IS 'Alembic migration version tracking';

-- Set to latest migration version after full DDL restore
-- This tells Alembic the schema is up to date
INSERT INTO alembic_version (version_num) VALUES ('003')
ON CONFLICT (version_num) DO NOTHING;
