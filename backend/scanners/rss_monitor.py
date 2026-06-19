"""Real-time SEC EDGAR RSS/Atom feed monitor."""

from __future__ import annotations

import logging
import sqlite3
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, List, Optional, Set

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from config import get_settings
from models import CriticalFiling, RSSAlert

logger = logging.getLogger(__name__)

RSS_URL = (
    "https://www.sec.gov/cgi-bin/browse-edgar"
    "?action=getcurrent&type=&company=&dateb=&owner=include&start=0&count=100&output=atom"
)

CRITICAL_FORMS = {"S-3", "S-3/A", "424B3", "424B5", "424B2", "8-K", "EFFECT", "RW", "S-1", "S-1/A"}
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


class RSSMonitor:
    """Poll SEC Atom feed and alert on critical dilution filings."""

    def __init__(self, dedup_db: Optional[Path] = None) -> None:
        self.settings = get_settings()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.settings.sec_user_agent})
        self.dedup_db = dedup_db or (self.settings.data_dir / "rss_seen.sqlite")
        self._init_dedup_db()

    def _init_dedup_db(self) -> None:
        self.dedup_db.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.dedup_db) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS seen (accession TEXT PRIMARY KEY, seen_at TEXT)"
            )
            conn.commit()

    def _is_seen(self, accession: str) -> bool:
        with sqlite3.connect(self.dedup_db) as conn:
            row = conn.execute("SELECT 1 FROM seen WHERE accession=?", (accession,)).fetchone()
            return row is not None

    def _mark_seen(self, accession: str) -> None:
        with sqlite3.connect(self.dedup_db) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO seen (accession, seen_at) VALUES (?, ?)",
                (accession, datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=15), reraise=True)
    def fetch_feed(self) -> str:
        time.sleep(0.1)
        resp = self.session.get(RSS_URL, timeout=30)
        resp.raise_for_status()
        return resp.text

    def parse_feed(self, xml_content: str) -> List[RSSAlert]:
        """Parse Atom feed entries into RSSAlert objects."""
        root = ET.fromstring(xml_content)
        alerts: List[RSSAlert] = []
        for entry in root.findall("atom:entry", ATOM_NS):
            title = entry.findtext("atom:title", default="", namespaces=ATOM_NS)
            link_el = entry.find("atom:link", ATOM_NS)
            link = link_el.get("href", "") if link_el is not None else ""
            updated = entry.findtext("atom:updated", default="", namespaces=ATOM_NS)
            summary = entry.findtext("atom:summary", default="", namespaces=ATOM_NS)

            form_type = self._extract_form_type(title)
            if form_type not in CRITICAL_FORMS and not form_type.startswith("S-3") and not form_type.startswith("424B"):
                continue

            accession = self._extract_accession(link) or self._extract_accession(title) or link
            if self._is_seen(accession):
                continue

            cik = self._extract_cik(link) or ""
            company = title.split(" - ")[0] if " - " in title else title[:80]
            alerts.append(
                RSSAlert(
                    accession_number=accession,
                    cik=cik,
                    company_name=company,
                    form_type=form_type,
                    filing_url=link,
                    summary=summary[:500] if summary else None,
                    detected_at=datetime.now(timezone.utc),
                )
            )
        return alerts

    @staticmethod
    def _extract_form_type(title: str) -> str:
        for form in sorted(CRITICAL_FORMS, key=len, reverse=True):
            if form in title:
                return form
        parts = title.split(" - ")
        if len(parts) > 1:
            return parts[1].split()[0].strip()
        return "UNKNOWN"

    @staticmethod
    def _extract_accession(text: str) -> Optional[str]:
        import re
        m = re.search(r"(\d{10}-\d{2}-\d{6})", text)
        return m.group(1) if m else None

    @staticmethod
    def _extract_cik(url: str) -> Optional[str]:
        import re
        m = re.search(r"/data/(\d+)/", url)
        if m:
            return m.group(1).lstrip("0") or "0"
        return None

    def poll_once(self) -> List[RSSAlert]:
        """Single poll cycle — returns new alerts only."""
        xml = self.fetch_feed()
        alerts = self.parse_feed(xml)
        for alert in alerts:
            self._mark_seen(alert.accession_number)
        return alerts

    def run_daemon(
        self,
        interval_seconds: int = 120,
        on_alert: Optional[Callable[[RSSAlert], None]] = None,
    ) -> None:
        """Continuously poll RSS feed."""
        logger.info("RSS monitor started (interval=%ds)", interval_seconds)
        while True:
            try:
                alerts = self.poll_once()
                for alert in alerts:
                    logger.warning(
                        "🚨 NEW FILING: %s %s %s — %s",
                        alert.form_type,
                        alert.company_name,
                        alert.cik,
                        alert.filing_url,
                    )
                    if on_alert:
                        on_alert(alert)
            except Exception as exc:
                logger.error("RSS poll error: %s", exc)
            time.sleep(interval_seconds)
