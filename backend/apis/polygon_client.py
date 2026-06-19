"""Massive.com (formerly Polygon.io) API client."""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from apis._rate_limit import RateLimiter
from cache import TTLCache
from config import get_settings
from models import CandlePoint, NewsArticle

logger = logging.getLogger(__name__)

NEWS_CACHE_TTL_SECONDS = 3600  # Massive news updates ~hourly


def _sentiment_from_insights(insights: list, ticker: str) -> tuple[Optional[float], Optional[str]]:
    """Map Massive insights sentiment label to -1..1 float."""
    if not insights:
        return None, None
    match = None
    for ins in insights:
        if not isinstance(ins, dict):
            continue
        if (ins.get("ticker") or "").upper() == ticker.upper():
            match = ins
            break
    if match is None and isinstance(insights[0], dict):
        match = insights[0]
    if not match:
        return None, None
    label = (match.get("sentiment") or "").lower()
    reasoning = match.get("sentiment_reasoning")
    score = {"positive": 1.0, "negative": -1.0, "neutral": 0.0}.get(label)
    return score, reasoning


class PolygonClient:
    """Massive/Polygon market data client (same API key works on both hosts)."""

    BASE_URLS = ("https://api.massive.com", "https://api.polygon.io")

    def __init__(self, cache: TTLCache) -> None:
        self.settings = get_settings()
        self.cache = cache
        self.limiter = RateLimiter(self.settings.polygon_rate_limit_per_min)
        self.api_key = self.settings.massive_api_key or self.settings.polygon_api_key

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=20), reraise=False)
    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Optional[dict]:
        if not self.api_key:
            return None
        self.limiter.wait()
        params = dict(params or {})
        params["apiKey"] = self.api_key
        last_exc: Exception | None = None
        for base in self.BASE_URLS:
            try:
                with httpx.Client(timeout=30) as client:
                    resp = client.get(f"{base}{path}", params=params)
                    resp.raise_for_status()
                    return resp.json()
            except Exception as exc:
                last_exc = exc
                logger.debug("Massive request failed on %s: %s", base, exc)
        logger.error("Massive error: %s", last_exc)
        return None

    def fetch_active_tickers(self) -> List[dict]:
        cache_key = "polygon:active_tickers"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        results: List[dict] = []
        path, params = "/v3/reference/tickers", {"active": "true", "limit": 1000, "market": "stocks"}
        while path:
            data = self._get(path, params if path.startswith("/") else None)
            if not data:
                break
            results.extend(data.get("results", []))
            next_url = data.get("next_url")
            if next_url:
                for base in self.BASE_URLS:
                    if next_url.startswith(base):
                        path = next_url.replace(base, "")
                        break
                else:
                    path = ""
            else:
                path = ""
            params = None
        if results:
            self.cache.set(cache_key, results, self.settings.polygon_cache_ttl_hours * 3600)
        return results

    def get_ticker_details(self, ticker: str) -> Optional[dict]:
        cache_key = f"polygon:ticker:{ticker.upper()}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        data = self._get(f"/v3/reference/tickers/{ticker.upper()}")
        if data:
            self.cache.set(cache_key, data, self.settings.polygon_cache_ttl_hours * 3600)
        return data

    def get_candles(self, ticker: str, days: int = 90) -> List[CandlePoint]:
        cache_key = f"polygon:candles:{ticker.upper()}:{days}"
        cached = self.cache.get(cache_key)
        if cached:
            return [CandlePoint(**c) for c in cached]
        end = datetime.now(timezone.utc).date()
        start = end - timedelta(days=days)
        data = self._get(
            f"/v2/aggs/ticker/{ticker.upper()}/range/1/day/{start}/{end}",
            {"adjusted": "true", "sort": "asc", "limit": 50000},
        )
        points: List[CandlePoint] = []
        if data and data.get("results"):
            for bar in data["results"]:
                ts = datetime.fromtimestamp(bar["t"] / 1000, tz=timezone.utc)
                points.append(CandlePoint(
                    date=ts.strftime("%Y-%m-%d"),
                    open=float(bar["o"]), high=float(bar["h"]),
                    low=float(bar["l"]), close=float(bar["c"]),
                    volume=float(bar.get("v", 0)),
                ))
            self.cache.set(cache_key, [p.model_dump() for p in points], 3600)
        return points

    def get_shares_outstanding(self, ticker: str) -> Optional[float]:
        data = self.get_ticker_details(ticker)
        if data and data.get("results", {}).get("share_class_shares_outstanding"):
            return float(data["results"]["share_class_shares_outstanding"])
        return None

    def get_news(self, ticker: str, limit: int = 20) -> list[NewsArticle]:
        symbol = ticker.upper()
        cache_key = f"massive:news:{symbol}:{limit}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return [NewsArticle(**item) for item in cached[:limit]]

        data = self._get("/v2/reference/news", {"ticker": symbol, "limit": limit, "order": "desc"})
        if not data or not data.get("results"):
            self.cache.set(cache_key, [], NEWS_CACHE_TTL_SECONDS)
            return []

        articles: list[NewsArticle] = []
        for item in data["results"][:limit]:
            title = item.get("title")
            if not title:
                continue
            pub = item.get("published_utc") or ""
            pub_date = pub[:10] if len(pub) >= 10 else datetime.now(timezone.utc).strftime("%Y-%m-%d")
            publisher = item.get("publisher") or {}
            pub_name = publisher.get("name") if isinstance(publisher, dict) else "Massive"
            sentiment, reasoning = _sentiment_from_insights(item.get("insights") or [], symbol)
            summary = (item.get("description") or "")[:500] or None
            if reasoning and summary:
                summary = f"{summary}\n\nSentiment: {reasoning}"[:500]
            elif reasoning:
                summary = reasoning[:500]
            articles.append(
                NewsArticle(
                    title=title,
                    source=pub_name or "Massive",
                    date=pub_date,
                    url=item.get("article_url") or item.get("amp_url") or "",
                    summary=summary,
                    source_type="massive",
                    sentiment=sentiment,
                )
            )
        self.cache.set(cache_key, [a.model_dump() for a in articles], NEWS_CACHE_TTL_SECONDS)
        return articles
