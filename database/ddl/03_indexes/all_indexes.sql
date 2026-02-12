-- All Database Indexes
-- Performance indexes for queries

-- =============================================================================
-- Posts Table Indexes
-- =============================================================================

-- Index for filtering by platform
CREATE INDEX IF NOT EXISTS ix_posts_platform
    ON posts (platform);

-- Index for looking up by external ID
CREATE INDEX IF NOT EXISTS ix_posts_external_id
    ON posts (external_id);

-- Unique composite index to prevent duplicate imports
CREATE UNIQUE INDEX IF NOT EXISTS ix_posts_platform_external_id
    ON posts (platform, external_id);

-- Index for time-based queries
CREATE INDEX IF NOT EXISTS ix_posts_published_at
    ON posts (published_at DESC);

-- Index for fetched_at (useful for sync operations)
CREATE INDEX IF NOT EXISTS ix_posts_fetched_at
    ON posts (fetched_at DESC);

-- =============================================================================
-- Sentiment Results Table Indexes
-- =============================================================================

-- Index for joining with posts
CREATE INDEX IF NOT EXISTS ix_sentiment_results_post_id
    ON sentiment_results (post_id);

-- Index for filtering by sentiment label
CREATE INDEX IF NOT EXISTS ix_sentiment_results_label
    ON sentiment_results (label);

-- Index for finding expired analyses
CREATE INDEX IF NOT EXISTS ix_sentiment_results_expires_at
    ON sentiment_results (expires_at)
    WHERE expires_at IS NOT NULL;

-- =============================================================================
-- Aggregations Table Indexes
-- =============================================================================

-- Index for topic name searches
CREATE INDEX IF NOT EXISTS ix_aggregations_topic_name
    ON aggregations (topic_name);

-- Index for time-based queries
CREATE INDEX IF NOT EXISTS ix_aggregations_period_end
    ON aggregations (period_end DESC);

-- Index for patch version filtering
CREATE INDEX IF NOT EXISTS ix_aggregations_patch_version
    ON aggregations (patch_version)
    WHERE patch_version IS NOT NULL;

-- =============================================================================
-- Feedback Table Indexes
-- =============================================================================

-- Index for filtering by topic
CREATE INDEX IF NOT EXISTS ix_feedback_topic_slug
    ON feedback (topic_slug);

-- Index for session lookups
CREATE INDEX IF NOT EXISTS ix_feedback_session_id
    ON feedback (session_id);

-- Index for feedback type filtering
CREATE INDEX IF NOT EXISTS ix_feedback_type
    ON feedback (feedback_type);

-- Index for time-based analytics
CREATE INDEX IF NOT EXISTS ix_feedback_created_at
    ON feedback (created_at DESC);
