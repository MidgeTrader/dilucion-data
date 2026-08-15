"""SEC company facts and submissions API client."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from tenacity import retry, stop_after_attempt, wait_exponential

from apis.connection_pool import get_client
from cache import TTLCache
from config import get_settings
from models import SECFilingMeta

logger = logging.getLogger(__name__)


class CompanyFactsClient:
    """Fetch company data from data.sec.gov APIs."""

    SEC_DATA = "https://data.sec.gov"
    SEC_WWW = "https://www.sec.gov"

    def __init__(self, cache: Optional[TTLCache] = None) -> None:
        self.settings = get_settings()
        self.cache = cache or TTLCache(self.settings.cache_db_path)
        self.headers = {
            "User-Agent": self.settings.sec_user_agent,
            "Accept": "application/json",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=15), reraise=False)
    def _get(self, base: str, path: str, cache_key: str, ttl: int) -> Optional[dict]:
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        time.sleep(0.1)
        try:
            client = get_client()  # default: connect=5s, read=15s
            resp = client.get(f"{base}{path}", headers=self.headers)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            data = resp.json()
            self.cache.set(cache_key, data, ttl)
            return data
        except Exception as exc:
            logger.error("SEC API error %s: %s", path, exc)
            return None

    def resolve_cik_from_ticker(self, ticker: str) -> Optional[str]:
        """Resolve CIK using SEC company tickers JSON."""
        data = self._get(self.SEC_WWW, "/files/company_tickers.json", "sec:company_tickers", 86400)
        if not data:
            return None
        for entry in data.values():
            if str(entry.get("ticker", "")).upper() == ticker.upper():
                return str(entry["cik_str"]).lstrip("0") or "0"
        return None

    def get_submissions(self, cik: str) -> Optional[dict]:
        padded = cik.zfill(10)
        return self._get(self.SEC_DATA, f"/submissions/CIK{padded}.json", f"sec:submissions:{cik}", 3600)

    def get_recent_filings(
        self,
        cik: str,
        *,
        form_filter: Optional[List[str]] = None,
        limit: int = 40,
    ) -> List[SECFilingMeta]:
        """List recent filings for a CIK."""
        data = self.get_submissions(cik)
        if not data:
            return []
        recent = data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        dates = recent.get("filingDate", [])
        accessions = recent.get("accessionNumber", [])
        docs = recent.get("primaryDocument", [])
        descriptions = recent.get("primaryDocDescription", [])

        results: List[SECFilingMeta] = []
        for i in range(min(len(forms), limit * 8)):
            form = forms[i]
            if form_filter and form not in form_filter:
                if not any(form.startswith(f.split("/")[0]) for f in form_filter):
                    continue
            accession = accessions[i].replace("-", "")
            acc_raw = accessions[i]
            primary = docs[i] if i < len(docs) else ""
            desc = descriptions[i] if i < len(descriptions) else ""
            url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{primary}"
            results.append(
                SECFilingMeta(
                    accession_number=acc_raw,
                    form_type=form,
                    filed_date=dates[i],
                    url=url,
                    description=desc,
                )
            )
            if len(results) >= limit:
                break
        return results

    def get_shares_outstanding(self, cik: str) -> Optional[float]:
        """Extract shares outstanding from company facts XBRL."""
        padded = cik.zfill(10)
        data = self._get(self.SEC_DATA, f"/api/xbrl/companyfacts/CIK{padded}.json", f"sec:facts:{cik}", 7200)
        if not data:
            return None
        try:
            us_gaap = data.get("facts", {}).get("us-gaap", {})
            for concept in ("CommonStockSharesOutstanding", "EntityCommonStockSharesOutstanding"):
                if concept in us_gaap:
                    units = us_gaap[concept].get("units", {})
                    shares = units.get("shares", [])
                    if shares:
                        return float(shares[-1]["val"])
        except (KeyError, TypeError, ValueError) as exc:
            logger.debug("Could not parse shares outstanding: %s", exc)
        return None

    def get_company_info(self, cik: str) -> Dict[str, Any]:
        data = self.get_submissions(cik)
        if not data:
            return {}
        return {
            "cik": cik,
            "name": data.get("name"),
            "tickers": data.get("tickers", []),
            "sic": data.get("sic"),
            "sic_description": data.get("sicDescription"),
            "category": data.get("category"),
        }
