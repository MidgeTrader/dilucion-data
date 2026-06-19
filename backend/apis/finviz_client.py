"""Finviz data client — short interest, borrow rate, float, insider data."""

from __future__ import annotations

import logging
from typing import Optional

from cache import TTLCache
from config import get_settings

logger = logging.getLogger(__name__)


class FinvizClient:
    """Fetch fundamentals and ownership data from Finviz."""

    def __init__(self, cache: TTLCache) -> None:
        self.cache = cache
        self.settings = get_settings()

    def get_profile_fields(self, ticker: str) -> dict:
        """Return a dict of finviz fields mapped to our profile keys."""
        symbol = ticker.upper()
        cache_key = f"finviz:profile:{symbol}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        result = {
            "sector": None, "industry": None,
            "float_shares": None, "shares_outstanding": None,
            "short_percent_float": None, "days_to_cover": None,
            "borrow_rate": None, "short_interest": None,
            "institutional_ownership": None,
            "insider_ownership": None, "insider_transactions": None,
            "employees": None, "country": None,
        }
        try:
            from finvizfinance.quote import finvizfinance

            f = finvizfinance(symbol)
            data = f.ticker_fundament()
            if not data:
                return result

            # Map Finviz keys → our keys
            def fv(key: str) -> Optional[str]:
                return data.get(key)

            # Shares
            raw_float = fv("Shs Float")
            if raw_float:
                result["float_shares"] = self._parse_number(raw_float)

            raw_out = fv("Shs Outstand")
            if raw_out:
                result["shares_outstanding"] = self._parse_number(raw_out)

            # Short data
            raw_sf = fv("Short Float")
            if raw_sf:
                result["short_percent_float"] = self._parse_pct(raw_sf)

            raw_sr = fv("Short Ratio")
            if raw_sr:
                result["days_to_cover"] = float(raw_sr)

            # Ownership
            raw_inst = fv("Inst Own")
            if raw_inst:
                result["institutional_ownership"] = self._parse_pct(raw_inst)

            raw_ins = fv("Insider Own")
            if raw_ins:
                result["insider_ownership"] = self._parse_pct(raw_ins)

            raw_ins_tr = fv("Insider Trans")
            if raw_ins_tr:
                result["insider_transactions"] = self._parse_pct(raw_ins_tr)

            # Sector / Industry (more granular than Polygon)
            raw_sector = fv("Sector")
            if raw_sector:
                result["sector"] = raw_sector
            raw_ind = fv("Industry")
            if raw_ind:
                result["industry"] = raw_ind

            # Employees
            raw_emp = fv("Employees")
            if raw_emp:
                try:
                    result["employees"] = int(raw_emp.replace(",", ""))
                except ValueError:
                    pass

            raw_country = fv("Country")
            if raw_country:
                result["country"] = raw_country

            self.cache.set(cache_key, result, 21600)  # 6h cache

        except Exception as exc:
            logger.warning("Finviz failed for %s: %s", symbol, exc)

        return result

    @staticmethod
    def _parse_number(val: str) -> Optional[float]:
        """Parse '4.80M' → 4800000, '9.26B' → 9260000000."""
        if not val:
            return None
        val = val.strip().replace(",", "")
        if val in ("-", ""):
            return None
        multiplier = 1
        if val[-1].upper() == "M":
            multiplier = 1_000_000
            val = val[:-1]
        elif val[-1].upper() == "B":
            multiplier = 1_000_000_000
            val = val[:-1]
        elif val[-1].upper() == "K":
            multiplier = 1_000
            val = val[:-1]
        try:
            return float(val) * multiplier
        except ValueError:
            return None

    @staticmethod
    def _parse_pct(val: str) -> Optional[float]:
        """Parse '5.48%' → 5.48 (percentage value, not decimal)."""
        if not val or val == "-":
            return None
        try:
            return float(val.rstrip("%"))
        except ValueError:
            return None
