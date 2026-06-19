"""Polygon.io API client."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from apis._rate_limit import RateLimiter
from cache import TTLCache
from config import get_settings
from models import CandlePoint

logger = logging.getLogger(__name__)


class PolygonClient:
    BASE = "https://api.polygon.io"

    def __init__(self, cache: TTLCache) -> None:
        self.settings = get_settings()
        self.cache = cache
        self.limiter = RateLimiter(self.settings.polygon_rate_limit_per_min)
        self.api_key = self.settings.polygon_api_key

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=20), reraise=False)
    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Optional[dict]:
        if not self.api_key:
            return None
        self.limiter.wait()
        params = dict(params or {})
        params["apiKey"] = self.api_key
        try:
            with httpx.Client(timeout=30) as client:
                resp = client.get(f"{self.BASE}{path}", params=params)
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            logger.error("Polygon error: %s", exc)
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
            path = next_url.replace(self.BASE, "") if next_url else ""
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
        end = datetime.utcnow().date()
        start = end - timedelta(days=days)
        data = self._get(
            f"/v2/aggs/ticker/{ticker.upper()}/range/1/day/{start}/{end}",
            {"adjusted": "true", "sort": "asc", "limit": 50000},
        )
        points: List[CandlePoint] = []
        if data and data.get("results"):
            for bar in data["results"]:
                ts = datetime.utcfromtimestamp(bar["t"] / 1000)
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
