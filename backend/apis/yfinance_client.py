"""Yahoo Finance news via yfinance — strong fallback for micro-caps."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from cache import TTLCache
from config import get_settings
from models import NewsArticle, QuoteData

logger = logging.getLogger(__name__)


class YFinanceClient:
    """Fallback market data via yfinance when Finnhub/Polygon unavailable."""

    def __init__(self, cache: TTLCache) -> None:
        self.settings = get_settings()
        self.cache = cache

    def get_quote(self, ticker: str) -> Optional[QuoteData]:
        symbol = ticker.upper()
        cache_key = f"yfinance:quote:{symbol}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return QuoteData(**cached)
        try:
            import yfinance as yf

            fi = yf.Ticker(symbol).fast_info
            price = float(fi.last_price) if getattr(fi, "last_price", None) else None
            prev = None
            for attr in ("previous_close", "regular_market_previous_close"):
                val = getattr(fi, attr, None)
                if val:
                    prev = float(val)
                    break
            change_pct = None
            if price is not None and prev and prev > 0:
                change_pct = round((price - prev) / prev * 100, 4)
            if price is None:
                return None
            quote = QuoteData(
                ticker=symbol,
                price=price,
                change_percent=change_pct,
                timestamp=datetime.now(timezone.utc),
                source="yfinance",
            )
            self.cache.set(cache_key, quote.model_dump(), 300)
            return quote
        except Exception as exc:
            logger.debug("yfinance quote failed for %s: %s", symbol, exc)
            return None

    def get_price(self, ticker: str) -> Optional[float]:
        quote = self.get_quote(ticker)
        return quote.price if quote else None

    def get_profile_fields(self, ticker: str) -> dict[str, Any]:
        symbol = ticker.upper()
        cache_key = f"yfinance:profile:{symbol}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        fields: dict[str, any] = {
            "company_name": None, "sector": None, "industry": None,
            "country": None, "exchange": None, "website": None,
            "longBusinessSummary": None, "employees": None,
            "market_cap": None, "enterprise_value": None,
            "avg_volume": None, "cash_per_share": None,
            "institutional_ownership": None, "days_to_cover": None,
            "shares_outstanding": None, "float_shares": None,
            "short_percent_float": None,
        }
        try:
            import yfinance as yf

            info = yf.Ticker(symbol).info or {}
            fields = {
                "company_name": info.get("longName") or info.get("shortName"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "country": info.get("country"),
                "exchange": (info.get("exchange") or "").split(" ")[0] if info.get("exchange") else None,
                "website": info.get("website"),
                "longBusinessSummary": info.get("longBusinessSummary"),
                "employees": int(info["fullTimeEmployees"]) if info.get("fullTimeEmployees") else None,
                "market_cap": float(info["marketCap"]) if info.get("marketCap") else None,
                "enterprise_value": float(info["enterpriseValue"]) if info.get("enterpriseValue") else None,
                "avg_volume": float(info["averageVolume"]) if info.get("averageVolume") else None,
                "cash_per_share": float(info["totalCashPerShare"]) if info.get("totalCashPerShare") else None,
                "institutional_ownership": (
                    round(float(info["heldPercentInstitutions"]) * 100, 2)
                    if info.get("heldPercentInstitutions") else None
                ),
                "days_to_cover": float(info["daysToCover"]) if info.get("daysToCover") else None,
                "shares_outstanding": float(info["sharesOutstanding"]) if info.get("sharesOutstanding") else None,
                "float_shares": float(info["floatShares"]) if info.get("floatShares") else None,
                "short_percent_float": round(float(info["shortPercentOfFloat"]) * 100, 2) if info.get("shortPercentOfFloat") else None,
            }
            self.cache.set(cache_key, fields, 86400)
        except Exception as exc:
            logger.debug("yfinance profile failed for %s: %s", symbol, exc)
        return fields

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

    def get_news(self, ticker: str, limit: int = 20) -> list[NewsArticle]:
        symbol = ticker.upper()
        cache_key = f"yfinance:news:{symbol}"
        cached = self.cache.get(cache_key)
        if cached:
            return [NewsArticle(**item) for item in cached[:limit]]

        try:
            import yfinance as yf
            raw = getattr(yf.Ticker(symbol), "news", None) or []
            articles: list[NewsArticle] = []
            for item in raw[:limit]:
                title = item.get("title")
                if not title:
                    continue
                ts = item.get("providerPublishTime")
                if ts:
                    pub_date = datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d")
                else:
                    pub_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                link = item.get("link") or item.get("url") or ""
                publisher = item.get("publisher") or item.get("source") or "Yahoo Finance"
                articles.append(
                    NewsArticle(
                        title=title,
                        source=publisher,
                        date=pub_date,
                        url=link,
                        summary=(item.get("summary") or item.get("description") or "")[:500] or None,
                        source_type="yfinance",
                    )
                )
            if articles:
                self.cache.set(cache_key, [a.model_dump() for a in articles], 900)
            return articles
        except Exception as exc:
            logger.error("yfinance news error for %s: %s", symbol, exc)
            return []
