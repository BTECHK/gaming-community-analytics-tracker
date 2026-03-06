"""Integration test: ingest → NLP → aggregation end-to-end pipeline.

Validates that the full pipeline works without Docker by using
SQLite + MockValkey + mocked NLP models.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Post, Platform, SentimentResult, SentimentLabel, Aggregation
from app.nlp.service import NLPService
from app.nlp.sentiment import SentimentScore
from app.nlp.topics import TopicResult
from app.nlp.toxicity import ToxicityResult
from app.dashboard.service import AggregationService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_post(
    title: str = "the game discussion",
    content: str = "Great changes in the latest patch",
    platform: Platform = Platform.REDDIT,
) -> Post:
    now = datetime.now(timezone.utc)
    return Post(
        id=str(uuid4()),
        platform=platform,
        external_id=str(uuid4()),
        title=title,
        content=content,
        author="player1",
        url="https://reddit.com/r/gamecommunity/test",
        upvotes=10,
        comments_count=5,
        published_at=now,
        fetched_at=now,
        created_at=now,
        updated_at=now,
    )


# ---------------------------------------------------------------------------
# Full pipeline: ingest → NLP → verify DB writes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_full_pipeline_ingest_nlp_verify(test_session: AsyncSession):
    """Insert posts → run NLP with mocked models → verify sentiment in DB."""
    # 1. Simulate ingestion: insert posts
    posts = [
        _make_post("Patch 16.2 is great", "Loving the balance changes", Platform.REDDIT),
        _make_post("New champion release", "The kit looks interesting", Platform.YOUTUBE),
        _make_post("Matchmaking issues", "Queue times are too long", Platform.REDDIT),
        _make_post("Ranked changes", "The LP system needs work", Platform.TierSite),
    ]
    for p in posts:
        test_session.add(p)
    await test_session.commit()

    # 2. Mock NLP models
    sentiments = [
        SentimentScore("positive", 0.92, {"positive": 0.92, "neutral": 0.05, "negative": 0.03}),
        SentimentScore("positive", 0.85, {"positive": 0.85, "neutral": 0.10, "negative": 0.05}),
        SentimentScore("negative", 0.78, {"positive": 0.10, "neutral": 0.12, "negative": 0.78}),
        SentimentScore("negative", 0.72, {"positive": 0.15, "neutral": 0.13, "negative": 0.72}),
    ]
    topics = [
        TopicResult(["balance"], [0], [0.9], ["Balance"], [["nerf", "buff"]]),
        TopicResult(["champion-release"], [1], [0.85], ["Champion Release"], [["kit", "abilities"]]),
        TopicResult(["matchmaking"], [2], [0.8], ["Matchmaking"], [["queue", "mmr"]]),
        TopicResult(["ranked"], [3], [0.75], ["Ranked"], [["lp", "ladder"]]),
    ]
    toxicities = [
        ToxicityResult(False, 0.05, {"toxicity": 0.05}),
        ToxicityResult(False, 0.03, {"toxicity": 0.03}),
        ToxicityResult(False, 0.15, {"toxicity": 0.15}),
        ToxicityResult(False, 0.10, {"toxicity": 0.10}),
    ]

    mock_analyzer = MagicMock()
    mock_analyzer.analyze_batch.return_value = sentiments
    mock_analyzer.model_name = "test-roberta"

    mock_topic = MagicMock()
    mock_topic.detect_batch.return_value = topics

    mock_toxicity = MagicMock()
    mock_toxicity.detect_batch.return_value = toxicities

    # 3. Run NLP processing
    svc = NLPService(
        test_session,
        analyzer=mock_analyzer,
        topic_detector=mock_topic,
        toxicity_detector=mock_toxicity,
    )

    with patch("app.nlp.service.get_model_breaker") as mock_breaker_fn:
        breaker = MagicMock()
        breaker.call.side_effect = lambda fn, *a, **kw: fn(*a, **kw)
        mock_breaker_fn.return_value = breaker

        result = await svc.process_batch()

    # 4. Verify processing result
    assert result["processed"] == 4
    assert result["status"] == "complete"

    # 5. Verify sentiment results in DB
    sr_query = await test_session.execute(select(SentimentResult))
    sentiment_results = sr_query.scalars().all()
    assert len(sentiment_results) == 4

    labels = {sr.label for sr in sentiment_results}
    assert SentimentLabel.positive in labels
    assert SentimentLabel.negative in labels

    # Verify each result has expected fields
    for sr in sentiment_results:
        assert sr.confidence > 0
        assert sr.model_name == "test-roberta"
        assert sr.analyzed_at is not None
        assert sr.expires_at is not None
        assert sr.topics is not None


@pytest.mark.asyncio
async def test_full_pipeline_nlp_then_aggregation(test_session: AsyncSession):
    """Insert posts → NLP → aggregation picks up processed posts."""
    # 1. Insert posts all about the same topic ("balance")
    posts = []
    for i in range(5):
        p = _make_post(
            title=f"Balance discussion {i}",
            content=f"The latest balance changes are {'great' if i % 2 == 0 else 'terrible'}",
            platform=Platform.REDDIT if i < 3 else Platform.YOUTUBE,
        )
        posts.append(p)
        test_session.add(p)
    await test_session.commit()

    # 2. Mock NLP models — all posts about "balance" topic
    sentiments = [
        SentimentScore("positive", 0.88, {"positive": 0.88, "neutral": 0.07, "negative": 0.05}),
        SentimentScore("negative", 0.75, {"positive": 0.10, "neutral": 0.15, "negative": 0.75}),
        SentimentScore("positive", 0.90, {"positive": 0.90, "neutral": 0.06, "negative": 0.04}),
        SentimentScore("negative", 0.80, {"positive": 0.08, "neutral": 0.12, "negative": 0.80}),
        SentimentScore("positive", 0.85, {"positive": 0.85, "neutral": 0.10, "negative": 0.05}),
    ]
    topics = [
        TopicResult(["balance"], [0], [0.9], ["Balance"], [["nerf", "buff"]])
        for _ in posts
    ]
    toxicities = [ToxicityResult(False, 0.05, {"toxicity": 0.05}) for _ in posts]

    mock_analyzer = MagicMock()
    mock_analyzer.analyze_batch.return_value = sentiments
    mock_analyzer.model_name = "test-roberta"

    mock_topic = MagicMock()
    mock_topic.detect_batch.return_value = topics

    mock_toxicity = MagicMock()
    mock_toxicity.detect_batch.return_value = toxicities

    # 3. Run NLP
    svc = NLPService(
        test_session,
        analyzer=mock_analyzer,
        topic_detector=mock_topic,
        toxicity_detector=mock_toxicity,
    )

    with patch("app.nlp.service.get_model_breaker") as mock_breaker_fn:
        breaker = MagicMock()
        breaker.call.side_effect = lambda fn, *a, **kw: fn(*a, **kw)
        mock_breaker_fn.return_value = breaker

        nlp_result = await svc.process_batch()

    assert nlp_result["processed"] == 5

    # 4. Run aggregation
    with patch("app.dashboard.patch_service.PatchService") as MockPatchSvc:
        mock_ps = MagicMock()
        mock_ps.get_current_patch = AsyncMock(return_value="16.2")
        MockPatchSvc.return_value = mock_ps

        agg_svc = AggregationService(test_session)
        aggregations = await agg_svc.aggregate_topics(period_days=7, min_posts=3)

    # 5. Verify aggregation created for "balance" topic
    assert len(aggregations) >= 1

    # Find the balance aggregation
    balance_aggs = [a for a in aggregations if "balance" in a.topic_slug.lower()]
    assert len(balance_aggs) == 1
    balance = balance_aggs[0]

    assert balance.post_count == 5
    assert balance.sentiment_positive > 0
    assert balance.sentiment_negative > 0
    assert balance.source_mix is not None
    assert "reddit" in balance.source_mix
    assert balance.confidence_score is not None
    assert balance.confidence_score > 0


@pytest.mark.asyncio
async def test_pipeline_with_toxic_filtering(test_session: AsyncSession):
    """Pipeline filters toxic posts before aggregation sees them."""
    posts = [
        _make_post("Good discussion", "Reasonable feedback"),
        _make_post("Toxic rage", "Extremely toxic content"),
        _make_post("Nice analysis", "Well thought out points"),
    ]
    for p in posts:
        test_session.add(p)
    await test_session.commit()

    sentiments = [_make_sentiment_score("positive", 0.9)] * 3
    topics = [
        TopicResult(["discussion"], [0], [0.8], ["Discussion"], [["feedback"]])
    ] * 3
    toxicities = [
        ToxicityResult(False, 0.05, {"toxicity": 0.05}),
        ToxicityResult(True, 0.95, {"toxicity": 0.95}),  # toxic
        ToxicityResult(False, 0.08, {"toxicity": 0.08}),
    ]

    mock_analyzer = MagicMock()
    mock_analyzer.analyze_batch.return_value = sentiments
    mock_analyzer.model_name = "test-roberta"

    mock_topic = MagicMock()
    mock_topic.detect_batch.return_value = topics

    mock_toxicity = MagicMock()
    mock_toxicity.detect_batch.return_value = toxicities

    svc = NLPService(
        test_session,
        analyzer=mock_analyzer,
        topic_detector=mock_topic,
        toxicity_detector=mock_toxicity,
    )

    with patch("app.nlp.service.get_model_breaker") as mock_breaker_fn:
        breaker = MagicMock()
        breaker.call.side_effect = lambda fn, *a, **kw: fn(*a, **kw)
        mock_breaker_fn.return_value = breaker

        result = await svc.process_batch()

    assert result["processed"] == 2
    assert result["filtered_toxic"] == 1

    # Verify toxic post was deleted from DB
    remaining_posts = (await test_session.execute(select(Post))).scalars().all()
    assert len(remaining_posts) == 2

    # Verify only 2 sentiment results
    srs = (await test_session.execute(select(SentimentResult))).scalars().all()
    assert len(srs) == 2


@pytest.mark.asyncio
async def test_pipeline_empty_batch_no_errors(test_session: AsyncSession):
    """Pipeline handles empty database gracefully."""
    svc = NLPService(test_session)
    result = await svc.process_batch()

    assert result["processed"] == 0
    assert result["status"] == "complete"

    # Aggregation should also handle empty
    with patch("app.dashboard.patch_service.PatchService") as MockPatchSvc:
        mock_ps = MagicMock()
        mock_ps.get_current_patch = AsyncMock(return_value="16.2")
        MockPatchSvc.return_value = mock_ps

        agg_svc = AggregationService(test_session)
        aggregations = await agg_svc.aggregate_topics()

    assert aggregations == []


# ---------------------------------------------------------------------------
# Helper used by multiple tests
# ---------------------------------------------------------------------------

def _make_sentiment_score(label: str = "positive", confidence: float = 0.9) -> SentimentScore:
    scores = {"positive": 0.0, "neutral": 0.0, "negative": 0.0}
    scores[label] = confidence
    remaining = 1.0 - confidence
    for k in scores:
        if k != label:
            scores[k] = remaining / 2
    return SentimentScore(label=label, confidence=confidence, scores=scores)
