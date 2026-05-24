"""Tests for backend services."""

import pytest

from app.services.topic_naming import (
    generate_topic_name,
    _get_fallback_name,
    _clean_topic_name,
    FALLBACK_TOPIC_NAMES,
)
from app.services.digest import (
    generate_digest_summary,
    _generate_fallback_summary,
    _build_topic_context,
)


class TestTopicNaming:
    """Tests for topic naming service."""

    def test_get_fallback_name_matchmaking(self):
        """Test fallback name for matchmaking keywords."""
        keywords = ["ranked", "queue", "mmr"]
        name = _get_fallback_name(keywords)
        assert name == "Ranked Play"

    def test_get_fallback_name_balance(self):
        """Test fallback name for balance keywords."""
        keywords = ["nerf", "buff", "op"]
        name = _get_fallback_name(keywords)
        assert name == "Nerfs & Buffs"

    def test_get_fallback_name_toxic(self):
        """Test fallback name for toxicity keywords."""
        keywords = ["toxic", "flame", "report"]
        name = _get_fallback_name(keywords)
        assert name == "Player Behavior"

    def test_get_fallback_name_unknown(self):
        """Test fallback name for unknown keywords uses first keyword."""
        keywords = ["customword", "another"]
        name = _get_fallback_name(keywords)
        assert name == "Customword"

    def test_get_fallback_name_empty(self):
        """Test fallback name for empty keywords."""
        keywords = []
        name = _get_fallback_name(keywords)
        assert name == "General Discussion"

    def test_clean_topic_name_removes_quotes(self):
        """Test that clean_topic_name removes quotes."""
        name = _clean_topic_name('"Test Topic"')
        assert name == "Test Topic"

    def test_clean_topic_name_limits_words(self):
        """Test that clean_topic_name limits to 4 words."""
        name = _clean_topic_name("One Two Three Four Five Six")
        assert name == "One Two Three Four"

    def test_clean_topic_name_removes_trailing_punctuation(self):
        """Test that clean_topic_name removes trailing punctuation."""
        name = _clean_topic_name("Test Topic.")
        assert name == "Test Topic"

    @pytest.mark.asyncio
    async def test_generate_topic_name_uses_fallback(self):
        """Test that generate_topic_name uses fallback when no API key."""
        # Without API key configured, should use fallback
        keywords = ["matchmaking", "ranked", "queue"]
        name = await generate_topic_name(keywords)
        assert name == "Ranked & Matchmaking"


class TestDigestService:
    """Tests for digest summary service."""

    def test_build_topic_context(self):
        """Test building context from topics."""
        topics = [
            {
                "name": "Character Balance",
                "summary": "Discussion about nerfs and buffs",
                "sentiment": {"positive": 30, "negative": 50, "neutral": 20},
                "post_count": 100,
            }
        ]
        context = _build_topic_context(topics)
        assert "Character Balance" in context
        assert "nerfs and buffs" in context
        assert "negative" in context
        assert "100 posts" in context

    def test_build_topic_context_empty(self):
        """Test building context from empty topics."""
        topics = []
        context = _build_topic_context(topics)
        assert context == ""

    def test_generate_fallback_summary_single_topic(self):
        """Test fallback summary with single topic."""
        topics = [
            {
                "name": "Test Topic",
                "summary": "A test summary",
                "sentiment": {"positive": 60, "negative": 20, "neutral": 20},
                "post_count": 50,
            }
        ]
        summary = _generate_fallback_summary(topics)
        assert "1 topic" in summary
        assert "Test Topic" in summary
        assert "50 posts" in summary

    def test_generate_fallback_summary_multiple_topics(self):
        """Test fallback summary with multiple topics."""
        topics = [
            {
                "name": "Topic A",
                "summary": "Summary A",
                "sentiment": {"positive": 70, "negative": 10, "neutral": 20},
                "post_count": 100,
            },
            {
                "name": "Topic B",
                "summary": "Summary B",
                "sentiment": {"positive": 30, "negative": 50, "neutral": 20},
                "post_count": 50,
            },
        ]
        summary = _generate_fallback_summary(topics)
        assert "2 topics" in summary
        assert "Topic A" in summary  # Most active

    def test_generate_fallback_summary_empty(self):
        """Test fallback summary with no topics."""
        summary = _generate_fallback_summary([])
        assert "No topics" in summary

    @pytest.mark.asyncio
    async def test_generate_digest_summary_empty_topics(self):
        """Test digest summary with no topics."""
        result = await generate_digest_summary([])
        assert result["topic_count"] == 0
        assert "No topics" in result["summary"]
        assert result["is_ai_generated"] is False

    @pytest.mark.asyncio
    async def test_generate_digest_summary_with_topics(self):
        """Test digest summary with topics uses fallback when no API key."""
        topics = [
            {
                "name": "Character Updates",
                "summary": "New character reworks",
                "sentiment": {"positive": 50, "negative": 20, "neutral": 30},
                "post_count": 75,
            }
        ]
        result = await generate_digest_summary(topics)
        assert result["topic_count"] == 1
        assert result["is_ai_generated"] is False
        assert "Character Updates" in result["summary"] or "1 topic" in result["summary"]
