"""SEC EDGAR full-text search (EFTS) for dilution keywords."""

from __future__ import annotations

import logging
import time
from typing import List, Optional

from tenacity import retry, stop_after_attempt, wait_exponential

from apis.connection_pool import get_client
from config import get_settings
from models import SearchHit

logger = logging.getLogger(__name__)

EFTS_URL = "https://efts.sec.gov/LATEST/search-index"

DEFAULT_QUERIES = [
    "At-the-market offering",
    "Pre-Funded Warrants",
    "Full Ratchet",
    "Aggregate offering price of up to",
    "Convertible note",
    "death spiral",
]


class EFTSSearch:
    """Full-text search against SEC EDGAR filings."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.headers = {
            "User-Agent": self.settings.sec_user_agent,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=20), reraise=False)
    def search(
        self,
        query: str,
        *,
        form_types: Optional[List[str]] = None,
        limit: int = 20,
    ) -> List[SearchHit]:
        """Search SEC full-text index."""
        payload = {
            "q": query,
            "dateRange": "custom",
            "startdt": "2020-01-01",
            "enddt": "2026-12-31",
            "from": 0,
            "size": limit,
        }
        if form_types:
            payload["forms"] = form_types

        time.sleep(0.1)
        try:
            client = get_client(timeout=30)
            resp = client.post(EFTS_URL, json=payload, headers=self.headers)
            if resp.status_code in (403, 429):
                logger.warning("EFTS returned %d for query: %s", resp.status_code, query)
                return []
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.error("EFTS search failed: %s", exc)
            return []

        hits: List[SearchHit] = []
        for item in data.get("hits", {}).get("hits", []):
            src = item.get("_source", {})
            cik = str(src.get("ciks", [""])[0] if src.get("ciks") else "").lstrip("0") or "0"
            accession = src.get("adsh", "")
            form = src.get("form", "")
            filed = src.get("file_date", "")
            entity = src.get("display_names", [""])[0] if src.get("display_names") else ""
            url = f"https://www.sec.gov/Archives/edgar/data/{cik.zfill(10)}/{accession.replace('-', '')}/{accession}-index.htm"
            excerpt = " ".join(item.get("highlight", {}).get("file_body", []))[:500]
            hits.append(
                SearchHit(
                    query=query,
                    cik=cik,
                    company_name=entity,
                    form_type=form,
                    filed_date=filed,
                    accession_number=accession,
                    filing_url=url,
                    excerpt=excerpt or None,
                )
            )
        return hits

    def search_all_defaults(self, limit_per_query: int = 10) -> List[SearchHit]:
        """Run all default dilution keyword searches."""
        all_hits: List[SearchHit] = []
        for q in DEFAULT_QUERIES:
            all_hits.extend(self.search(q, limit=limit_per_query))
            time.sleep(0.1)
        return all_hits
