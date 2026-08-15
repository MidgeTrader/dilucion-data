"""Finnhub API client."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from tenacity import retry, stop_after_attempt, wait_exponential

from apis._rate_limit import RateLimiter
from apis.connection_pool import get_client
from cache import TTLCache
from config import get_settings
from models import NewsArticle, QuoteData

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
            client = get_client(timeout=20)
            resp = client.get(f"{self.BASE}/quote", params={"symbol": ticker.upper(), "token": self.api_key})
            resp.raise_for_status()
            data = resp.json()
            quote = QuoteData(
                ticker=ticker.upper(),
                price=float(data["c"]) if data.get("c") else None,
                change_percent=float(data["dp"]) if data.get("dp") else None,
                timestamp=datetime.now(timezone.utc),
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
            client = get_client(timeout=20)
            resp = client.get(f"{self.BASE}/stock/profile2", params={"symbol": ticker.upper(), "token": self.api_key})
            resp.raise_for_status()
            data = resp.json()
            if data:
                self.cache.set(cache_key, data, 86400)
            return data
        except Exception as exc:
            logger.error("Finnhub profile error: %s", exc)
            return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=15), reraise=False)
    def get_company_news(self, ticker: str, days: int = 90, limit: int = 20) -> list[NewsArticle]:
        """Fetch recent company news from Finnhub /company-news."""
        symbol = ticker.upper()
        cache_key = f"finnhub:news:{symbol}:{days}"
        cached = self.cache.get(cache_key)
        if cached:
            return [NewsArticle(**item) for item in cached]

        if not self.api_key:
            return []

        from datetime import date, timedelta

        end = date.today()
        start = end - timedelta(days=days)

        self.limiter.wait()
        try:
            client = get_client(timeout=20)
            resp = client.get(
                f"{self.BASE}/company-news",
                params={
                    "symbol": symbol,
                    "from": start.isoformat(),
                    "to": end.isoformat(),
                    "token": self.api_key,
                },
            )
            resp.raise_for_status()
            raw = resp.json()
            if not isinstance(raw, list):
                return []

            articles: list[NewsArticle] = []
            for item in raw[:limit]:
                headline = item.get("headline") or item.get("title")
                if not headline:
                    continue
                ts = item.get("datetime")
                if ts:
                    pub_date = datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d")
                else:
                    pub_date = end.isoformat()
                articles.append(
                    NewsArticle(
                        title=headline,
                        source=item.get("source") or "Finnhub",
                        date=pub_date,
                        url=item.get("url") or "",
                        summary=(item.get("summary") or "")[:500] or None,
                        source_type="finnhub",
                    )
                )

            self.cache.set(
                cache_key,
                [a.model_dump() for a in articles],
                self.settings.finnhub_cache_ttl_minutes * 60,
            )
            return articles
        except Exception as exc:
            logger.error("Finnhub news error for %s: %s", symbol, exc)
            return []
