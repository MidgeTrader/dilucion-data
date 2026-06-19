"""Benzinga news API — strong coverage for US micro-caps (paid API key)."""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET

import httpx

from cache import TTLCache
from config import get_settings
from models import NewsArticle

logger = logging.getLogger(__name__)


class BenzingaClient:
    BASE = "https://api.benzinga.com/api/v2/news"

    def __init__(self, cache: TTLCache) -> None:
        self.settings = get_settings()
        self.cache = cache
        self.api_key = self.settings.benzinga_api_key

    def get_news(self, ticker: str, limit: int = 20) -> list[NewsArticle]:
        symbol = ticker.upper()
        cache_key = f"benzinga:news:{symbol}"
        cached = self.cache.get(cache_key)
        if cached:
            return [NewsArticle(**item) for item in cached[:limit]]

        if not self.api_key:
            return []

        try:
            with httpx.Client(timeout=25) as client:
                resp = client.get(
                    self.BASE,
                    params={
                        "tickers": symbol,
                        "pageSize": limit,
                        "displayOutput": "full",
                        "token": self.api_key,
                    },
                )
                resp.raise_for_status()
                root = ET.fromstring(resp.text)
        except Exception as exc:
            logger.error("Benzinga news error for %s: %s", symbol, exc)
            return []

        articles: list[NewsArticle] = []
        for item in root.findall(".//item")[:limit]:
            title = _text(item, "title")
            if not title:
                continue
            pub = _text(item, "created") or _text(item, "updated")
            pub_date = pub[:10] if pub and len(pub) >= 10 else ""
            url = _text(item, "url") or ""
            teaser = _text(item, "teaser") or _text(item, "body") or ""
            articles.append(
                NewsArticle(
                    title=title,
                    source="Benzinga",
                    date=pub_date or "",
                    url=url,
                    summary=teaser[:500] if teaser else None,
                    source_type="benzinga",
                )
            )

        if articles:
            self.cache.set(cache_key, [a.model_dump() for a in articles], 900)
        return articles


def _text(parent: ET.Element, tag: str) -> str | None:
    el = parent.find(tag)
    if el is not None and el.text:
        return el.text.strip()
    return None
