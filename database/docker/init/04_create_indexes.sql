-- Docker Init Script: Indexes
-- Runs automatically on first container start

-- Posts indexes
CREATE INDEX IF NOT EXISTS ix_posts_platform ON posts (platform);
CREATE INDEX IF NOT EXISTS ix_posts_external_id ON posts (external_id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_posts_platform_external_id ON posts (platform, external_id);
CREATE INDEX IF NOT EXISTS ix_posts_published_at ON posts (published_at DESC);
CREATE INDEX IF NOT EXISTS ix_posts_fetched_at ON posts (fetched_at DESC);

-- Sentiment results indexes
CREATE INDEX IF NOT EXISTS ix_sentiment_results_post_id ON sentiment_results (post_id);
CREATE INDEX IF NOT EXISTS ix_sentiment_results_label ON sentiment_results (label);

-- Aggregations indexes
CREATE INDEX IF NOT EXISTS ix_aggregations_topic_name ON aggregations (topic_name);
CREATE INDEX IF NOT EXISTS ix_aggregations_period_end ON aggregations (period_end DESC);

-- Feedback indexes
CREATE INDEX IF NOT EXISTS ix_feedback_topic_slug ON feedback (topic_slug);
CREATE INDEX IF NOT EXISTS ix_feedback_session_id ON feedback (session_id);
CREATE INDEX IF NOT EXISTS ix_feedback_type ON feedback (feedback_type);

DO $$ BEGIN
    RAISE NOTICE 'Indexes created successfully';
END $$;
