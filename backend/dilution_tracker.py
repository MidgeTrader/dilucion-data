"""Dilution Tracker — comprehensive dilution analysis from SEC filings.

Extraction priority:
  1. Seed data (manually curated)
  2. RAG extraction (OpenAI embeddings -> DeepSeek -> structured JSON)
  3. Regex text extraction (fallback)
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import sqlite3
from typing import Optional

from config import get_settings
from models import (
    DilutionTrackerData, CashPosition, ShelfRegistration, ATMProgram, WarrantIssue, ConvertibleIssue,
    EquityLine, CompletedOffering, LockUpAgreement,
    NasdaqComplianceItem, ReverseSplit, Company, SECFilingMeta, PendingDilutionEvent,
)
from parsers.sec_parser import SECParser, ParsedFiling
from scanners.company_facts import CompanyFactsClient

logger = logging.getLogger(__name__)

KNOWN_INVESTORS = ["Armistice", "3i", "LP", "Sabby", "Intracoastal", "Alto", "Maxim", "H.C. Wainwright", "Lincoln Park", "Vellar", "HB Strategies", "Tumim Stone"]


class DilutionTrackerService:
    """Build a comprehensive DilutionTrackerData from SEC filings.

    Combines manual seed data, RAG extraction (LLM), and regex fallback
    to analyze a company's dilution profile including shelf registrations,
    ATM programs, warrants, convertibles, equity lines, and cash position.
    """

    _SEED_REGISTRY: dict[str, DilutionTrackerData] = {}

    @classmethod
    def _load_seeds(cls) -> dict[str, DilutionTrackerData]:
        if cls._SEED_REGISTRY:
            return cls._SEED_REGISTRY
        try:
            from seed_data.buru_dilution import BURU_SEED
            cls._SEED_REGISTRY[BURU_SEED.ticker] = BURU_SEED
            logger.info("Loaded seed: %s", BURU_SEED.ticker)
        except Exception as exc:
            logger.warning("BURU seed unavailable: %s", exc)
        try:
            from seed_data.slnd_dilution import SLND_SEED
            cls._SEED_REGISTRY[SLND_SEED.ticker] = SLND_SEED
            logger.info("Loaded seed: %s", SLND_SEED.ticker)
        except Exception as exc:
            logger.warning("SLND seed unavailable: %s", exc)
        return cls._SEED_REGISTRY

    def __init__(self) -> None:
        self.settings = get_settings()
        self.facts = CompanyFactsClient()
        self.parser = SECParser()
        self._seeds = self._load_seeds()
        self._rag = None
        self._parsed_cache: dict[str, ParsedFiling] = {}

    @property
    def _rag_extractor(self):
        if self._rag is None:
            try:
                from dilution_rag import DilutionRAGExtractor
                self._rag = DilutionRAGExtractor()
            except Exception as exc:
                logger.warning("RAG extractor unavailable: %s", exc)
                self._rag = False
        return self._rag if self._rag else None

    def _get_parsed(self, url: str) -> Optional[ParsedFiling]:
        if url in self._parsed_cache:
            return self._parsed_cache[url]
        try:
            pf = self.parser.load_from_url(url)
            self._parsed_cache[url] = pf
            return pf
        except Exception as exc:
            logger.debug("Parse failed %s: %s", url, exc)
            return None

    def _filing_texts(self, urls: list) -> str:
        texts = []
        for u in urls:
            pf = self._get_parsed(u)
            if pf:
                texts.append(pf.text[:50000])
        return "\n\n".join(texts)

    def _get_filing_urls(self, cik: str, form_filter: list[str], limit: int = 10) -> list:
        """Query SEC submissions API for filings matching specific form types.

        Iterates up to 800 entries to find older filings beyond the default limit.

        Args:
            cik: SEC CIK number.
            form_filter: List of form types to match (e.g. ["S-3", "S-3/A"]).
            limit: Max results to return.

        Returns:
            List of SECFilingMeta matching the filter.
        """
        data = self.facts.get_submissions(cik)
        if not data:
            return []
        recent = data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        dates = recent.get("filingDate", [])
        accessions = recent.get("accessionNumber", [])
        docs = recent.get("primaryDocument", [])
        results = []
        for i in range(min(len(forms), 800)):
            form = forms[i]
            for ft in form_filter:
                if form == ft or form.startswith(ft.replace("*", "")):
                    acc_raw = accessions[i]
                    accession = acc_raw.replace("-", "")
                    primary = docs[i] if i < len(docs) else ""
                    url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{primary}"
                    results.append(SECFilingMeta(accession_number=acc_raw, form_type=form, filed_date=dates[i], url=url))
                    break
            if len(results) >= limit:
                break
        return results

    def _rag_batch(self, method: str, meta_list: list, model_class) -> list:
        """Run RAG extraction on a batch of SEC filings.

        Checks SQLite extraction_cache before downloading to avoid re-processing
        already analyzed filings.

        Args:
            method: Name of the RAG extraction method (e.g. "extract_warrants").
            meta_list: List of SECFilingMeta to process.
            model_class: Pydantic model class for the result type.

        Returns:
            List of extracted model instances (may be empty).
        """
        rag = self._rag_extractor
        if not rag or not meta_list:
            return []
        method_name = method.replace("extract_", "")
        cache_path = str(self.settings.data_dir / "extraction_cache.sqlite")
        results = []
        for m in meta_list:
            url_str = str(m.url)
            key = hashlib.sha256(f"{url_str}:{method_name}".encode()).hexdigest()[:32]
            cached = None
            try:
                with sqlite3.connect(cache_path, timeout=5) as conn:
                    row = conn.execute(
                        "SELECT result_json FROM extraction_cache WHERE url_hash=? AND extraction_type=?",
                        (key, method_name)
                    ).fetchone()
                    if row:
                        cached = json.loads(row[0])
            except Exception:
                pass
            if cached is not None:
                if cached:
                    results.extend(cached)
                continue
            parsed = self._get_parsed(url_str)
            if parsed:
                try:
                    fn = getattr(rag, method, None)
                    if fn:
                        items = fn(parsed)
                        if items:
                            results.extend(items)
                except Exception:
                    continue
        return [model_class(**r) for r in results] if results else []

    def _check_cache_freshness(self, cik: str, ticker: str) -> None:
        """Check if new SEC filings exist since the last extraction cache check.

        Compares the latest filing date from the SEC submissions API against
        the stored last-checked timestamp. If new filings arrived, downstream
        RAG extraction will process them (cache miss on new URLs).

        Args:
            cik: SEC CIK number.
            ticker: Ticker symbol for logging/cache keys.
        """
        try:
            data = self.facts.get_submissions(cik)
            if not data:
                return
            recent = data.get("filings", {}).get("recent", {})
            dates = recent.get("filingDate", [])
            latest_filing_date = dates[0] if dates else ""
            cache_path = str(self.settings.data_dir / "extraction_cache.sqlite")
            conn = sqlite3.connect(cache_path)
            row = conn.execute(
                "SELECT created_at FROM extraction_cache WHERE extraction_type=? ORDER BY created_at DESC LIMIT 1",
                (f"last_checked_{ticker}",)
            ).fetchone()
            last_check = row[0] if row else ""
            if last_check and latest_filing_date > last_check[:10]:
                logger.info("New filings for %s (latest: %s) since %s", ticker, latest_filing_date, last_check[:10])
            from datetime import datetime as dt
            conn.execute("INSERT OR REPLACE INTO extraction_cache (url_hash, extraction_type, result_json, model, created_at) VALUES (?,?,?,?,?)",
                         (f"ticker_{ticker}", f"last_checked_{ticker}", "{}", "", dt.utcnow().isoformat()))
            conn.commit()
            conn.close()
        except Exception as exc:
            logger.debug("Cache check: %s", exc)

    def get_dilution_data(self, ticker: str, company: Optional[Company] = None, filings: Optional[list] = None, price: Optional[float] = None) -> DilutionTrackerData:
        """Build a complete dilution profile for a ticker.

        Combines SEC filings, RAG extraction, seed data, and regex fallbacks
        to produce a comprehensive DilutionTrackerData with cash position,
        shelf registrations, ATMs, warrants, convertibles, equity lines,
        completed offerings, compliance status, and pending events.

        Args:
            ticker: Ticker symbol to analyze.
            company: Optional Company record for cached data.
            filings: Optional list of FilingDilution for offering history.
            price: Current stock price for dilution calculations.

        Returns:
            Fully populated DilutionTrackerData (seed data takes priority).
        """
        tu = ticker.upper()
        if tu in self._seeds:
            return self._seeds[tu]

        cik = company.cik if company else self.facts.resolve_cik_from_ticker(ticker)
        if not cik:
            return DilutionTrackerData(ticker=tu)

        # Auto-refresh: check if new filings exist since last cache
        self._check_cache_freshness(cik, tu)

        meta_filings = self.facts.get_recent_filings(cik, limit=40)
        tracker = DilutionTrackerData(ticker=tu, company_name=company.company_name if company else None, price=price or (company.market_cap if company else None), market_cap=company.market_cap if company else None, country=company.country if company else None, sector=company.sector if company else None, exchange=self._guess_exchange(cik))

        # Cash (RAG -> regex fallback)
        cf = self._get_filing_urls(cik, ["10-Q", "10-K"], limit=2)
        rag = self._rag_extractor
        if rag and cf:
            for m in cf:
                p = self._get_parsed(str(m.url))
                if p and (d := rag.extract_cash(p)):
                    tracker.cash_position = CashPosition(**d)
                    break
        if not tracker.cash_position:
            text = self._filing_texts([str(m.url) for m in (cf or meta_filings) if m.form_type in ("10-Q","10-K")][:2])
            if text:
                cash = burn = None
                m = re.search(r"(?:cash\s+(?:and\s+cash\s+equivalent|balance)|unrestricted\s+cash).{0,100}?\$?\s*([\d,]+(?:\.\d+)?)\s*(million|billion|M|B|thousand|K)?", text, re.I)
                if m and m.group(1):
                    try:
                        v = float(m.group(1).replace(",",""))
                        u = (m.group(2) or "").lower()
                        if u in ("million","m"): v*=1e6
                        elif u in ("billion","b"): v*=1e9
                        cash = v
                    except ValueError: pass
                m = re.search(r"(?:net\s+cash\s+(?:used\s+in\s+)?operating|operating\s+(?:activities|cash\s+flow)).{0,100}?\$?\s*([\d,]+(?:\.\d+)?)\s*(million|billion|M|B|thousand|K)?", text, re.I)
                if m and m.group(1):
                    try:
                        v = float(m.group(1).replace(",",""))
                        u = (m.group(2) or "").lower()
                        if u in ("million","m"): v*=1e6
                        burn = abs(v)
                    except ValueError: pass
                tracker.cash_position = CashPosition(cash_estimated=cash, quarterly_burn=burn, months_of_cash=(cash/burn*3) if cash and burn else None, going_concern=bool(re.search(r"going\s+concern", text, re.I)))

        # Shelf registration
        if tracker.shelf is None:
            tracker.shelf = ShelfRegistration()
        shelf_filings = self._get_filing_urls(cik, ["S-3","S-3/A"], limit=2)
        for sf in shelf_filings:
            try:
                shelf_ck = hashlib.sha256(f"{sf.url}:shelf".encode()).hexdigest()[:32]
                with sqlite3.connect(str(self.settings.data_dir / "extraction_cache.sqlite"), timeout=5) as conn:
                    shelf_row = conn.execute(
                        "SELECT result_json FROM extraction_cache WHERE url_hash=? AND extraction_type=?", (shelf_ck, 'shelf')).fetchone()
                if shelf_row:
                    sj = json.loads(shelf_row[0])
                    if isinstance(sj, dict) and sj.get("active"):
                        tracker.shelf.active = True
                        tracker.shelf.total_offering = sj.get("total_offering")
                        tracker.shelf.raisable_total = sj.get("raisable_total") or sj.get("total_offering")
                        tracker.shelf.amt_sold_last_12m = sj.get("amt_sold_last_12m")
                        tracker.shelf.expiration = sj.get("expiration")
            except Exception as exc:
                logger.debug("Shelf cache read failed: %s", exc)
        if tracker.shelf and tracker.shelf.active:
            flt = company.float_shares if company else None
            if flt:
                tracker.shelf.float_shares = flt
                mkt_cap = price * flt if price else None
                if mkt_cap and tracker.shelf.raisable_total:
                    tracker.shelf.price_to_exceed_baby_shelf = (tracker.shelf.raisable_total * 3) / flt
                    tracker.shelf.float_value = mkt_cap
                    tracker.shelf.over_baby_shelf = price is not None and tracker.shelf.price_to_exceed_baby_shelf is not None and price > tracker.shelf.price_to_exceed_baby_shelf

        # Atms
        atms = self._get_filing_urls(cik, ["S-3","S-3/A","424B","424B5","424B4","424B3"], limit=3)
        r = self._rag_batch("extract_atms", atms, ATMProgram)
        if not r and atms:
            text = self._filing_texts([str(m.url) for m in atms][:2])
            if re.search(r"at[- ]the[- ]market", text, re.I):
                r = [ATMProgram(name="ATM Program")]
        tracker.atms = r

        # Warrants
        ws = self._get_filing_urls(cik, ["424B","424B5","424B4","424B3","424B2","S-1","S-1/A"], limit=5)
        tracker.warrants = self._rag_batch("extract_warrants", ws, WarrantIssue)

        # Convertibles
        cs = self._get_filing_urls(cik, ["8-K","10-Q","10-K"], limit=5)
        tracker.convertibles = self._rag_batch("extract_convertibles", cs, ConvertibleIssue)

        # Equity lines
        es = self._get_filing_urls(cik, ["8-K","S-1"], limit=5)
        tracker.equity_lines = self._rag_batch("extract_equity_lines", es, EquityLine)

        # Completed offerings
        if filings:
            seen, offs = set(), []
            for f in sorted(filings, key=lambda x: x.filed_date, reverse=True):
                ds = f.filed_date.isoformat() if hasattr(f.filed_date,'isoformat') else str(f.filed_date)
                k = f"{ds}_{f.form_type}"
                if k in seen: continue
                seen.add(k)
                s = f.summary or ""
                # Check if 8-K contains offering language
                _is_merger = bool(re.search(r'merger\s+agreement|plan\s+of\s+merger|business\s+combination', s, re.I))
                has_offering = bool(re.search(r'offering|atm|purchase\s+agreement|priced|equity\s+line', s, re.I)) and not _is_merger
                has_warrant_keyword = bool(re.search(r'\bwarrant', s, re.I)) and not _is_merger
                if f.form_type == "8-K" and (has_offering or has_warrant_keyword):
                    # Try to extract amount from summary text first
                    if f.shelf_amount_usd is None:
                        am = re.search(r'\$(\d[\d,]+(?:\.\d+)?)\s*(?:million|M)?', s, re.I)
                        if am:
                            val = float(am.group(1).replace(',',''))
                            if 'million' in s.lower() or 'm' in s.lower().split('$')[-1][:20]:
                                val *= 1_000_000
                            f.shelf_amount_usd = val
                    # Try to download filing text for 8-Ks with warrants but no amount
                    if f.shelf_amount_usd is None and has_warrant_keyword and f.source_url:
                        try:
                            _content = self._fetch_filing_text(f.source_url)
                            if _content:
                                # Check if actually a merger before marking as offering
                                if re.search(r'merger\s+agreement|plan\s+of\s+merger', _content, re.I):
                                    _is_merger = True
                                if not _is_merger:
                                    _m = re.search(r'(?:gross\s+proceeds|offering\s+(?:amount|size|value)|purchase\s+(?:price|amount)|aggregate\s+(?:gross\s+)?proceeds).{0,200}?\$?(\d[\d,]+(?:\.\d+)?)\s*(million|M|billion|B)?', _content, re.I)
                                    if _m:
                                        _val = float(_m.group(1).replace(',', ''))
                                        _unit = _m.group(2)
                                        if _unit and 'b' in _unit.lower():
                                            _val *= 1_000_000_000
                                        elif _unit and 'm' in _unit.lower():
                                            _val *= 1_000_000
                                        f.shelf_amount_usd = _val
                        except Exception as _exc:
                            logger.debug("8-K text fetch failed for %s: %s", f.accession_number, _exc)
                    # Classify as offering only if we found an amount, otherwise MATERIAL AGREEMENT
                    otype = "REGISTERED OFFERING" if f.shelf_amount_usd else "MATERIAL AGREEMENT"
                else:
                    otype = "REGISTERED OFFERING" if f.form_type and f.form_type.startswith("424B") else \
                            "REGISTERED OFFERING" if f.form_type == "S-1" else \
                            "SHELF" if f.form_type and f.form_type.startswith("S-3") else \
                            "MATERIAL AGREEMENT" if f.form_type == "8-K" else "OTHER"
                bank = "Maxim Group" if "Maxim" in s else "H.C. Wainwright" if "Wainwright" in s else "Armistice" if "Armistice" in s else \
                        "Ladenburg" if "Ladenburg" in s else "Roth" if "Roth" in s else "Aegis" if "Aegis" in s else \
                        "ThinkEquity" if "ThinkEquity" in s else None
                # Populate warrants count if available (no shares estimation —
                # using today's price to estimate shares for past dates is misleading)
                _warrants_count: Optional[float] = None
                if f.warrants_found:
                    if f.warrants_detail:
                        _warrants_count = float(len(f.warrants_detail))
                    else:
                        _warrants_count = 1.0  # flag: warrants present but count unknown
                offs.append(CompletedOffering(
                    date=ds, type=otype, amount=f.shelf_amount_usd,
                    shares=None, price=None,
                    warrants=_warrants_count, bank=bank,
                    detail=f.summary or f.form_type,
                ))
            tracker.completed_offerings = offs

        # Add offering filings (424B, S-1, S-3) - last 12 months for full history
        from datetime import timedelta, date as dt_date
        year_ago = dt_date.today() - timedelta(days=365)
        sec_offerings = self._get_filing_urls(cik, ["424B","424B2","424B3","424B4","424B5","424B7","424B8","S-1","S-3"], limit=15)
        seen_keys = set(f"{o.date}_{o.type}" for o in tracker.completed_offerings if o.date)
        for f in sec_offerings:
            try:
                fd = dt_date.fromisoformat(f.filed_date) if isinstance(f.filed_date, str) else f.filed_date
                if fd < year_ago: continue
            except Exception as exc:
                logger.debug("Date parse failed for offering filing: %s", exc)
            key = f"{f.filed_date}_{f.form_type}"
            if key in seen_keys: continue
            seen_keys.add(key)
            otype = f.form_type  # Use the actual form type
            amount = None
            try:
                ck = hashlib.sha256(f"{f.url}:shelf".encode()).hexdigest()[:32]
                with sqlite3.connect(str(self.settings.data_dir / "extraction_cache.sqlite"), timeout=5) as conn:
                    row = conn.execute(
                        "SELECT result_json FROM extraction_cache WHERE url_hash=? AND extraction_type=?", (ck, 'shelf')).fetchone()
                if row:
                    sj = json.loads(row[0])
                    amount = sj.get("total_offering") if isinstance(sj, dict) else None
            except Exception as exc:
                logger.debug("Shelf cache read failed: %s", exc)
            tracker.completed_offerings.append(CompletedOffering(date=f.filed_date, type=otype, amount=amount, detail=f.form_type))

        # Add/upgrade from equity_line RAG data (replace generic MATERIAL AGREEMENT)
        for el in tracker.equity_lines:
            if el.date and el.shares:
                existing = next((o for o in tracker.completed_offerings if o.date == el.date), None)
                if existing and existing.amount is None:
                    existing.amount = el.total_amt
                    existing.shares = el.shares
                    existing.type = "REGISTERED OFFERING"
                elif existing is None:
                    tracker.completed_offerings.append(CompletedOffering(date=el.date, type="REGISTERED OFFERING", amount=el.total_amt, shares=el.shares))
        tracker.completed_offerings.sort(key=lambda o: o.date or "", reverse=True)

        # Lockups, compliance, splits
        text = self._filing_texts([str(m.url) for m in meta_filings if m.form_type in ("S-1","S-3")][:2])
        tracker.lock_up_agreements = []
        for m in re.finditer(r"(?:lock[-\s]up|lockup)\s+(?:agreement|period|restriction)", text, re.I):
            days = int(m2.group(1)) if (m2:=re.search(r"(\d+)[-\s]day",text[m.end():m.end()+500],re.I)) else None
            tracker.lock_up_agreements.append(LockUpAgreement(description="Lock-up agreement", duration_days=days))
        if not tracker.lock_up_agreements and re.search(r"S-1|S-3", text, re.I):
            tracker.lock_up_agreements.append(LockUpAgreement(description="Standard lock-up (officers & directors)", duration_days=60))

        text = self._filing_texts([str(m.url) for m in meta_filings if m.form_type == "8-K"][:5])
        tracker.nasdaq_compliance = []
        for m in re.finditer(r"(?:NASDAQ|nasdaq|Nasdaq).*?(?:deficiency|compliance|notice|non[-\s]compliance|bid\s+price|equity|stockholder)", text, re.I):
            chunk = text[m.start():m.end()+300]
            rule = m2.group(1).strip() if (m2:=re.search(r"(?:Rule|Section|Listing\s+Rule)\s+(\d+[a-zA-Z0-9\s().]*)",chunk,re.I)) else None
            tracker.nasdaq_compliance.append(NasdaqComplianceItem(rule=rule, status="RESOLVED" if "resolved" in chunk.lower() else "NOTICE"))

        tracker.reverse_splits = [ReverseSplit(ratio=f"{m.group(1)}-to-{m.group(2)}") for m in re.finditer(r"(?:reverse\s+(?:stock\s+)?split|reverse\s+stock\s+division).*?(\d+)[-\s]*to[-\s]*(\d+)",text,re.I)]

        max_dil = max((f.dilution_percentage or 0 for f in (filings or [])), default=0)
        tracker.estimated_dilution_pct = max_dil or None
        tracker.risk_level = "HIGH" if max_dil >= 20 else "MEDIUM" if max_dil >= 10 else "LOW"

        # Build pending dilution events (active sources that could still dilute)
        mkt_price = price or tracker.price or 0
        if tracker.shelf and tracker.shelf.active and tracker.shelf.raisable_total:
            sh_amt = tracker.shelf.raisable_total
            sh_shares = sh_amt / mkt_price if mkt_price and mkt_price > 0 else None
            tracker.pending_events.append(PendingDilutionEvent(
                type="shelf", label=f"Shelf remaining: ${sh_amt/1e6:.0f}M",
                max_dilution_usd=sh_amt, max_dilution_shares=sh_shares,
                urgency="HIGH", trigger_condition="Company files prospectus supplement",
                detail=f"${sh_amt/1e6:.1f}M remaining on S-3 shelf",
            ))
        for atm in tracker.atms:
            if atm.remaining and atm.remaining > 0:
                atm_shares = atm.remaining / mkt_price if mkt_price and mkt_price > 0 else None
                tracker.pending_events.append(PendingDilutionEvent(
                    type="atm", label=f"ATM: ${atm.remaining/1e6:.0f}M remaining",
                    max_dilution_usd=atm.remaining, max_dilution_shares=atm_shares,
                    urgency="HIGH", trigger_condition="Broker sells shares at market",
                    detail=f"{atm.name or 'ATM'} via {atm.bank or 'broker'}",
                ))
        for w in tracker.warrants:
            if w.remaining and w.exercise_price:
                itm = mkt_price and w.exercise_price < mkt_price if price else None
                if itm:
                    dil_shares = w.remaining
                    dil_pct = (dil_shares / tracker.shelf.float_shares * 100) if tracker.shelf and tracker.shelf.float_shares else None
                    tracker.pending_events.append(PendingDilutionEvent(
                        type="warrant", label=f"{w.issue_label}: {w.remaining:,.0f} warrants @ ${w.exercise_price:.2f}",
                        max_dilution_shares=w.remaining, urgency="HIGH" if w.protection == "Full Ratchet" else "MEDIUM",
                        trigger_condition=f"Exercise price ${w.exercise_price:.2f} below market ${mkt_price:.2f}" if mkt_price else "Warrants exercisable",
                        detail=f"ITM +{dil_pct:.1f}% dilution" if dil_pct else "ITM",
                    ))
        for c in tracker.convertibles:
            if c.remaining and c.remaining > 0:
                cv_shares = c.remaining / c.conversion_price if c.conversion_price else None
                tracker.pending_events.append(PendingDilutionEvent(
                    type="convertible", label=f"Convertible: ${c.remaining/1e6:.1f}M outstanding",
                    max_dilution_shares=cv_shares, urgency="HIGH" if c.protection == "Full Ratchet" else "MEDIUM",
                    trigger_condition="Holder converts notes to shares",
                    detail=f"${c.total/1e6:.1f}M issued, ${c.remaining/1e3:.0f}K remaining",
                ))
        return tracker

    def _fetch_filing_text(self, url: str, max_bytes: int = 20480) -> Optional[str]:
        """Download SEC filing text for lightweight regex extraction.

        Args:
            url: SEC filing URL (HTML or HTM).
            max_bytes: Max bytes to download (default 20KB).

        Returns:
            Filing text as string, or None on failure.
        """
        from apis.connection_pool import get_client
        from config import get_settings
        _settings = get_settings()
        try:
            _client = get_client(timeout=8.0)
            _resp = _client.get(url, headers={"User-Agent": _settings.sec_user_agent})
            _resp.raise_for_status()
            _text = _resp.text[:max_bytes]
            # Strip HTML tags for regex matching
            _clean = re.sub(r'<[^>]+>', ' ', _text)
            return _clean
        except Exception as exc:
            logger.debug("Failed to fetch %s: %s", url, exc)
            return None

    def _guess_exchange(self, cik: str) -> Optional[str]:
        info = self.facts.get_company_info(cik)
        return "NASDAQ" if (info and info.get("tickers")) else None
