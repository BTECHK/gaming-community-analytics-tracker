"""Tests for NLPService — process_batch, circuit breaker, DLQ paths."""

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Post, Platform, SentimentResult, SentimentLabel
from app.nlp.circuit_breaker import CircuitBreaker, CircuitOpenError, CircuitState
from app.nlp.service import NLPService
from app.nlp.sentiment import SentimentScore
from app.nlp.topics import TopicResult
from app.nlp.toxicity import ToxicityResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_post(
    title: str = "Test title",
    content: str = "Test content about gaming",
    platform: Platform = Platform.REDDIT,
) -> Post:
    """Create a transient Post object for testing."""
    now = datetime.now(timezone.utc)
    return Post(
        id=str(uuid4()),
        platform=platform,
        external_id=str(uuid4()),
        title=title,
        content=content,
        author="tester",
        url="https://example.com/post",
        upvotes=0,
        comments_count=0,
        published_at=now,
        fetched_at=now,
        created_at=now,
        updated_at=now,
    )


def _make_sentiment(label: str = "positive", confidence: float = 0.9) -> SentimentScore:
    return SentimentScore(
        label=label,
        confidence=confidence,
        scores={"positive": 0.9, "neutral": 0.05, "negative": 0.05},
    )


def _make_topic() -> TopicResult:
    return TopicResult(
        topics=["matchmaking"],
        topic_ids=[0],
        probabilities=[0.8],
        display_names=["Matchmaking"],
        keywords=[["ranked", "mmr"]],
    )


def _make_toxicity(is_toxic: bool = False, score: float = 0.1) -> ToxicityResult:
    return ToxicityResult(
        is_toxic=is_toxic,
        toxicity_score=score,
        categories={"toxicity": score},
    )


# ---------------------------------------------------------------------------
# NLPService.process_batch — happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_process_batch_no_posts(test_session: AsyncSession):
    """process_batch returns immediately when there are no unprocessed posts."""
    svc = NLPService(test_session)
    result = await svc.process_batch()
    assert result["processed"] == 0
    assert result["status"] == "complete"


@pytest.mark.asyncio
async def test_process_batch_analyzes_posts(test_session: AsyncSession):
    """process_batch finds unprocessed posts, runs analysis, and stores results."""
    # Insert test posts
    posts = [_make_post(title=f"Post {i}") for i in range(3)]
    for p in posts:
        test_session.add(p)
    await test_session.commit()

    # Mock the three NLP model classes
    mock_analyzer = MagicMock()
    mock_analyzer.analyze_batch.return_value = [_make_sentiment() for _ in posts]
    mock_analyzer.model_name = "test-model"

    mock_topic = MagicMock()
    mock_topic.detect_batch.return_value = [_make_topic() for _ in posts]

    mock_toxicity = MagicMock()
    mock_toxicity.detect_batch.return_value = [_make_toxicity() for _ in posts]

    svc = NLPService(
        test_session,
        analyzer=mock_analyzer,
        topic_detector=mock_topic,
        toxicity_detector=mock_toxicity,
    )

    # Patch circuit breakers to pass-through
    with patch("app.nlp.service.get_model_breaker") as mock_breaker_fn:
        breaker = MagicMock()
        breaker.call.side_effect = lambda fn, *a, **kw: fn(*a, **kw)
        mock_breaker_fn.return_value = breaker

        result = await svc.process_batch()

    assert result["processed"] == 3
    assert result["status"] == "complete"
    assert result["filtered_toxic"] == 0


@pytest.mark.asyncio
async def test_process_batch_filters_toxic(test_session: AsyncSession):
    """Toxic posts are filtered out and deleted instead of stored."""
    posts = [_make_post(title=f"Post {i}") for i in range(3)]
    for p in posts:
        test_session.add(p)
    await test_session.commit()

    mock_analyzer = MagicMock()
    mock_analyzer.analyze_batch.return_value = [_make_sentiment() for _ in posts]
    mock_analyzer.model_name = "test-model"

    mock_topic = MagicMock()
    mock_topic.detect_batch.return_value = [_make_topic() for _ in posts]

    # Mark second post as toxic
    toxicity_results = [_make_toxicity(), _make_toxicity(is_toxic=True, score=0.95), _make_toxicity()]
    mock_toxicity = MagicMock()
    mock_toxicity.detect_batch.return_value = toxicity_results

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
    assert result["status"] == "complete"


# ---------------------------------------------------------------------------
# Circuit breaker integration
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_threshold():
    """CircuitBreaker transitions to OPEN after failure_threshold failures."""
    cb = CircuitBreaker(failure_threshold=3, cooldown_seconds=60, name="test")

    assert cb.state == CircuitState.CLOSED

    for i in range(3):
        with pytest.raises(ValueError):
            cb.call(lambda: (_ for _ in ()).throw(ValueError("boom")))

    assert cb.state == CircuitState.OPEN
    assert cb.failure_count == 3

    # Subsequent calls should raise CircuitOpenError
    with pytest.raises(CircuitOpenError):
        cb.call(lambda: "ok")


@pytest.mark.asyncio
async def test_circuit_breaker_resets_on_success():
    """CircuitBreaker resets failure count on successful call."""
    cb = CircuitBreaker(failure_threshold=3, cooldown_seconds=60, name="test")

    # Two failures, then a success
    for _ in range(2):
        with pytest.raises(ValueError):
            cb.call(lambda: (_ for _ in ()).throw(ValueError("boom")))

    assert cb.failure_count == 2
    cb.call(lambda: "ok")
    assert cb.failure_count == 0
    assert cb.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_process_batch_returns_failed_on_circuit_open(test_session: AsyncSession):
    """process_batch returns 'failed' status when circuit breaker is open."""
    # Insert a post so process_batch tries to analyze
    post = _make_post()
    test_session.add(post)
    await test_session.commit()

    svc = NLPService(test_session)

    # Make _get_analyzer raise CircuitOpenError
    with patch.object(svc, "_get_analyzer", side_effect=CircuitOpenError("open")):
        result = await svc.process_batch()

    # analyze_posts returns [] when circuit is open, which maps to "partial"
    assert result["status"] in ("failed", "partial")
    assert result["processed"] == 0


# ---------------------------------------------------------------------------
# Dead Letter Queue paths
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_add_to_dlq_on_analysis_failure(test_session: AsyncSession):
    """Posts are added to DLQ when analysis raises an exception."""
    posts = [_make_post() for _ in range(2)]
    for p in posts:
        test_session.add(p)
    await test_session.commit()

    mock_analyzer = MagicMock()
    mock_analyzer.analyze_batch.side_effect = RuntimeError("model crash")
    mock_analyzer.model_name = "test-model"

    svc = NLPService(
        test_session,
        analyzer=mock_analyzer,
        topic_detector=MagicMock(),
        toxicity_detector=MagicMock(),
    )

    # Patch DLQ to track calls
    mock_dlq = AsyncMock()
    with patch("app.nlp.service.DeadLetterQueue") as DLQClass:
        DLQClass.get_instance = AsyncMock(return_value=mock_dlq)

        with patch("app.nlp.service.get_model_breaker") as mock_breaker_fn:
            breaker = MagicMock()
            breaker.call.side_effect = lambda fn, *a, **kw: fn(*a, **kw)
            mock_breaker_fn.return_value = breaker

            result = await svc.analyze_posts(posts)

    assert len(result) == 0
    assert mock_dlq.add_failed_post.call_count == 2


@pytest.mark.asyncio
async def test_add_to_dlq_empty_posts(test_session: AsyncSession):
    """add_to_dlq returns 0 for empty list."""
    svc = NLPService(test_session)
    count = await svc.add_to_dlq([], "no error")
    assert count == 0


# ---------------------------------------------------------------------------
# Mixed success/failure batch
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_process_batch_mixed_results(test_session: AsyncSession):
    """process_batch handles a batch where some succeed and one is toxic."""
    posts = [_make_post(title=f"Post {i}") for i in range(4)]
    for p in posts:
        test_session.add(p)
    await test_session.commit()

    sentiments = [
        _make_sentiment("positive", 0.9),
        _make_sentiment("negative", 0.8),
        _make_sentiment("neutral", 0.7),
        _make_sentiment("positive", 0.85),
    ]
    topics = [_make_topic() for _ in posts]
    toxicities = [
        _make_toxicity(),
        _make_toxicity(),
        _make_toxicity(is_toxic=True, score=0.99),  # post 3 toxic
        _make_toxicity(),
    ]

    mock_analyzer = MagicMock()
    mock_analyzer.analyze_batch.return_value = sentiments
    mock_analyzer.model_name = "test-model"

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

    assert result["processed"] == 3  # 4 - 1 toxic
    assert result["filtered_toxic"] == 1
    assert result["status"] == "complete"


# ---------------------------------------------------------------------------
# get_unprocessed_posts
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_unprocessed_posts_excludes_analyzed(test_session: AsyncSession):
    """get_unprocessed_posts excludes posts with valid sentiment results."""
    p1 = _make_post(title="Unprocessed")
    p2 = _make_post(title="Already processed")
    test_session.add(p1)
    test_session.add(p2)
    await test_session.flush()

    # Add sentiment result for p2
    sr = SentimentResult(
        post_id=p2.id,
        label=SentimentLabel.positive,
        confidence=0.9,
        scores={"positive": 0.9, "neutral": 0.05, "negative": 0.05},
        model_name="test",
        analyzed_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=48),
    )
    test_session.add(sr)
    await test_session.commit()

    svc = NLPService(test_session)
    unprocessed = await svc.get_unprocessed_posts()

    assert len(unprocessed) == 1
    assert unprocessed[0].id == p1.id


@pytest.mark.asyncio
async def test_get_unprocessed_posts_includes_expired(test_session: AsyncSession):
    """get_unprocessed_posts includes posts with expired sentiment results."""
    post = _make_post(title="Expired")
    test_session.add(post)
    await test_session.flush()

    # Add expired sentiment result
    sr = SentimentResult(
        post_id=post.id,
        label=SentimentLabel.neutral,
        confidence=0.7,
        model_name="test",
        analyzed_at=datetime.now(timezone.utc) - timedelta(hours=72),
        expires_at=datetime.now(timezone.utc) - timedelta(hours=24),  # expired
    )
    test_session.add(sr)
    await test_session.commit()

    svc = NLPService(test_session)
    unprocessed = await svc.get_unprocessed_posts()

    assert len(unprocessed) == 1
    assert unprocessed[0].id == post.id


# ---------------------------------------------------------------------------
# get_stats
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_stats_empty_db(test_session: AsyncSession):
    """get_stats returns zeroes on empty database."""
    svc = NLPService(test_session)
    stats = await svc.get_stats()

    assert stats["total_posts"] == 0
    assert stats["with_valid_sentiment"] == 0
    assert stats["needs_analysis"] == 0
    assert "config" in stats
