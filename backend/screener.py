"""Gap Screener — Yahoo Finance active penny stocks."""

from __future__ import annotations

import logging

import requests
import yfinance as yf
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class GapScreener:
    YAHOO_URL = "https://finance.yahoo.com/research-hub/screener/most_active_penny_stocks/"

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"})

    def _get_yf_data(self, ticker: str) -> dict:
        try:
            t = yf.Ticker(ticker)
            info = t.info or {}
            price = info.get("currentPrice") or info.get("regularMarketPrice")
            prev_close = info.get("previousClose")
            if not price or not prev_close:
                return {}
            change = price - prev_close
            gap = (change / prev_close) * 100
            return {
                "symbol": ticker,
                "name": str(info.get("shortName") or info.get("longName") or ticker)[:60],
                "price": round(float(price), 4),
                "change": round(float(change), 4),
                "change_pct": round(float(gap), 1),
                "gap_pct": round(float(gap), 1),
                "prev_close": round(float(prev_close), 4),
                "open": round(float(info.get("regularMarketOpen", 0)), 4),
                "high": round(float(info.get("regularMarketDayHigh", 0)), 4),
                "low": round(float(info.get("regularMarketDayLow", 0)), 4),
                "volume": int(info.get("regularMarketVolume", 0)),
                "avg_volume": int(info.get("averageVolume", 0)),
            }
        except Exception as exc:
            logger.debug("yfinance fail %s: %s", ticker, exc)
            return {}

    def scan(self, sort_type: str = "gainers", min_gap: float = 25.0, min_price: float = 0.30, max_results: int = 30) -> list[dict]:
        try:
            resp = self.session.get(self.YAHOO_URL, timeout=30)
            soup = BeautifulSoup(resp.text, "lxml")
            table = soup.find("table")
            if not table:
                return []
            symbols = []
            for tr in table.find_all("tr")[1:]:
                cells = [td.get_text(strip=True) for td in tr.find_all("td")]
                if len(cells) < 7:
                    continue
                raw = cells[1].strip().upper() if len(cells) > 1 else ""
                if len(raw) > 3 and raw[0] == raw[1]:
                    raw = raw[1:]
                symbols.append(raw)
        except Exception as exc:
            logger.warning("Yahoo fail: %s", exc)
            return []

        results = []
        for t in symbols[:max_results * 2]:
            d = self._get_yf_data(t)
            if not d or d["price"] < min_price:
                continue
            if sort_type == "losers" and d["change_pct"] > -min_gap:
                continue
            if sort_type not in ("losers", "premarket", "aftermarket") and d["gap_pct"] < min_gap:
                continue
            results.append(d)
            if len(results) >= max_results:
                break

        results.sort(key=lambda x: x["change_pct"], reverse=(sort_type != "losers"))
        return results
