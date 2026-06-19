"""Aggregates news from SEC filings + all external sources."""

from __future__ import annotations

import logging
import re
from typing import Any, Iterable

from apis.benzinga_client import BenzingaClient
from apis.eodhd_client import EodhdClient
from apis.finnhub_client import FinnhubClient
from apis.google_news_client import GoogleNewsClient
from apis.polygon_client import PolygonClient
from apis.yfinance_client import YFinanceClient
from cache import TTLCache
from config import get_settings
from models import NewsArticle

logger = logging.getLogger(__name__)

SEC_NEWS_FORMS = {"8-K", "8-K/A", "S-3", "S-3/A", "424B2", "424B3", "424B4", "424B5", "424B5/A", "6-K", "F-3", "F-1", "10-Q", "10-K"}

SOURCE_PRIORITY = {
    "sec": 0,
    "massive": 1,
    "polygon": 1,  # legacy source_type
    "eodhd": 2,
    "benzinga": 3,
    "yfinance": 4,
    "finnhub": 5,
    "google": 6,
}


class NewsAggregator:
    def __init__(self, cache: TTLCache) -> None:
        self.cache = cache
        self.finnhub = FinnhubClient(cache)
        self.polygon = PolygonClient(cache)
        self.yfinance = YFinanceClient(cache)
        self.google = GoogleNewsClient(cache)
        self.benzinga = BenzingaClient(cache)
        self.eodhd = EodhdClient(cache)

    def get_all_news(
        self,
        ticker: str,
        company_name: str | None = None,
        filings: Iterable[Any] | None = None,
        limit: int = 30,
    ) -> list[NewsArticle]:
        symbol = ticker.upper()
        cache_key = f"news:all:{symbol}:{limit}"
        cached = self.cache.get(cache_key)
        if cached:
            return [NewsArticle(**item) for item in cached]

        combined: list[NewsArticle] = []

        combined.extend(self._filings_to_news(filings))
        massive_news = self.polygon.get_news(symbol, limit=15)
        combined.extend(massive_news)
        # EODHD free tier: ~20 calls/day — skip if Massive already has coverage
        if len(massive_news) < 3:
            combined.extend(self.eodhd.get_news(symbol, limit=20))
        combined.extend(self.benzinga.get_news(symbol, limit=15))
        combined.extend(self.yfinance.get_news(symbol, limit=15))
        combined.extend(self.finnhub.get_company_news(symbol, limit=15))
        combined.extend(self.google.get_news(symbol, company_name, limit=10))

        merged = self._dedupe_and_sort(combined, limit)
        if merged:
            self.cache.set(cache_key, [a.model_dump() for a in merged], 600)
        return merged

    def _filings_to_news(self, filings: Iterable[Any] | None) -> list[NewsArticle]:
        if not filings:
            return []
        articles: list[NewsArticle] = []
        for f in filings:
            form = _field(f, "form_type") or ""
            base_form = form.split("/")[0].upper()
            if base_form not in SEC_NEWS_FORMS and not any(form.upper().startswith(x) for x in SEC_NEWS_FORMS):
                continue
            filed = _field(f, "filed_date")
            if hasattr(filed, "isoformat"):
                date_str = filed.isoformat()
            else:
                date_str = str(filed) if filed else ""
            ticker = _field(f, "ticker") or ""
            title = f"{form} — {ticker} SEC filing"
            summary = _field(f, "summary")
            url = _field(f, "source_url") or ""
            if not url and _field(f, "accession_number"):
                url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={_field(f, 'cik') or ticker}"
            articles.append(
                NewsArticle(
                    title=title,
                    source="SEC EDGAR",
                    date=date_str[:10] if date_str else "",
                    url=url,
                    summary=(summary or "")[:500] or None,
                    source_type="sec",
                )
            )
        return articles

    def _dedupe_and_sort(self, articles: list[NewsArticle], limit: int) -> list[NewsArticle]:
        seen: set[str] = set()
        unique: list[NewsArticle] = []
        for a in sorted(articles, key=self._sort_key, reverse=True):
            key = _norm_key(a)
            if key in seen:
                continue
            seen.add(key)
            unique.append(a)
            if len(unique) >= limit:
                break
        return unique

    def _sort_key(self, a: NewsArticle) -> tuple:
        # Sort by date DESC first, then by source priority, then title
        date_str = a.date or ""
        # Invert date string for DESC sort (most recent first)
        return (date_str, SOURCE_PRIORITY.get(a.source_type or "", 99), a.title)


def _field(obj: Any, name: str) -> Any:
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


def _norm_key(a: NewsArticle) -> str:
    if a.url and a.url.startswith("http"):
        return a.url.lower().rstrip("/")
    title = re.sub(r"\W+", " ", (a.title or "").lower()).strip()
    return f"{title}|{a.date}"
