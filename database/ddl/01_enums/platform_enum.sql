-- Platform Enum Type
-- Defines supported data source platforms

DO $$ BEGIN
    CREATE TYPE platform_enum AS ENUM (
        'reddit',
        'youtube',
        'official-news',
        'tier-site',
        'google_trends',
        'guide-site'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

COMMENT ON TYPE platform_enum IS 'Supported data source platforms for content ingestion';
