"""SEC HTML parser with keyword extraction for dilution signals."""

from __future__ import annotations

import logging
import re
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from config import get_settings

logger = logging.getLogger(__name__)


class SECRateLimitError(Exception):
    pass


class SECAccessError(Exception):
    pass


class ExtractionResult(BaseModel):
    """Structured keyword extraction from a filing."""

    has_atm: bool = False
    has_full_ratchet: bool = False
    has_prefunded_warrants: bool = False
    warrants_found: bool = False
    shelf_amount_usd: Optional[float] = None
    use_of_proceeds_text: Optional[str] = None
    dilution_text: Optional[str] = None
    matched_keywords: list[str] = Field(default_factory=list)


@dataclass
class ParsedFiling:
    url: str
    text: str
    form_type: Optional[str]
    accession_number: Optional[str]
    cik: Optional[str]
    title: Optional[str]
    extraction: ExtractionResult = field(default_factory=ExtractionResult)


class RateLimiter:
    def __init__(self, max_calls: int, period_seconds: float = 1.0) -> None:
        self.max_calls = max_calls
        self.period_seconds = period_seconds
        self._timestamps: deque[float] = deque()

    def wait(self) -> None:
        now = time.time()
        while self._timestamps and now - self._timestamps[0] >= self.period_seconds:
            self._timestamps.popleft()
        if len(self._timestamps) >= self.max_calls:
            time.sleep(self.period_seconds - (now - self._timestamps[0]) + 0.05)
        self._timestamps.append(time.time())
        time.sleep(0.1)


class SECParser:
    """Download, clean, and extract dilution signals from SEC HTML filings."""

    FORM_TYPES = {"S-3", "S-3/A", "424B5", "424B3", "10-Q", "10-K", "S-1", "8-K", "424B2", "EFFECT", "RW"}

    KEYWORD_PATTERNS = {
        "atm": re.compile(r"at[- ]the[- ]market\s+(?:offering|program|agreement)", re.I),
        "full_ratchet": re.compile(r"full\s+ratchet", re.I),
        "prefunded": re.compile(r"pre[- ]funded\s+warrant", re.I),
        "warrants": re.compile(r"\bwarrants?\b", re.I),
        "use_of_proceeds": re.compile(r"use\s+of\s+proceeds", re.I),
        "dilution": re.compile(r"\bdilution\b", re.I),
        "offering_amount": re.compile(
            r"aggregate\s+offering\s+price\s+of\s+up\s+to\s+\$?\s*([\d,]+(?:\.\d+)?)\s*(million|billion|M|B)?",
            re.I,
        ),
    }

    def __init__(self) -> None:
        self.settings = get_settings()
        self.rate_limiter = RateLimiter(self.settings.sec_rate_limit_per_sec)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": self.settings.sec_user_agent,
                "Accept-Encoding": "gzip, deflate",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
        )

    @staticmethod
    def extract_accession(url: str) -> Optional[str]:
        match = re.search(r"/(\d{10}-\d{2}-\d{6})/", url)
        if match:
            return match.group(1)
        match = re.search(r"accession[_-]?number=(\d{10}-\d{2}-\d{6})", url, re.I)
        return match.group(1) if match else None

    @staticmethod
    def extract_cik(url: str) -> Optional[str]:
        match = re.search(r"/(\d{10})/", url)
        if match:
            return match.group(1).lstrip("0") or "0"
        match = re.search(r"CIK=(\d+)", url, re.I)
        return match.group(1).lstrip("0") if match else None

    @retry(
        retry=retry_if_exception_type((requests.RequestException, SECRateLimitError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    def download(self, url: str) -> str:
        self.rate_limiter.wait()
        logger.info("Downloading: %s", url)
        response = self.session.get(url, timeout=60)
        if response.status_code == 429:
            raise SECRateLimitError("429 rate limit")
        if response.status_code == 403:
            raise SECAccessError("403 — check SEC_USER_AGENT")
        if response.status_code == 404:
            raise SECAccessError(f"404 not found: {url}")
        response.raise_for_status()
        return response.text

    def clean_html(self, html: str) -> str:
        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style", "noscript", "meta", "link", "head"]):
            tag.decompose()
        for tag in soup.find_all(True):
            if tag.name in {"td", "th", "tr", "p", "div", "br", "li", "h1", "h2", "h3"}:
                tag.append("\n")
        text = soup.get_text(separator=" ")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def extract_keywords(self, text: str) -> ExtractionResult:
        """Scan text for dilution-critical keywords."""
        result = ExtractionResult()
        if self.KEYWORD_PATTERNS["atm"].search(text):
            result.has_atm = True
            result.matched_keywords.append("ATM")
        if self.KEYWORD_PATTERNS["full_ratchet"].search(text):
            result.has_full_ratchet = True
            result.matched_keywords.append("Full Ratchet")
        if self.KEYWORD_PATTERNS["prefunded"].search(text):
            result.has_prefunded_warrants = True
            result.matched_keywords.append("Pre-Funded Warrants")
        if self.KEYWORD_PATTERNS["warrants"].search(text):
            result.warrants_found = True
            result.matched_keywords.append("Warrants")

        uop = self.KEYWORD_PATTERNS["use_of_proceeds"].search(text)
        if uop:
            start = max(0, uop.start() - 50)
            result.use_of_proceeds_text = text[start : uop.start() + 800]

        dil = self.KEYWORD_PATTERNS["dilution"].search(text)
        if dil:
            start = max(0, dil.start() - 50)
            result.dilution_text = text[start : dil.start() + 800]

        amt = self.KEYWORD_PATTERNS["offering_amount"].search(text)
        if amt:
            result.shelf_amount_usd = self._parse_amount(amt.group(1), amt.group(2))
            result.matched_keywords.append(f"Shelf ${result.shelf_amount_usd:,.0f}")

        return result

    @staticmethod
    def _parse_amount(num_str: str, unit: Optional[str]) -> float:
        amount = float(num_str.replace(",", ""))
        unit = (unit or "").lower()
        if unit in {"million", "m"}:
            amount *= 1_000_000
        elif unit in {"billion", "b"}:
            amount *= 1_000_000_000
        return amount

    def parse(self, url: str, html: Optional[str] = None) -> ParsedFiling:
        raw = html if html is not None else self.download(url)
        text = self.clean_html(raw)
        if len(text) < 100:
            raise ValueError(f"Text too short from {url}")
        extraction = self.extract_keywords(text)
        accession = self.extract_accession(url)
        cik = self.extract_cik(url)
        form_type = self._detect_form(text, url)
        title_match = re.search(r"(?i)(FORM\s+[0-9A-Z\-/]+)", text[:3000])
        title = title_match.group(1) if title_match else form_type
        return ParsedFiling(
            url=url,
            text=text,
            form_type=form_type,
            accession_number=accession,
            cik=cik,
            title=title,
            extraction=extraction,
        )

    def _detect_form(self, text: str, url: str) -> Optional[str]:
        for form in self.FORM_TYPES:
            if re.search(rf"\b{re.escape(form)}\b", text[:8000], re.I):
                return form
        path = urlparse(url).path.upper()
        for form in self.FORM_TYPES:
            if form.replace("-", "") in path.replace("-", ""):
                return form
        return None

    def load_from_url(self, url: str) -> ParsedFiling:
        return self.parse(url)


# Backward-compat alias
SECLoader = SECParser
