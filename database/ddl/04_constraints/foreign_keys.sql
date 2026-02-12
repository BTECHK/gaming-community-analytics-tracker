-- Foreign Key Constraints
-- Run after all tables are created

-- =============================================================================
-- Sentiment Results -> Posts
-- =============================================================================

-- Add foreign key if not exists
DO $$ BEGIN
    ALTER TABLE sentiment_results
        ADD CONSTRAINT fk_sentiment_results_post_id
        FOREIGN KEY (post_id) REFERENCES posts(id)
        ON DELETE CASCADE;
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- =============================================================================
-- Unique Constraints
-- =============================================================================

-- Unique topic slug in aggregations
DO $$ BEGIN
    ALTER TABLE aggregations
        ADD CONSTRAINT uq_aggregations_topic_slug
        UNIQUE (topic_slug);
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- =============================================================================
-- Check Constraints
-- =============================================================================

-- Sentiment percentages should be between 0 and 1
DO $$ BEGIN
    ALTER TABLE aggregations
        ADD CONSTRAINT chk_sentiment_positive_range
        CHECK (sentiment_positive >= 0 AND sentiment_positive <= 1);
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE aggregations
        ADD CONSTRAINT chk_sentiment_neutral_range
        CHECK (sentiment_neutral >= 0 AND sentiment_neutral <= 1);
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE aggregations
        ADD CONSTRAINT chk_sentiment_negative_range
        CHECK (sentiment_negative >= 0 AND sentiment_negative <= 1);
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Confidence score should be between 0 and 1
DO $$ BEGIN
    ALTER TABLE sentiment_results
        ADD CONSTRAINT chk_confidence_range
        CHECK (confidence >= 0 AND confidence <= 1);
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Post count should be non-negative
DO $$ BEGIN
    ALTER TABLE aggregations
        ADD CONSTRAINT chk_post_count_positive
        CHECK (post_count >= 0);
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;
