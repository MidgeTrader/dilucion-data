"""Gap Screener — Yahoo Finance active penny stocks + Nasdaq halts."""

from __future__ import annotations

import logging
import re

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

    @staticmethod
    def _fmt_reason(raw: str) -> str:
        """Split concatenated halt reasons: H10T1T12 -> H10-T1-T12."""
        if not raw:
            return ""
        parts = re.findall(r'[A-Za-z]+\d*', raw)
        return "-".join(parts) if parts else raw

    def halts(self) -> list[dict]:
        """Fetch real trading halts via Playwright (intercepts RPCHandler.axd)."""
        import time
        from bs4 import BeautifulSoup as BS
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                html_data = None

                def _capture(response):
                    nonlocal html_data
                    if "RPCHandler.axd" in response.url:
                        try:
                            j = response.json()
                            if isinstance(j, dict) and "result" in j and "<table" in str(j["result"]):
                                html_data = j["result"]
                        except: pass

                page.on("response", _capture)
                page.goto("https://www.nasdaqtrader.com/trader.aspx?id=tradehalts", wait_until="networkidle")
                time.sleep(2)
                browser.close()

            if html_data:
                soup = BS(html_data, "lxml")
                halts = []
                for tr in soup.find_all("tr")[1:]:
                    cells = [td.get_text(strip=True) for td in tr.find_all("td")]
                    if len(cells) >= 5:
                        halts.append({
                            "symbol": cells[2] if len(cells) > 2 else "",
                            "status": "Active",
                            "reason": self._fmt_reason(cells[5]) if len(cells) > 5 else "",
                            "date": cells[0] if len(cells) > 0 else "",
                            "halt_time": cells[1].split(".")[0] if len(cells) > 1 else "",
                            "resume_time": cells[6] if len(cells) > 6 else "",
                            "duration": cells[6] if len(cells) > 6 else "",
                            "market": cells[4] if len(cells) > 4 else "",
                        })
                if halts:
                    return halts
        except Exception as exc:
            logger.warning("Playwright halts failed: %s", exc)
        return []
