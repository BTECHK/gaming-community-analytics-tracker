"""
Search Trends Adapter

Fetches search-interest time series for configured topic keywords.
keyword lists and tuning have been removed
for public release.
"""

from typing import Any


class SearchTrendsAdapter:
    """Adapter for external search-trends source."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    async def fetch(self, *args: Any, **kwargs: Any) -> list[Any]:
        """Fetch search-trend entries. Implementation details omitted."""
        return []
