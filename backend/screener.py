"""Gap Screener — Yahoo Finance active penny stocks."""

from __future__ import annotations

import logging

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class GapScreener:
    YAHOO_URL = "https://finance.yahoo.com/research-hub/screener/most_active_penny_stocks/"

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"})

    def _to_num(self, s: str) -> float:
        s = s.strip().replace("%", "").replace("+", "").replace(",", "").replace("--", "0")
        try:
            return float(s)
        except ValueError:
            return 0.0

    def scan(self, min_gap: float = 25.0, min_price: float = 0.30, max_results: int = 30) -> list[dict]:
        try:
            resp = self.session.get(self.YAHOO_URL, timeout=30)
        except Exception as exc:
            logger.warning("Yahoo fetch failed: %s", exc)
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        table = soup.find("table")
        if not table:
            return []

        results = []
        for tr in table.find_all("tr")[1:]:
            cells = [td.get_text(strip=True) for td in tr.find_all("td")]
            if len(cells) < 7:
                continue

            price = self._to_num(cells[4]) if len(cells) > 4 else 0
            gap = self._to_num(cells[6]) if len(cells) > 6 else 0

            if gap < min_gap or price < min_price:
                continue

            raw = cells[1].upper() if len(cells) > 1 else ""
            # Fix Yahoo prefix bug: repeated first char means remove it
            if len(raw) > 3 and raw[0] == raw[1]:
                raw = raw[1:]

            results.append({
                "symbol": raw,
                "name": cells[2][:60] if len(cells) > 2 else "",
                "price": round(price, 4),
                "gap_pct": round(gap, 1),
                "volume": self._to_num(cells[7]) if len(cells) > 7 else 0,
            })

            if len(results) >= max_results:
                break

        results.sort(key=lambda x: x["gap_pct"], reverse=True)
        return results
