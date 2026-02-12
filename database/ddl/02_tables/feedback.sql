-- Feedback Table
-- User feedback on topic summaries

CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    topic_slug VARCHAR(255) NOT NULL,
    feedback_type VARCHAR(50) NOT NULL,
    reason VARCHAR(100),
    details TEXT,
    session_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE feedback IS 'User feedback on topic summaries';
COMMENT ON COLUMN feedback.id IS 'Unique identifier (UUID)';
COMMENT ON COLUMN feedback.topic_slug IS 'Topic this feedback relates to';
COMMENT ON COLUMN feedback.feedback_type IS 'Type of feedback (upvote, downvote, report)';
COMMENT ON COLUMN feedback.reason IS 'Reason category for downvotes/reports';
COMMENT ON COLUMN feedback.details IS 'Free-form feedback details';
COMMENT ON COLUMN feedback.session_id IS 'Anonymous session identifier';
COMMENT ON COLUMN feedback.created_at IS 'When feedback was submitted';
