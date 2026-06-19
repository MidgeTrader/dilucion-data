"""Stocksera API client."""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from cache import TTLCache
from config import get_settings
from models import ShortInterestData

logger = logging.getLogger(__name__)


def _safe_float(value: Any) -> Optional[float]:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


class StockseraClient:
    BASE = "https://stocksera.com/api"

    def __init__(self, cache: TTLCache) -> None:
        self.settings = get_settings()
        self.cache = cache
        self.api_key = self.settings.stocksera_api_key

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=15), reraise=False)
    def get_short_interest(self, ticker: str) -> Optional[ShortInterestData]:
        cache_key = f"stocksera:short:{ticker.upper()}"
        cached = self.cache.get(cache_key)
        if cached:
            return ShortInterestData(**cached)
        if not self.api_key:
            return None
        try:
            with httpx.Client(timeout=25) as client:
                resp = client.get(
                    f"{self.BASE}/shorts/{ticker.upper()}",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                if resp.status_code == 404:
                    return ShortInterestData(ticker=ticker.upper())
                resp.raise_for_status()
                data = resp.json()
                result = ShortInterestData(
                    ticker=ticker.upper(),
                    short_interest=_safe_float(data.get("short_interest")),
                    borrow_rate=_safe_float(data.get("borrow_rate") or data.get("fee_rate")),
                    short_percent_float=_safe_float(data.get("short_percent_float") or data.get("percent_float")),
                )
                self.cache.set(cache_key, result.model_dump(), self.settings.stocksera_cache_ttl_hours * 3600)
                return result
        except Exception as exc:
            logger.error("Stocksera error: %s", exc)
            return None
