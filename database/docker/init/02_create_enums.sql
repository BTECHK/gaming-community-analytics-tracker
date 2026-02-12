-- Docker Init Script: Enum Types
-- Runs automatically on first container start

-- Platform enum
DO $$ BEGIN
    CREATE TYPE platform_enum AS ENUM (
        'reddit', 'youtube', 'official-news', 'tier-site', 'google_trends', 'guide-site'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Sentiment label enum
DO $$ BEGIN
    CREATE TYPE sentiment_label_enum AS ENUM (
        'positive', 'neutral', 'negative'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    RAISE NOTICE 'Enum types created successfully';
END $$;
