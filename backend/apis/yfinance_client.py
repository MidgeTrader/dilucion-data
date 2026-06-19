"""YFinance fallback for price and shares data."""

from __future__ import annotations

import logging
from typing import Optional

from cache import TTLCache
from config import get_settings

logger = logging.getLogger(__name__)


class YFinanceClient:
    """Fallback market data via yfinance when Finnhub/Polygon unavailable."""

    def __init__(self, cache: TTLCache) -> None:
        self.settings = get_settings()
        self.cache = cache

    def get_price(self, ticker: str) -> Optional[float]:
        cache_key = f"yfinance:price:{ticker.upper()}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached.get("price")
        try:
            import yfinance as yf
            info = yf.Ticker(ticker.upper()).fast_info
            price = float(info.last_price) if hasattr(info, "last_price") and info.last_price else None
            if price:
                self.cache.set(cache_key, {"price": price}, 300)
            return price
        except Exception as exc:
            logger.debug("yfinance price fallback failed for %s: %s", ticker, exc)
            return None

    def get_shares_outstanding(self, ticker: str) -> Optional[float]:
        cache_key = f"yfinance:shares:{ticker.upper()}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached.get("shares")
        try:
            import yfinance as yf
            info = yf.Ticker(ticker.upper()).info
            shares = info.get("sharesOutstanding") or info.get("floatShares")
            if shares:
                shares = float(shares)
                self.cache.set(cache_key, {"shares": shares}, 86400)
            return float(shares) if shares else None
        except Exception as exc:
            logger.debug("yfinance shares fallback failed: %s", exc)
            return None
