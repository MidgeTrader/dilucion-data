"""SEC HTML parser with keyword extraction for dilution signals."""

from __future__ import annotations

import logging
import re
import warnings
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from pydantic import BaseModel, Field
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from apis._rate_limit import RateLimiter
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
    is_shelf_takedown: bool = False
    is_rights_offering: bool = False
    is_overnight_offering: bool = False
    is_block_trade: bool = False
    is_secondary_offering: bool = False
    is_primary_offering: bool = False
    is_best_efforts: bool = False
    is_firm_commitment: bool = False
    is_global_offering: bool = False
    is_continuous_offering: bool = False
    is_spot_offering: bool = False
    is_warrant_offering: bool = False
    shelf_amount_usd: Optional[float] = None
    use_of_proceeds_text: Optional[str] = None
    dilution_text: Optional[str] = None
    matched_keywords: list[str] = Field(default_factory=list)
    warrants_detail: list[dict] = Field(default_factory=list)


@dataclass
class ParsedFiling:
    url: str
    text: str
    form_type: Optional[str]
    accession_number: Optional[str]
    cik: Optional[str]
    title: Optional[str]
    extraction: ExtractionResult = field(default_factory=ExtractionResult)


class SECParser:
    """Download, clean, and extract dilution signals from SEC HTML filings."""

    FORM_TYPES = {"S-3", "S-3/A", "424B2", "424B3", "424B4", "424B5", "10-Q", "10-K", "S-1", "8-K", "EFFECT", "RW"}

    KEYWORD_PATTERNS = {
        "atm": re.compile(r"at[- ]the[- ]market\s+(?:offering|program|agreement)", re.I),
        "full_ratchet": re.compile(r"full\s+ratchet", re.I),
        "prefunded": re.compile(r"pre[- ]funded\s+warrant", re.I),
        "warrants": re.compile(r"\bwarrants?\b", re.I),
        "use_of_proceeds": re.compile(r"use\s+of\s+proceeds", re.I),
        "dilution": re.compile(r"\bdilution\b", re.I),
        "offering_amount": re.compile(
            r"(?:aggregate\s+)?offering\s+(?:price|amount|of)\s+(?:of\s+)?(?:up\s+to\s+)?\$?\s*([\d,]+(?:\.\d+)?)\s*(million|billion|M|B)?",
            re.I,
        ),
        "direct_offering": re.compile(
            r"(?:registered\s+)?direct\s+offering\s+(?:of\s+)?\$?\s*([\d,]+(?:\.\d+)?)\s*(million|billion|M|B)?",
            re.I,
        ),
        "private_placement": re.compile(
            r"(?:private\s+)?placement\s+(?:financing\s+)?(?:of\s+)?\$?\s*([\d,]+(?:\.\d+)?)\s*(million|billion|M|B)?",
            re.I,
        ),
        "purchase_agreement": re.compile(
            r"(?:securities\s+)?purchase\s+agreement\s+(?:for\s+)?\$?\s*([\d,]+(?:\.\d+)?)\s*(million|billion|M|B)?",
            re.I,
        ),
        "gross_proceeds": re.compile(
            r"gross\s+proceeds.*?\$\s*([\d,]+(?:\.\d+)?)\s*(million|billion|M|B)",
            re.I,
        ),
        "public_offering": re.compile(
            r"(?:underwritten\s+)?public\s+offering\s+(?:of\s+)?\$?\s*([\d,]+(?:\.\d+)?)\s*(million|billion|M|B)?",
            re.I,
        ),
        "shelf_registration": re.compile(
            r"shelf\s+(?:registration\s+)?(?:of\s+)?(?:up\s+to\s+)?\$?\s*([\d,]+(?:\.\d+)?)\s*(million|billion|M|B)?",
            re.I,
        ),
        "proposed_offering": re.compile(
            r"proposed\s+(?:public\s+)?offering\s+(?:of\s+)?\$?\s*([\d,]+(?:\.\d+)?)\s*(million|billion|M|B)?",
            re.I,
        ),
        "sale_of_stock": re.compile(
            r"(?:sell|sale)\s+(?:of\s+)?(?:up\s+to\s+)?\$?\s*([\d,]+(?:\.\d+)?)\s*(million|billion|M|B)?\s+(?:of\s+)?(?:common\s+)?stock",
            re.I,
        ),
        "raise_capital": re.compile(
            r"raise\s+(?:approximately\s+)?(?:up\s+to\s+)?\$?\s*([\d,]+(?:\.\d+)?)\s*(million|billion|M|B)?",
            re.I,
        ),
        "atm_offering": re.compile(
            r"at[-\s]the[-\s]market.*?(?:aggregate\s+)?offering\s+price.*?(?:up\s+to\s+)?\$?\s*([\d,]+(?:\.\d+)?)\s*(million|billion|M|B)?",
            re.I,
        ),
        # Offering type classifiers
        "shelf_takedown": re.compile(r"shelf\s+(?:offering|take[-\s]down|takedown)", re.I),
        "rights_offering": re.compile(r"rights\s+offering", re.I),
        "overnight_offering": re.compile(r"overnight\s+offering", re.I),
        "block_trade": re.compile(r"block\s+trade", re.I),
        "secondary_offering": re.compile(r"secondary\s+offering", re.I),
        "primary_offering": re.compile(r"primary\s+offering", re.I),
        "best_efforts": re.compile(r"best\s+efforts\s+offering", re.I),
        "firm_commitment": re.compile(r"firm\s+commitment\s+offering", re.I),
        "global_offering": re.compile(r"global\s+offering", re.I),
        "continuous_offering": re.compile(r"continuous\s+offering", re.I),
        "spot_offering": re.compile(r"spot\s+offering", re.I),
        "warrant_offering": re.compile(r"(?:registered\s+)?warrant\s+offering", re.I),
        # Warrant detail extraction
        "warrant_type": re.compile(
            r"(?:(?:series\s+)?([A-Z])|common|pre[- ]funded)\s+warrants?\b",
            re.I,
        ),
        "warrant_count": re.compile(
            r"(?:warrants?\s+(?:to\s+)?purchase\s+)?(?:up\s+to\s+)?([\d,]+(?:\s*million|\s*billion)?)\s+(?:shares\s+of\s+)?(?:common\s+stock\s+)?underlying\s+(?:the\s+)?warrants?",
            re.I,
        ),
        "warrant_exercise_price": re.compile(
            r"(?:exercise\s+)?price\s+(?:equal\s+to\s+|of\s+|per\s+(?:warrant\s+)?share\s+)?\$?\s*([\d,]+(?:\.\d+)?)",
            re.I,
        ),
        "warrant_expiration": re.compile(
            r"(?:will\s+)?expir(?:e|ation)\s+(?:on\s+)?(\w+(?:\s+\w+)?\s+\d{1,2},?\s+\d{4}|\d+\s+(?:years?|months?)\s+(?:from\s+(?:the\s+)?(?:issuance\s+)?date|after\s+(?:the\s+)?(?:effective\s+)?date))",
            re.I,
        ),
    }

    def __init__(self) -> None:
        self.settings = get_settings()
        # period=1.0: el setting es por SEGUNDO (SEC permite 10 req/s).
        # Sin esto, RateLimiter usaba period=60s → 10 req/min y cada
        # batch de >10 descargas se congelaba ~50-60s.
        self.rate_limiter = RateLimiter(self.settings.sec_rate_limit_per_sec, period=1.0)
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
        warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
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

        # Offering type classifiers
        offering_types = [
            ("shelf_takedown", "is_shelf_takedown", "Shelf Takedown"),
            ("rights_offering", "is_rights_offering", "Rights Offering"),
            ("overnight_offering", "is_overnight_offering", "Overnight Offering"),
            ("block_trade", "is_block_trade", "Block Trade"),
            ("secondary_offering", "is_secondary_offering", "Secondary Offering"),
            ("primary_offering", "is_primary_offering", "Primary Offering"),
            ("best_efforts", "is_best_efforts", "Best Efforts"),
            ("firm_commitment", "is_firm_commitment", "Firm Commitment"),
            ("global_offering", "is_global_offering", "Global Offering"),
            ("continuous_offering", "is_continuous_offering", "Continuous Offering"),
            ("spot_offering", "is_spot_offering", "Spot Offering"),
            ("warrant_offering", "is_warrant_offering", "Warrant Offering"),
        ]
        for pattern_key, flag_attr, label in offering_types:
            pattern = self.KEYWORD_PATTERNS.get(pattern_key)
            if pattern and pattern.search(text):
                setattr(result, flag_attr, True)
                result.matched_keywords.append(label)

        uop = self.KEYWORD_PATTERNS["use_of_proceeds"].search(text)
        if uop:
            start = max(0, uop.start() - 50)
            result.use_of_proceeds_text = text[start : uop.start() + 800]

        dil = self.KEYWORD_PATTERNS["dilution"].search(text)
        if dil:
            start = max(0, dil.start() - 50)
            result.dilution_text = text[start : dil.start() + 800]

        # Try all offering patterns, pick the largest valid amount
        best_amount = None
        for pattern_name in ("offering_amount", "direct_offering", "private_placement", "purchase_agreement", "gross_proceeds", "public_offering", "shelf_registration", "proposed_offering", "sale_of_stock", "raise_capital", "atm_offering"):
            pattern = self.KEYWORD_PATTERNS.get(pattern_name)
            if not pattern:
                continue
            for match in pattern.finditer(text):
                raw = match.group(1)
                unit = match.group(2) if match.lastindex and match.lastindex >= 2 else None
                if raw:
                    amount = self._parse_amount(raw, unit)
                    # Skip par values (stock par value is always < $1, typically $0.0001 or $0.001)
                    if amount is not None and amount >= 1_000:
                        if best_amount is None or amount > best_amount:
                            best_amount = amount
        if best_amount:
            result.shelf_amount_usd = best_amount
            result.matched_keywords.append(f"Shelf ${best_amount:,.0f}")

        # Warrant detail extraction — extract each distinct warrant type with its terms
        if result.warrants_found or result.has_prefunded_warrants:
            text_lower = text.lower()
            # Find all warrant "blocks" by scanning for "warrant" mentions
            # Each block starts with a number followed by "series X warrants" or "pre-funded warrants"
            blocks = re.finditer(
                r"([\d,]+)\s+(series\s+([a-z])\s+|pre[- ]funded\s+)?warrants?\s+to\s+purchase\s+(?:up\s+to\s+)?([\d,]+)",
                text_lower,
            )
            seen_types = set()
            for b in blocks:
                is_prefunded = "pre-funded" in b.group(0) or "prefunded" in b.group(0)
                series_letter = b.group(3).upper() if b.group(3) else None
                wtype = "Pre-Funded" if is_prefunded else (f"Series {series_letter}" if series_letter else "Common")
                if wtype in seen_types:
                    continue
                seen_types.add(wtype)
                # Count
                raw_count = b.group(4).replace(",", "") if b.group(4) else None
                wcount = float(raw_count) if raw_count else None
                # Find exercise price near this block (within 500 chars after)
                block_end = b.end()
                nearby = text_lower[block_end:block_end + 1000]
                wprice = None
                pm = re.search(r"exercise\s+price\s+(?:of\s+)?\$?\s*([\d,]+(?:\.\d+)?)", nearby)
                if pm:
                    try:
                        wprice = float(pm.group(1).replace(",", ""))
                    except ValueError:
                        pass
                # Expiration
                wexp = None
                em = re.search(r"expir(?:e|ation)\s+(?:on\s+)?(.{5,30}?(?:years?|months?|days?)\s+(?:from|after|following))", nearby)
                if em:
                    wexp = em.group(1).strip()
                result.warrants_detail.append({
                    "type": wtype,
                    "count": wcount,
                    "exercise_price": wprice,
                    "expiration": wexp or "See filing",
                })
            # Also check for standalone warrant price mentions (common pre-funded)
            if "pre-funded" in text_lower and "Pre-Funded" not in seen_types:
                pm = re.search(r"pre[- ]funded\s+warrants?.*?exercise\s+price\s+(?:of\s+)?\$?\s*([\d,]+(?:\.\d+)?)", text_lower)
                if pm:
                    wprice = float(pm.group(1).replace(",", ""))
                    result.warrants_detail.append({
                        "type": "Pre-Funded", "count": None,
                        "exercise_price": wprice, "expiration": "Never (pre-funded)",
                    })

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
