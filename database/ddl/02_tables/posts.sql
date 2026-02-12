-- Posts Table
-- Raw ingested posts from various platforms

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

COMMENT ON TABLE posts IS 'Raw ingested posts from various platforms';
COMMENT ON COLUMN posts.id IS 'Unique identifier (UUID)';
COMMENT ON COLUMN posts.platform IS 'Source platform (youtube, tier-site, etc.)';
COMMENT ON COLUMN posts.external_id IS 'Platform-specific unique ID';
COMMENT ON COLUMN posts.title IS 'Post title (if applicable)';
COMMENT ON COLUMN posts.content IS 'Full post content/body';
COMMENT ON COLUMN posts.author IS 'Content author username';
COMMENT ON COLUMN posts.url IS 'Direct URL to original content';
COMMENT ON COLUMN posts.upvotes IS 'Engagement metric (likes, upvotes, etc.)';
COMMENT ON COLUMN posts.comments_count IS 'Number of comments/replies';
COMMENT ON COLUMN posts.published_at IS 'When content was originally published';
COMMENT ON COLUMN posts.fetched_at IS 'When we ingested this content';
COMMENT ON COLUMN posts.created_at IS 'Database record creation time';
COMMENT ON COLUMN posts.updated_at IS 'Database record last update time';
