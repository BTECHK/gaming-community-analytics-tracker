-- Docker Init Script: Constraints
-- Runs automatically on first container start

-- Foreign key: sentiment_results -> posts
DO $$ BEGIN
    ALTER TABLE sentiment_results
        ADD CONSTRAINT fk_sentiment_results_post_id
        FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Unique constraint: aggregations.topic_slug
DO $$ BEGIN
    ALTER TABLE aggregations
        ADD CONSTRAINT uq_aggregations_topic_slug UNIQUE (topic_slug);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Check constraints
DO $$ BEGIN
    ALTER TABLE aggregations ADD CONSTRAINT chk_sentiment_positive_range
        CHECK (sentiment_positive >= 0 AND sentiment_positive <= 1);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE aggregations ADD CONSTRAINT chk_sentiment_neutral_range
        CHECK (sentiment_neutral >= 0 AND sentiment_neutral <= 1);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE aggregations ADD CONSTRAINT chk_sentiment_negative_range
        CHECK (sentiment_negative >= 0 AND sentiment_negative <= 1);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE sentiment_results ADD CONSTRAINT chk_confidence_range
        CHECK (confidence >= 0 AND confidence <= 1);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Set alembic version to latest
INSERT INTO alembic_version (version_num) VALUES ('003')
ON CONFLICT (version_num) DO NOTHING;

DO $$ BEGIN
    RAISE NOTICE 'Constraints created successfully';
    RAISE NOTICE 'Database initialization complete!';
END $$;
