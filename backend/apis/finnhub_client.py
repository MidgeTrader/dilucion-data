"""Finnhub API client."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from apis._rate_limit import RateLimiter
from cache import TTLCache
from config import get_settings
from models import QuoteData

logger = logging.getLogger(__name__)


class FinnhubClient:
    BASE = "https://finnhub.io/api/v1"

    def __init__(self, cache: TTLCache) -> None:
        self.settings = get_settings()
        self.cache = cache
        self.limiter = RateLimiter(self.settings.finnhub_rate_limit_per_min)
        self.api_key = self.settings.finnhub_api_key

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=15), reraise=False)
    def get_quote(self, ticker: str) -> Optional[QuoteData]:
        cache_key = f"finnhub:quote:{ticker.upper()}"
        cached = self.cache.get(cache_key)
        if cached:
            return QuoteData(**cached)
        if not self.api_key:
            return None
        self.limiter.wait()
        try:
            with httpx.Client(timeout=20) as client:
                resp = client.get(f"{self.BASE}/quote", params={"symbol": ticker.upper(), "token": self.api_key})
                resp.raise_for_status()
                data = resp.json()
                quote = QuoteData(
                    ticker=ticker.upper(),
                    price=float(data["c"]) if data.get("c") else None,
                    change_percent=float(data["dp"]) if data.get("dp") else None,
                    timestamp=datetime.utcnow(),
                )
                self.cache.set(cache_key, quote.model_dump(), self.settings.finnhub_cache_ttl_minutes * 60)
                return quote
        except Exception as exc:
            logger.error("Finnhub quote error: %s", exc)
            return None

    def get_company_profile(self, ticker: str) -> Optional[dict]:
        cache_key = f"finnhub:profile:{ticker.upper()}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        if not self.api_key:
            return None
        self.limiter.wait()
        try:
            with httpx.Client(timeout=20) as client:
                resp = client.get(f"{self.BASE}/stock/profile2", params={"symbol": ticker.upper(), "token": self.api_key})
                resp.raise_for_status()
                data = resp.json()
                if data:
                    self.cache.set(cache_key, data, 86400)
                return data
        except Exception as exc:
            logger.error("Finnhub profile error: %s", exc)
            return None
