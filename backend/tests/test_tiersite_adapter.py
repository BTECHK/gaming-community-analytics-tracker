"""Tests for TierSite scraper adapter."""

import pytest

from app.ingestion.adapters.tiersite import (
    compute_tier,
    format_champion_name,
    KNOWN_CHAMPIONS,
    TIER_BRACKETS,
    ESTIMATED_TIER_DATA,
)


class TestComputeTier:
    """Tests for tier computation from win rate."""

    def test_compute_tier_s_plus(self):
        """Test S+ tier for high win rates."""
        assert compute_tier(55.0) == "S+"
        assert compute_tier(54.0) == "S+"

    def test_compute_tier_s(self):
        """Test S tier."""
        assert compute_tier(53.0) == "S"
        assert compute_tier(52.5) == "S"

    def test_compute_tier_a(self):
        """Test A tier."""
        assert compute_tier(52.0) == "A"
        assert compute_tier(51.0) == "A"

    def test_compute_tier_b(self):
        """Test B tier."""
        assert compute_tier(50.5) == "B"
        assert compute_tier(49.5) == "B"

    def test_compute_tier_c(self):
        """Test C tier."""
        assert compute_tier(49.0) == "C"
        assert compute_tier(48.0) == "C"

    def test_compute_tier_d(self):
        """Test D tier for low win rates."""
        assert compute_tier(47.0) == "D"
        assert compute_tier(45.0) == "D"

    def test_compute_tier_none(self):
        """Test tier for None win rate."""
        assert compute_tier(None) == "?"


class TestFormatChampionName:
    """Tests for champion name formatting."""

    def test_format_simple_name(self):
        """Test formatting simple champion names."""
        assert format_champion_name("ahri") == "Ahri"
        assert format_champion_name("jinx") == "Jinx"

    def test_format_special_cases(self):
        """Test formatting special case champion names."""
        assert format_champion_name("aurelionsol") == "Aurelion Sol"
        assert format_champion_name("drmundo") == "Dr. Mundo"
        assert format_champion_name("jarvaniv") == "Jarvan IV"
        assert format_champion_name("kaisa") == "Kai'Sa"
        assert format_champion_name("leesin") == "Lee Sin"
        assert format_champion_name("missfortune") == "Miss Fortune"

    def test_format_with_apostrophes(self):
        """Test formatting names with apostrophes."""
        assert format_champion_name("khazix") == "Kha'Zix"
        assert format_champion_name("velkoz") == "Vel'Koz"
        assert format_champion_name("belveth") == "Bel'Veth"
        assert format_champion_name("chogath") == "Cho'Gath"


class TestKnownChampions:
    """Tests for known champions list."""

    def test_known_champions_not_empty(self):
        """Test that known champions list is populated."""
        assert len(KNOWN_CHAMPIONS) > 100

    def test_known_champions_lowercase(self):
        """Test that all champion slugs are lowercase."""
        for champ in KNOWN_CHAMPIONS:
            assert champ == champ.lower()

    def test_popular_champions_included(self):
        """Test that popular champions are in the list."""
        popular = ["ahri", "jinx", "yasuo", "lux", "ezreal", "thresh"]
        for champ in popular:
            assert champ in KNOWN_CHAMPIONS


class TestTierBrackets:
    """Tests for tier bracket configuration."""

    def test_tier_brackets_ordered(self):
        """Test that tier brackets are in descending order."""
        tiers = list(TIER_BRACKETS.keys())
        values = list(TIER_BRACKETS.values())
        assert values == sorted(values, reverse=True)

    def test_tier_brackets_complete(self):
        """Test that all tiers are defined."""
        expected_tiers = {"S+", "S", "A", "B", "C", "D"}
        assert set(TIER_BRACKETS.keys()) == expected_tiers


class TestEstimatedTierData:
    """Tests for estimated tier data."""

    def test_estimated_data_has_required_fields(self):
        """Test that estimated data entries have required fields."""
        for champ, data in ESTIMATED_TIER_DATA.items():
            assert "tier" in data
            assert "win_rate" in data
            assert "role" in data

    def test_estimated_data_valid_tiers(self):
        """Test that estimated tiers are valid."""
        valid_tiers = {"S+", "S", "A", "B", "C", "D"}
        for champ, data in ESTIMATED_TIER_DATA.items():
            assert data["tier"] in valid_tiers

    def test_estimated_data_valid_roles(self):
        """Test that estimated roles are valid."""
        valid_roles = {"TOP", "JUNGLE", "MID", "ADC", "SUPPORT"}
        for champ, data in ESTIMATED_TIER_DATA.items():
            assert data["role"] in valid_roles

    def test_estimated_data_valid_win_rates(self):
        """Test that estimated win rates are reasonable."""
        for champ, data in ESTIMATED_TIER_DATA.items():
            assert 40.0 <= data["win_rate"] <= 60.0
