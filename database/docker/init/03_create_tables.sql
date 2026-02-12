-- Docker Init Script: Tables
-- Runs automatically on first container start

-- Posts table
CREATE TABLE IF NOT EXISTS posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    platform platform_enum NOT NULL,
    external_id VARCHAR(255) NOT NULL,
    title VARCHAR(500),
    content TEXT,
    author VARCHAR(255),
    url VARCHAR(2048) NOT NULL,
    upvotes INTEGER NOT NULL DEFAULT 0,
    comments_count INTEGER NOT NULL DEFAULT 0,
    published_at TIMESTAMP WITH TIME ZONE,
    fetched_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Sentiment results table
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

-- Aggregations table
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

-- Feedback table
CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    topic_slug VARCHAR(255) NOT NULL,
    feedback_type VARCHAR(50) NOT NULL,
    reason VARCHAR(100),
    details TEXT,
    session_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Alembic version table
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

DO $$ BEGIN
    RAISE NOTICE 'Tables created successfully';
END $$;
