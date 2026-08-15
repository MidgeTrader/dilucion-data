"""Google News RSS search — free fallback for obscure tickers."""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.parse import quote_plus

from apis.connection_pool import get_client
from cache import TTLCache
from config import get_settings
from models import NewsArticle

logger = logging.getLogger(__name__)


class GoogleNewsClient:
    BASE = "https://news.google.com/rss/search"

    def __init__(self, cache: TTLCache) -> None:
        self.cache = cache
        self.settings = get_settings()

    def get_news(self, ticker: str, company_name: str | None = None, limit: int = 15) -> list[NewsArticle]:
        symbol = ticker.upper()
        cache_key = f"google:news:{symbol}"
        cached = self.cache.get(cache_key)
        if cached:
            return [NewsArticle(**item) for item in cached[:limit]]

        query = f"{symbol} stock"
        if company_name:
            short = company_name.split(" Class")[0].split(" Inc")[0].strip()
            if short and short.upper() != symbol:
                query = f'"{symbol}" OR "{short}"'

        url = f"{self.BASE}?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
        try:
            client = get_client(timeout=20, follow_redirects=True)
            resp = client.get(url, headers={"User-Agent": "Mozilla/5.0 (compatible; DilutionTracker/1.0)"})
            resp.raise_for_status()
            root = ET.fromstring(resp.text)
        except Exception as exc:
            logger.error("Google News RSS error for %s: %s", symbol, exc)
            return []

        articles: list[NewsArticle] = []
        for item in root.findall(".//item")[: limit * 2]:
            title_el = item.find("title")
            link_el = item.find("link")
            pub_el = item.find("pubDate")
            source_el = item.find("source")
            if title_el is None or not title_el.text:
                continue
            title = title_el.text.strip()
            pub_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            if pub_el is not None and pub_el.text:
                try:
                    from email.utils import parsedate_to_datetime
                    pub_date = parsedate_to_datetime(pub_el.text).strftime("%Y-%m-%d")
                except Exception:
                    pass
            source_name = source_el.text.strip() if source_el is not None and source_el.text else "Google News"
            articles.append(
                NewsArticle(
                    title=title,
                    source=source_name,
                    date=pub_date,
                    url=(link_el.text or "").strip() if link_el is not None else "",
                    source_type="google",
                )
            )
            if len(articles) >= limit:
                break

        if articles:
            self.cache.set(cache_key, [a.model_dump() for a in articles], 1800)
        return articles
