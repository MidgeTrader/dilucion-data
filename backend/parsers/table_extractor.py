"""SEC filing HTML table extractor — parses structured data from 424B, S-1, 8-K tables.

Extracts warrants, convertibles, ATMs, offerings, and equity lines
from standard SEC filing tables using BeautifulSoup.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

import requests
from bs4 import BeautifulSoup, Tag

from config import get_settings

logger = logging.getLogger(__name__)


class TableExtractor:
    """Download SEC filing HTML and extract structured tables."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.settings.sec_user_agent,
            "Accept": "text/html,application/xhtml+xml",
        })

    def fetch_html(self, url: str) -> str:
        resp = self.session.get(url, timeout=60)
        resp.raise_for_status()
        return resp.text

    def extract_tables(self, html: str, form_type: str = "") -> dict:
        """Extract all structured data from filing tables.

        Returns a dict with:
          warrants: list[dict]
          convertibles: list[dict]
          offerings: list[dict]
          atms: list[dict]
          shelf_amount: float | None
          equity_lines: list[dict]
        """
        soup = BeautifulSoup(html, "lxml")
        tables = soup.find_all("table")

        result = {
            "warrants": [],
            "convertibles": [],
            "offerings": [],
            "atms": [],
            "shelf_amount": None,
            "equity_lines": [],
        }

        for table in tables:
            table_text = table.get_text(" ", strip=True).lower()

            if not table_text or len(table_text) < 30:
                continue

            # Classify and extract by table type
            if self._is_warrant_table(table_text):
                extracted = self._parse_warrant_table(table)
                result["warrants"].extend(extracted)

            elif self._is_convertible_table(table_text):
                extracted = self._parse_convertible_table(table)
                result["convertibles"].extend(extracted)

            elif self._is_offering_table(table_text):
                extracted = self._parse_offering_table(table)
                result["offerings"].extend(extracted)

            elif self._is_shelf_table(table_text):
                amt = self._parse_shelf_amount(table)
                if amt:
                    result["shelf_amount"] = amt

        # Also scan text for equity lines
        full_text = soup.get_text(" ", strip=True)
        if re.search(r"equity\s+line|lincoln\s+park|committed\s+equity|purchase\s+agreement", full_text, re.I):
            result["equity_lines"] = self._extract_equity_lines(full_text)

        return result

    # ─── Table classifiers ───────────────────────────────────────────────

    def _is_warrant_table(self, text: str) -> bool:
        """Check if table contains warrant data."""
        keywords = ["warrant", "exercise price", "expiration"]
        return sum(1 for k in keywords if k in text) >= 2

    def _is_convertible_table(self, text: str) -> bool:
        keywords = ["convertible", "conversion price", "principal", "interest", "note", "maturity"]
        return sum(1 for k in keywords if k in text) >= 3

    def _is_offering_table(self, text: str) -> bool:
        keywords = [
            "shares", "offering", "price", "common stock",
            "underwriting", "discount", "commission", "proceeds",
        ]
        return sum(1 for k in keywords if k in text) >= 3

    def _is_shelf_table(self, text: str) -> bool:
        keywords = ["shelf", "registration", "offering price", "aggregate"]
        return sum(1 for k in keywords if k in text) >= 2

    # ─── Table parsers ───────────────────────────────────────────────────

    def _rows_to_text(self, table: Tag) -> list[list[str]]:
        """Convert HTML table rows to list of text cells."""
        rows = []
        for tr in table.find_all("tr"):
            cells = [td.get_text(" ", strip=True) for td in tr.find_all(["td", "th"])]
            cells = [c for c in cells if c]
            if cells:
                rows.append(cells)
        return rows

    def _find_adjacent_amount(self, text: str, direction: str = "after", max_chars: int = 200) -> Optional[float]:
        """Find a USD amount near a position in text."""
        # Try common patterns
        patterns = [
            r"\$\s*([\d,]+(?:\.\d+)?)\s*(million|M|billion|B|thousand|K)?",
            r"([\d,]+(?:\.\d+)?)\s*(million|M|billion|B)\s*dollars?",
        ]
        for pat in patterns:
            for m in re.finditer(pat, text, re.I):
                val = float(m.group(1).replace(",", ""))
                unit = (m.group(2) or "").lower() if m.lastindex >= 2 else ""
                if unit in ("million", "m"):
                    val *= 1_000_000
                elif unit in ("billion", "b"):
                    val *= 1_000_000_000
                elif unit in ("thousand", "k"):
                    val *= 1_000
                if val >= 100:  # not a par value
                    return val
        return None

    def _parse_warrant_table(self, table: Tag) -> list[dict]:
        """Extract warrant issues from a table."""
        rows = self._rows_to_text(table)
        warrants = []
        header_idx = self._find_header_row(rows, ["warrant", "exercise", "expiration"])

        for i, row in enumerate(rows):
            if i <= header_idx:
                continue
            row_text = " ".join(row).lower()
            if "total" in row_text or not re.search(r"\d", row_text):
                continue

            w = self._row_to_warrant(row, rows[max(0, i-1)])
            if w and w.get("count") and w["count"] > 0:
                warrants.append(w)

        return warrants

    def _row_to_warrant(self, row: list[str], prev_row: list[str]) -> dict:
        """Parse a single warrant row."""
        text = " ".join(row)
        prev_text = " ".join(prev_row)
        combined = prev_text + " " + text

        # Try to extract date/issue label
        issue = None
        for pat in [
            r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[.\s]*\d{4}",
            r"Series\s+[A-Z]",
            r"(?:pre[-\s]funded|common)\s+warrant",
        ]:
            m = re.search(pat, combined, re.I)
            if m:
                issue = m.group(0)
                break

        # Count: look for numbers near "warrant" or standalone share counts
        count = None
        for cell in row:
            cell_clean = cell.replace(",", "").replace("$", "")
            cm = re.match(r"^([\d]+(?:\s*[\d]{3})*(?:\.\d+)?)\s*(million|M|billion|B)?$", cell_clean, re.I)
            if cm:
                val = float(cm.group(1))
                unit = (cm.group(2) or "").lower()
                if unit in ("million", "m"):
                    val *= 1_000_000
                if val > 1000 and val < 1e12:
                    count = val
                    break

        if not count:
            cm = re.search(r"([\d,]+(?:\.\d+)?)\s*(?:shares?|warrants?)", combined, re.I)
            if cm:
                count = float(cm.group(1).replace(",", ""))

        # Exercise price
        exercise_price = None
        em = re.search(r"\$\s*([\d,]+(?:\.\d+)?)", combined)
        if em:
            val = float(em.group(1).replace(",", ""))
            if 0.01 <= val <= 1000:
                exercise_price = val

        # Protection
        protection = "Customary Anti-Dilution"
        if "full ratchet" in combined:
            protection = "Full Ratchet"

        # Owners
        owners = []
        for inv in ["Armistice", "Sabby", "3i", "Alto", "Intracoastal", "Vellar", "Maxim", "Lincoln Park"]:
            if inv.lower() in combined:
                owners.append(inv)

        return {
            "issue_label": issue or "Warrants",
            "remaining": count,
            "exercise_price": exercise_price,
            "owners": list(set(owners)),
            "protection": protection,
        }

    def _parse_convertible_table(self, table: Tag) -> list[dict]:
        """Extract convertible notes from a table."""
        rows = self._rows_to_text(table)
        converts = []
        header_idx = self._find_header_row(rows, ["principal", "conversion", "interest", "maturity"])

        for i, row in enumerate(rows):
            if i <= header_idx:
                continue
            text = " ".join(row).lower()
            if "total" in text or not re.search(r"\$", text):
                continue

            c = self._row_to_convertible(row, text)
            if c and c.get("total") and c["total"] > 0:
                converts.append(c)

        return converts

    def _row_to_convertible(self, row: list[str], text: str) -> dict:
        total = None
        for cell in row:
            m = re.search(r"\$?\s*([\d,]+(?:\.\d+)?)\s*(million|M|billion|B)?", cell, re.I)
            if m:
                val = float(m.group(1).replace(",", ""))
                unit = (m.group(2) or "").lower()
                if unit in ("million", "m"):
                    val *= 1_000_000
                if val > 1000:
                    total = val
                    break

        cv_price = None
        cm = re.search(r"(?:conversion|convertible)\s+price[^.]*?\$\s*([\d,]+(?:\.\d+)?)", text, re.I)
        if cm:
            cv_price = float(cm.group(1).replace(",", ""))

        protection = "Full Ratchet" if "full ratchet" in text else "N/A"
        owner = "3i, LP" if "3i" in text else None

        return {
            "issue_label": "Convertible Note",
            "total": total,
            "conversion_price": cv_price,
            "protection": protection,
            "owner": owner,
        }

    def _parse_offering_table(self, table: Tag) -> list[dict]:
        """Extract offering details from prospectus supplement tables."""
        rows = self._rows_to_text(table)
        header_idx = self._find_header_row(rows, [
            "share", "offering", "price", "common", "per share",
        ])
        if header_idx < 0:
            return []

        offerings = []
        for i, row in enumerate(rows):
            if i <= header_idx:
                continue
            text = " ".join(row)
            text_lower = text.lower()
            if "total" in text_lower:
                continue

            offering = {
                "type": self._classify_offering(text),
                "shares": None,
                "price": None,
                "amount": None,
                "warrants": None,
                "bank": None,
            }

            for cell in row:
                cm = re.match(r"^([\d,]+(?:\.\d+)?)\s*(million|M|billion|B)?$", cell.strip(), re.I)
                if cm:
                    val = float(cm.group(1).replace(",", ""))
                    unit = (cm.group(2) or "").lower()
                    if unit in ("million", "m"): val *= 1_000_000
                    if val > 1e12: continue
                    if val > 1000 and val < 1e9:
                        if "$" not in cell:
                            offering["shares"] = val
                        else:
                            offering["amount"] = val
                    elif val >= 1e9:
                        offering["amount"] = val

                dm = re.search(r"\$\s*([\d,]+(?:\.\d+)?)", cell)
                if dm:
                    val2 = float(dm.group(1).replace(",", ""))
                    if val2 <= 1000:
                        offering["price"] = val2

            for bank in ["H.C. Wainwright", "Maxim Group", "Armistice", "Lincoln Park", "HC Wainwright"]:
                if bank.lower() in text_lower:
                    offering["bank"] = "H.C. Wainwright" if "wainwright" in text_lower else bank
                    break

            if any(v is not None for v in [offering["shares"], offering["amount"]]):
                offerings.append(offering)

        return offerings

    def _find_header_row(self, rows: list[list[str]], keywords: list[str]) -> int:
        """Find the header row index containing most keywords."""
        best, best_idx = 0, -1
        for i, row in enumerate(rows[:8]):
            text = " ".join(row).lower()
            score = sum(1 for k in keywords if k in text)
            if score > best:
                best = score
                best_idx = i
        return best_idx if best >= 2 else -1

    def _classify_offering(self, text: str) -> str:
        text_l = text.lower()
        if "atm" in text_l or "at-the-market" in text_l:
            return "ATM"
        if "registered direct" in text_l:
            return "REGISTERED DIRECT"
        if "best efforts" in text_l:
            return "BEST EFFORTS"
        if "firm commitment" in text_l:
            return "FIRM COMMITMENT"
        if "private placement" in text_l:
            return "PRIVATE PLACEMENT"
        if "public offering" in text_l:
            return "PUBLIC OFFERING"
        return "REGISTERED OFFERING"

    def _parse_shelf_amount(self, table: Tag) -> Optional[float]:
        """Extract shelf registration amount from S-3 tables."""
        text = table.get_text(" ", strip=True).lower()
        m = re.search(
            r"\$\s*([\d,]+(?:\.\d+)?)\s*(million|M|billion|B)?",
            text, re.I
        )
        if m:
            val = float(m.group(1).replace(",", ""))
            unit = (m.group(2) or "").lower()
            if unit in ("million", "m"):
                val *= 1_000_000
            elif unit in ("billion", "b"):
                val *= 1_000_000_000
            return val
        return None

    def _extract_equity_lines(self, text: str) -> list[dict]:
        """Extract equity line details from filing text."""
        lines = []
        m = re.search(r"\$\s*([\d,]+(?:\.\d+)?)\s*(million|M|billion|B)?\s*(?:common\s+stock\s+)?purchase\s+agreement", text, re.I)
        if m:
            val = float(m.group(1).replace(",", ""))
            unit = (m.group(2) or "").lower()
            if val >= 1_000:
                if unit in ("million", "m"):
                    val *= 1_000_000
                lines.append({"total_amt": val})
        return lines

    def fetch_and_extract(self, url: str, form_type: str = "") -> dict:
        """Fetch filing HTML and extract all structured tables."""
        try:
            html = self.fetch_html(url)
            return self.extract_tables(html, form_type)
        except Exception as exc:
            logger.warning("Table extraction failed for %s: %s", url, exc)
            return {"warrants": [], "convertibles": [], "offerings": [],
                    "atms": [], "shelf_amount": None, "equity_lines": []}
