-- Aggregations Table
-- Aggregated topic summaries with sentiment breakdowns

CREATE TABLE IF NOT EXISTS aggregations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    topic_name VARCHAR(255) NOT NULL,
    topic_slug VARCHAR(255) NOT NULL,
    sentiment_positive FLOAT NOT NULL DEFAULT 0.0,
    sentiment_neutral FLOAT NOT NULL DEFAULT 0.0,
    sentiment_negative FLOAT NOT NULL DEFAULT 0.0,
    summary TEXT,
    representative_quotes JSONB,
    post_count INTEGER NOT NULL DEFAULT 0,
    source_mix JSONB,
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    patch_version VARCHAR(20),
    confidence_score FLOAT,
    sentiment_explanation JSONB,
    confidence_breakdown JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE aggregations IS 'Aggregated topic summaries with sentiment breakdowns';
COMMENT ON COLUMN aggregations.id IS 'Unique identifier (UUID)';
COMMENT ON COLUMN aggregations.topic_name IS 'Human-readable topic name';
COMMENT ON COLUMN aggregations.topic_slug IS 'URL-safe topic identifier';
COMMENT ON COLUMN aggregations.sentiment_positive IS 'Percentage of positive sentiment (0-1)';
COMMENT ON COLUMN aggregations.sentiment_neutral IS 'Percentage of neutral sentiment (0-1)';
COMMENT ON COLUMN aggregations.sentiment_negative IS 'Percentage of negative sentiment (0-1)';
COMMENT ON COLUMN aggregations.summary IS 'AI-generated summary of the topic';
COMMENT ON COLUMN aggregations.representative_quotes IS 'Sample quotes as JSON array';
COMMENT ON COLUMN aggregations.post_count IS 'Number of posts in this aggregation';
COMMENT ON COLUMN aggregations.source_mix IS 'Breakdown by platform as JSON';
COMMENT ON COLUMN aggregations.period_start IS 'Start of aggregation time window';
COMMENT ON COLUMN aggregations.period_end IS 'End of aggregation time window';
COMMENT ON COLUMN aggregations.patch_version IS 'Game patch version (e.g., "14.3")';
COMMENT ON COLUMN aggregations.confidence_score IS 'Overall confidence in aggregation';
COMMENT ON COLUMN aggregations.sentiment_explanation IS 'Detailed sentiment reasoning as JSON';
COMMENT ON COLUMN aggregations.confidence_breakdown IS 'Per-factor confidence scores as JSON';
COMMENT ON COLUMN aggregations.created_at IS 'Database record creation time';
COMMENT ON COLUMN aggregations.updated_at IS 'Database record last update time';
