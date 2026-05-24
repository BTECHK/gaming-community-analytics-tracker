-- Demo Data Seed Script
-- Run this AFTER DDL to populate with example data
-- Safe to run multiple times (uses ON CONFLICT DO NOTHING)

-- Note: For full demo experience, use the Python script instead:
-- docker compose exec backend python scripts/seed_demo_data.py

-- This SQL file provides a minimal dataset for pure-SQL restore scenarios.

DO $$
DECLARE
    v_now TIMESTAMP WITH TIME ZONE := NOW();
    v_period_start TIMESTAMP WITH TIME ZONE := NOW() - INTERVAL '7 days';
    v_agg_id UUID;
BEGIN
    -- Check if data already exists
    IF EXISTS (SELECT 1 FROM aggregations LIMIT 1) THEN
        RAISE NOTICE 'Data already exists, skipping seed';
        RETURN;
    END IF;

    RAISE NOTICE 'Seeding demo data...';

    -- =========================================================================
    -- Aggregations (Topics)
    -- =========================================================================

    INSERT INTO aggregations (
        id, topic_name, topic_slug,
        sentiment_positive, sentiment_neutral, sentiment_negative,
        summary, representative_quotes, post_count, source_mix,
        period_start, period_end, patch_version, confidence_score,
        created_at, updated_at
    ) VALUES
    (
        uuid_generate_v4(),
        'Character Balance',
        'character-balance',
        0.25, 0.35, 0.40,
        'Players are discussing recent balance changes to two top-tier characters. The community is divided on whether the nerfs went far enough.',
        '[{"text": "the recent nerfs finally happened but it still feels strong", "platform": "youtube", "sentiment": "negative", "confidence": 0.85}]'::jsonb,
        156,
        '{"youtube": 70, "tier-site": 20, "official-news": 10}'::jsonb,
        v_period_start, v_now, '4.2', 0.82,
        v_now, v_now
    ),
    (
        uuid_generate_v4(),
        'Ranked & Matchmaking',
        'ranked-matchmaking',
        0.20, 0.30, 0.50,
        'Matchmaking quality in ranked continues to be a hot topic. Players report issues with team balance and autofill.',
        '[{"text": "Getting autofilled in 80% of my games", "platform": "youtube", "sentiment": "negative", "confidence": 0.91}]'::jsonb,
        203,
        '{"youtube": 65, "tier-site": 25, "official-news": 10}'::jsonb,
        v_period_start, v_now, '4.2', 0.78,
        v_now, v_now
    ),
    (
        uuid_generate_v4(),
        'New Skins',
        'new-skins',
        0.65, 0.25, 0.10,
        'The new Solar Flare skin line is receiving overwhelmingly positive reception.',
        '[{"text": "the Solar Flare set might be the best legendary of the year", "platform": "youtube", "sentiment": "positive", "confidence": 0.95}]'::jsonb,
        89,
        '{"youtube": 80, "tier-site": 5, "official-news": 15}'::jsonb,
        v_period_start, v_now, '4.2', 0.88,
        v_now, v_now
    ),
    (
        uuid_generate_v4(),
        'Pro Play & Esports',
        'pro-play-esports',
        0.55, 0.35, 0.10,
        'Global Finals 2026 bracket predictions are generating excitement.',
        '[{"text": "Team Apex looking dominant, showing why they are the GOAT", "platform": "youtube", "sentiment": "positive", "confidence": 0.89}]'::jsonb,
        134,
        '{"youtube": 75, "tier-site": 10, "official-news": 15}'::jsonb,
        v_period_start, v_now, '4.2', 0.85,
        v_now, v_now
    ),
    (
        uuid_generate_v4(),
        'Client & Performance',
        'client-performance',
        0.15, 0.25, 0.60,
        'Client performance issues persist despite recent patches.',
        '[{"text": "Client froze in the match lobby, lost rank points for dodging", "platform": "youtube", "sentiment": "negative", "confidence": 0.92}]'::jsonb,
        178,
        '{"youtube": 70, "tier-site": 15, "official-news": 15}'::jsonb,
        v_period_start, v_now, '4.2', 0.79,
        v_now, v_now
    );

    -- =========================================================================
    -- Sample Posts
    -- =========================================================================

    INSERT INTO posts (
        id, platform, external_id, title, content, author, url,
        upvotes, comments_count, published_at, fetched_at, created_at, updated_at
    ) VALUES
    (
        uuid_generate_v4(), 'youtube', 'demo_yt_001',
        'Balance Nerfs Finally Hit! Still Too Strong?',
        'Breaking down the latest balance changes and whether they actually matter in ranked queue.',
        'DemoUser1', 'https://youtube.com/watch?v=demo001',
        15420, 234, v_now - INTERVAL '2 days', v_now, v_now, v_now
    ),
    (
        uuid_generate_v4(), 'youtube', 'demo_yt_002',
        'Solar Flare Skin Spotlight',
        'Full preview of the new legendary cosmetic with all color variants.',
        'DemoUser2', 'https://youtube.com/watch?v=demo002',
        45600, 567, v_now - INTERVAL '1 day', v_now, v_now, v_now
    ),
    (
        uuid_generate_v4(), 'youtube', 'demo_yt_003',
        'Team Apex vs Team Vortex - Global Finals Preview',
        'Breaking down the matchup for the biggest game of the year.',
        'DemoUser3', 'https://youtube.com/watch?v=demo003',
        67800, 892, v_now - INTERVAL '3 days', v_now, v_now, v_now
    ),
    (
        uuid_generate_v4(), 'tier-site', 'demo_tier-site_001',
        'Best Character Tier List Patch 4.2',
        'Updated tier list for the current patch with all the meta picks.',
        'TierSite', 'https://tier-site/tierlist',
        0, 0, v_now - INTERVAL '1 day', v_now, v_now, v_now
    );

    -- =========================================================================
    -- Sentiment Results for Posts
    -- =========================================================================

    INSERT INTO sentiment_results (
        id, post_id, label, confidence, scores, topics,
        is_toxic, model_name, model_version, analyzed_at
    )
    SELECT
        uuid_generate_v4(),
        p.id,
        (ARRAY['positive', 'neutral', 'negative']::sentiment_label_enum[])[floor(random() * 3 + 1)],
        0.75 + random() * 0.2,
        '{"positive": 0.3, "neutral": 0.4, "negative": 0.3}'::jsonb,
        '["demo"]'::jsonb,
        false,
        'demo-model',
        '1.0.0',
        v_now
    FROM posts p
    WHERE p.external_id LIKE 'demo_%';

    RAISE NOTICE 'Demo data seeded successfully!';
END $$;
