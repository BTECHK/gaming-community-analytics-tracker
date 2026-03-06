"""Tests for NLP topics module."""

import pytest

from app.nlp.topics import (
    TopicResult,
    TOPIC_NAMES,
    TOPIC_DISPLAY_NAMES,
    SEED_TOPIC_LIST,
    SIMILARITY_THRESHOLD,
)


class TestTopicResult:
    """Tests for TopicResult dataclass."""

    def test_topic_result_defaults(self):
        """Test TopicResult default values."""
        result = TopicResult()
        assert result.topics == []
        assert result.topic_ids == []
        assert result.probabilities == []
        assert result.display_names == []
        assert result.keywords == []

    def test_topic_result_to_json(self):
        """Test TopicResult to_json method."""
        result = TopicResult(
            topics=["matchmaking", "toxicity"],
            topic_ids=[0, 1],
            probabilities=[0.8, 0.6],
        )
        assert result.to_json() == ["matchmaking", "toxicity"]

    def test_topic_result_get_display_name_known(self):
        """Test get_display_name for known topics."""
        result = TopicResult(
            topics=["matchmaking"],
            display_names=["Ranked & Matchmaking"],
        )
        name = result.get_display_name("matchmaking")
        assert name == "Ranked & Matchmaking"

    def test_topic_result_get_display_name_unknown(self):
        """Test get_display_name for unknown topics."""
        result = TopicResult(topics=["unknown_topic"])
        name = result.get_display_name("unknown_topic")
        assert name == "Unknown Topic"


class TestTopicNames:
    """Tests for topic name configuration."""

    def test_topic_names_count(self):
        """Test that we have expected number of base topics."""
        assert len(TOPIC_NAMES) == 7

    def test_topic_names_match_seed_list(self):
        """Test that topic names count matches seed list."""
        assert len(TOPIC_NAMES) == len(SEED_TOPIC_LIST)

    def test_all_topic_names_have_display_names(self):
        """Test that all topic names have display names."""
        for name in TOPIC_NAMES:
            assert name in TOPIC_DISPLAY_NAMES

    def test_display_names_not_empty(self):
        """Test that display names are not empty."""
        for name, display in TOPIC_DISPLAY_NAMES.items():
            assert len(display) > 0


class TestSeedTopicList:
    """Tests for seed topic list configuration."""

    def test_seed_topics_not_empty(self):
        """Test that seed topic lists are not empty."""
        for seed_list in SEED_TOPIC_LIST:
            assert len(seed_list) > 0

    def test_seed_topics_lowercase(self):
        """Test that seed topic words are lowercase."""
        for seed_list in SEED_TOPIC_LIST:
            for word in seed_list:
                assert word == word.lower()

    def test_seed_topics_minimum_words(self):
        """Test that each seed topic has sufficient keywords."""
        for seed_list in SEED_TOPIC_LIST:
            assert len(seed_list) >= 5

    def test_matchmaking_keywords(self):
        """Test matchmaking seed topic has key terms."""
        matchmaking_seeds = SEED_TOPIC_LIST[0]
        assert "ranked" in matchmaking_seeds
        assert "mmr" in matchmaking_seeds
        assert "queue" in matchmaking_seeds

    def test_toxicity_keywords(self):
        """Test toxicity seed topic has key terms."""
        toxicity_seeds = SEED_TOPIC_LIST[1]
        assert "toxic" in toxicity_seeds
        assert "report" in toxicity_seeds
        assert "ban" in toxicity_seeds

    def test_balance_keywords(self):
        """Test balance seed topic has key terms."""
        balance_seeds = SEED_TOPIC_LIST[2]
        assert "nerf" in balance_seeds
        assert "buff" in balance_seeds
        assert "meta" in balance_seeds

    def test_client_keywords(self):
        """Test client seed topic has key terms."""
        client_seeds = SEED_TOPIC_LIST[3]
        assert "bug" in client_seeds
        assert "crash" in client_seeds
        assert "lag" in client_seeds

    def test_champion_keywords(self):
        """Test champion seed topic has key terms."""
        champion_seeds = SEED_TOPIC_LIST[4]
        assert "champion" in champion_seeds
        assert "rework" in champion_seeds
        assert "skin" in champion_seeds


class TestSimilarityThreshold:
    """Tests for similarity threshold configuration."""

    def test_threshold_in_range(self):
        """Test that similarity threshold is reasonable."""
        assert 0.0 < SIMILARITY_THRESHOLD < 1.0

    def test_threshold_not_too_strict(self):
        """Test that threshold isn't too strict."""
        assert SIMILARITY_THRESHOLD <= 0.5

    def test_threshold_not_too_loose(self):
        """Test that threshold isn't too loose."""
        assert SIMILARITY_THRESHOLD >= 0.1
