"""EODHD financial news API (news-only — free tier ~20 calls/day).

Docs: https://eodhd.com/financial-apis/stock-market-financial-news-api
"""

from __future__ import annotations

import logging
from datetime import date, timedelta

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from apis._rate_limit import RateLimiter
from cache import TTLCache
from config import get_settings
from models import NewsArticle

logger = logging.getLogger(__name__)

# Free tier: ~20 API calls/day — cache news per ticker for 6h to avoid repeat hits.
NEWS_CACHE_TTL_SECONDS = 6 * 3600


class EodhdClient:
    BASE = "https://eodhd.com/api"

    def __init__(self, cache: TTLCache) -> None:
        self.settings = get_settings()
        self.cache = cache
        self.api_key = self.settings.eodhd_api_key
        self.limiter = RateLimiter(30)

    def resolve_symbol(self, ticker: str, exchange: str = "US") -> str:
        """EODHD format: SMR.US, AAPL.US"""
        t = ticker.upper().strip()
        if "." in t:
            return t
        return f"{t}.{exchange.upper()}"

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=10), reraise=False)
    def _get_json(self, path: str, params: dict | None = None) -> list | dict | None:
        if not self.api_key:
            return None
        self.limiter.wait()
        p = dict(params or {})
        p["api_token"] = self.api_key
        p.setdefault("fmt", "json")
        try:
            with httpx.Client(timeout=25) as client:
                resp = client.get(f"{self.BASE}/{path.lstrip('/')}", params=p)
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            logger.error("EODHD %s error: %s", path, exc)
            return None

    def get_news(self, ticker: str, limit: int = 20, days: int = 90) -> list[NewsArticle]:
        symbol = self.resolve_symbol(ticker)
        cache_key = f"eodhd:news:{symbol}:{limit}"
        cached = self.cache.get(cache_key)
        if cached:
            return [NewsArticle(**item) for item in cached[:limit]]

        end = date.today()
        start = end - timedelta(days=days)
        raw = self._get_json(
            "news",
            {
                "s": symbol,
                "limit": min(limit, 50),
                "offset": 0,
                "from": start.isoformat(),
                "to": end.isoformat(),
            },
        )
        if not isinstance(raw, list):
            return []

        articles: list[NewsArticle] = []
        for item in raw[:limit]:
            title = item.get("title")
            if not title:
                continue
            pub = item.get("date") or ""
            pub_date = pub[:10] if len(pub) >= 10 else end.isoformat()
            content = item.get("content") or ""
            sentiment = item.get("sentiment") or {}
            polarity = sentiment.get("polarity") if isinstance(sentiment, dict) else None
            tags = item.get("tags") or []
            source_name = "EODHD"
            if tags:
                source_name = f"EODHD · {tags[0].title() if isinstance(tags[0], str) else tags[0]}"

            articles.append(
                NewsArticle(
                    title=title,
                    source=source_name,
                    date=pub_date,
                    url=item.get("link") or "",
                    summary=content[:500] if content else None,
                    source_type="eodhd",
                    sentiment=polarity,
                )
            )

        # Cache even empty results to avoid burning calls on tickers with no coverage.
        self.cache.set(cache_key, [a.model_dump() for a in articles], NEWS_CACHE_TTL_SECONDS)
        return articles
