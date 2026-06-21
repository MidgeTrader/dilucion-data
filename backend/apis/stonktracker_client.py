"""Stonktracker client — solo borrow fee."""

from __future__ import annotations

import logging
import re
from typing import Optional

import httpx

from cache import TTLCache
from models import ShortInterestData

logger = logging.getLogger(__name__)


class StonktrackerClient:
    """Extrae unicamente el borrow fee de stonktracker.com."""

    BASE = "https://stonktracker.com/stock"

    def __init__(self, cache: TTLCache) -> None:
        self.cache = cache

    def get_borrow_data(self, ticker: str) -> Optional[ShortInterestData]:
        """Obtiene solo el borrow fee desde stonktracker."""
        symbol = ticker.upper()
        cache_key = f"stonktracker:borrow:{symbol}"

        # Cache hit
        cached = self.cache.get(cache_key)
        if cached is not None:
            if isinstance(cached, dict):
                return ShortInterestData(**cached)
            return cached

        # Fetch page
        html = self._fetch_page(symbol)
        if not html:
            return None

        # Extraer solo borrow fee
        borrow_rate = self._extract_borrow_fee(html)
        if borrow_rate is None:
            logger.info("Stonktracker %s: no se encontro borrow fee", symbol)
            return None

        logger.info("Stonktracker %s: borrow_fee=%s%%", symbol, borrow_rate)

        result = ShortInterestData(
            ticker=symbol,
            borrow_rate=borrow_rate,
            source="stonktracker",
        )

        # 48h cache
        self.cache.set(cache_key, result.model_dump(), 172800)
        return result

    def _fetch_page(self, symbol: str) -> Optional[str]:
        """Fetch the stonktracker page HTML."""
        try:
            with httpx.Client(timeout=20, follow_redirects=True) as client:
                resp = client.get(
                    f"{self.BASE}/{symbol}",
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/125.0.0.0 Safari/537.36"
                        ),
                        "Accept": "text/html,application/xhtml+xml",
                        "Accept-Language": "en-US,en;q=0.9",
                    },
                )
                if resp.status_code == 404:
                    logger.info("Stonktracker: no page for %s", symbol)
                    return None
                resp.raise_for_status()
                return resp.text
        except httpx.HTTPError as exc:
            logger.warning("Stonktracker HTTP error for %s: %s", symbol, exc)
            return None

    def _extract_borrow_fee(self, html: str) -> Optional[float]:
        """Busca la card 'Borrow Fee' y extrae el porcentaje."""
        try:
            # Buscar todas las metric cards
            pattern = (
                r'<p class="text-sm text-gray-500 uppercase tracking-wide">'
                r"(.*?)</p>\s*"
                r'<p class="text-2xl font-bold[^"]*">'
                r"(.*?)</p>"
            )
            for label, value in re.findall(pattern, html, re.DOTALL):
                if "borrow fee" in label.strip().lower():
                    raw = re.sub(r"\s+", " ", value.strip())
                    m = re.search(r"([\d.]+)", raw)
                    if m:
                        return float(m.group(1))
        except Exception as exc:
            logger.warning("Stonktracker parse error: %s", exc)
        return None
