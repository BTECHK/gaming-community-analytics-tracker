"""Tests for TierSite adapter interface."""

import pytest

from app.ingestion.adapters.tiersite import TierListAdapter


class TestTierListAdapter:
    """Tests for the tier-list data source adapter."""

    def test_adapter_instantiates(self):
        """Adapter can be created without arguments."""
        adapter = TierListAdapter()
        assert adapter is not None

    @pytest.mark.asyncio
    async def test_fetch_returns_list(self):
        """fetch() returns a list."""
        adapter = TierListAdapter()
        result = await adapter.fetch()
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_fetch_with_limit(self):
        """fetch() accepts keyword arguments."""
        adapter = TierListAdapter()
        result = await adapter.fetch(limit=10)
        assert isinstance(result, list)
