-- Sentiment Label Enum Type
-- Defines sentiment classification labels

DO $$ BEGIN
    CREATE TYPE sentiment_label_enum AS ENUM (
        'positive',
        'neutral',
        'negative'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

COMMENT ON TYPE sentiment_label_enum IS 'Sentiment classification labels for NLP analysis';
