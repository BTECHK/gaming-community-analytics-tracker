-- Sentiment Results Table
-- NLP analysis results for posts

CREATE TABLE IF NOT EXISTS sentiment_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id UUID NOT NULL,
    label sentiment_label_enum NOT NULL,
    confidence FLOAT NOT NULL,
    scores JSONB,
    topics JSONB,
    is_toxic BOOLEAN NOT NULL DEFAULT FALSE,
    toxicity_score FLOAT,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50),
    analyzed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

COMMENT ON TABLE sentiment_results IS 'NLP analysis results for posts';
COMMENT ON COLUMN sentiment_results.id IS 'Unique identifier (UUID)';
COMMENT ON COLUMN sentiment_results.post_id IS 'Reference to analyzed post';
COMMENT ON COLUMN sentiment_results.label IS 'Sentiment classification (positive/neutral/negative)';
COMMENT ON COLUMN sentiment_results.confidence IS 'Model confidence score (0-1)';
COMMENT ON COLUMN sentiment_results.scores IS 'Detailed scores per label as JSON';
COMMENT ON COLUMN sentiment_results.topics IS 'Extracted topics as JSON array';
COMMENT ON COLUMN sentiment_results.is_toxic IS 'Whether content is flagged as toxic';
COMMENT ON COLUMN sentiment_results.toxicity_score IS 'Toxicity confidence score';
COMMENT ON COLUMN sentiment_results.model_name IS 'NLP model used for analysis';
COMMENT ON COLUMN sentiment_results.model_version IS 'Model version identifier';
COMMENT ON COLUMN sentiment_results.analyzed_at IS 'When analysis was performed';
COMMENT ON COLUMN sentiment_results.expires_at IS 'When analysis should be refreshed';
