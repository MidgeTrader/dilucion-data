"""Daily SEC master index scanner for dilution-critical form types."""

from __future__ import annotations

import io
import logging
import time
from datetime import date, datetime, timedelta
from typing import List, Optional

import pandas as pd
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from config import get_settings
from models import CriticalFiling

logger = logging.getLogger(__name__)

CRITICAL_FORMS = {
    "S-3": "🔴",
    "S-3/A": "🔴",
    "424B3": "🔴",
    "424B5": "🔴",
    "8-K": "💀",
    "EFFECT": "⚠️",
    "RW": "🟢",
}


class DilutionScanner:
    """Download and parse SEC daily master index for dilution events."""

    BASE = "https://www.sec.gov/Archives/edgar/daily-index"

    def __init__(self) -> None:
        self.settings = get_settings()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.settings.sec_user_agent})

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=20), reraise=True)
    def _download_index(self, index_date: date) -> str:
        ymd = index_date.strftime("%Y%m%d")
        year = index_date.strftime("%Y")
        qtr = (index_date.month - 1) // 3 + 1
        url = f"{self.BASE}/{year}/QTR{qtr}/master.{ymd}.idx"
        logger.info("Downloading master index: %s", url)
        time.sleep(0.1)
        resp = self.session.get(url, timeout=60)
        if resp.status_code == 404:
            raise FileNotFoundError(f"No index for {index_date}")
        if resp.status_code == 403:
            raise PermissionError("SEC 403 — check SEC_USER_AGENT")
        if resp.status_code == 429:
            time.sleep(5)
            resp = self.session.get(url, timeout=60)
        resp.raise_for_status()
        return resp.text

    def parse_index(self, content: str) -> pd.DataFrame:
        """Parse master.idx into DataFrame with CIK, Company, Form, Date, File."""
        lines = content.splitlines()
        start = 0
        for i, line in enumerate(lines):
            if line.startswith("CIK|"):
                start = i + 1
                break
        records = []
        for line in lines[start:]:
            if not line.strip() or "|" not in line:
                continue
            parts = line.split("|")
            if len(parts) < 5:
                continue
            cik, company, form_type, filed, path = parts[0], parts[1], parts[2], parts[3], parts[4]
            records.append(
                {
                    "cik": cik.strip().lstrip("0") or "0",
                    "company_name": company.strip(),
                    "form_type": form_type.strip(),
                    "filed_date": filed.strip(),
                    "file_path": path.strip(),
                }
            )
        return pd.DataFrame(records)

    def filter_critical(self, df: pd.DataFrame) -> pd.DataFrame:
        """Keep only dilution-critical form types."""
        if df.empty:
            return df
        patterns = list(CRITICAL_FORMS.keys())
        mask = df["form_type"].isin(patterns)
        mask |= df["form_type"].str.startswith("S-3", na=False)
        mask |= df["form_type"].str.startswith("424B", na=False)
        return df[mask].copy()

    def scan_date(self, index_date: Optional[date] = None) -> List[CriticalFiling]:
        """Scan a single day's master index."""
        index_date = index_date or date.today()
        try:
            content = self._download_index(index_date)
        except FileNotFoundError:
            logger.warning("No index for %s (weekend/holiday?)", index_date)
            return []
        df = self.filter_critical(self.parse_index(content))
        results: List[CriticalFiling] = []
        for _, row in df.iterrows():
            emoji = CRITICAL_FORMS.get(row["form_type"], "🔴")
            filing_url = f"https://www.sec.gov/Archives/{row['file_path']}"
            try:
                filed = datetime.strptime(row["filed_date"], "%Y-%m-%d").date()
            except ValueError:
                filed = index_date
            results.append(
                CriticalFiling(
                    cik=str(row["cik"]),
                    company_name=row["company_name"],
                    form_type=row["form_type"],
                    filed_date=filed,
                    file_path=row["file_path"],
                    filing_url=filing_url,
                    alert_level=emoji,
                )
            )
        logger.info("Found %d critical filings on %s", len(results), index_date)
        return results

    def scan_range(self, days: int = 5) -> pd.DataFrame:
        """Scan last N business days, return combined DataFrame."""
        all_rows: List[dict] = []
        for i in range(days):
            d = date.today() - timedelta(days=i)
            if d.weekday() >= 5:
                continue
            for filing in self.scan_date(d):
                all_rows.append(filing.model_dump())
            time.sleep(0.1)
        return pd.DataFrame(all_rows)
