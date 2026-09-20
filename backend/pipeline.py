"""End-to-end scan + analyze pipeline."""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import List, Optional

from apis.data_enrichment import DataEnrichment
from db.database import Database
from models import Company, FilingDilution, PipelineResult, RiskLevel, ScanResult
from parsers.dilution_calculator import DilutionCalculator
from parsers.sec_parser import SECParser
from rag.rag_engine import RAGEngine
from scanners.company_facts import CompanyFactsClient

logger = logging.getLogger(__name__)

# All forms to scan — broad coverage for grouped filings view
ALL_FORMS = None  # None = scan everything the SEC API has
# Fallback for SEC form descriptions when summary is empty
FORM_DESCRIPTIONS = {
    "10-Q": "Form 10-Q — Quarterly report [Sections 13 or 15(d)]",
    "10-K": "Form 10-K — Annual report [Section 13 and 15(d)]",
    "10-Q/A": "Form 10-Q/A — Quarterly report [Amendment]",
    "10-K/A": "Form 10-K/A — Annual report [Amendment]",
    "8-K": "Form 8-K — Current report",
    "8-K/A": "Form 8-K/A — Current report [Amendment]",
    "S-1": "Form S-1 — General form for registration of securities",
    "S-1/A": "Form S-1/A — Registration statement [Amendment]",
    "S-3": "Form S-3 — Shelf registration statement",
    "S-3/A": "Form S-3/A — Shelf registration [Amendment]",
    "S-8": "Form S-8 — Securities to be offered to employees",
    "424B2": "Prospectus supplement [Rule 424(b)(2)]",
    "424B3": "Prospectus supplement [Rule 424(b)(3)]",
    "424B4": "Form 424B4 — Prospectus [Rule 424(b)(4)]",
    "424B5": "Prospectus supplement [Rule 424(b)(5)]",
    "DEF 14A": "Form DEF 14A — Definitive proxy statement",
    "DEFA14A": "Form DEFA14A — Additional definitive proxy materials",
    "PRE 14A": "Form PRE 14A — Preliminary proxy statement",
    "3": "Form 3 — Initial statement of beneficial ownership",
    "4": "Form 4 — Statement of changes in beneficial ownership",
    "5": "Form 5 — Annual statement of beneficial ownership",
    "144": "Form 144 — Report of proposed sale of securities",
    "13G": "Schedule 13G — Beneficial ownership report",
    "13G/A": "Schedule 13G/A — Beneficial ownership [Amendment]",
    "13D": "Schedule 13D — Beneficial ownership report",
    "EFFECT": "Form EFFECT — Notice of Effectiveness",
    "RW": "Form RW — Withdrawal of registration statement",
    "SD": "Form SD — Specialized disclosure report",
    "CORRESP": "Form CORRESP — Correspondence",
    "LETTER": "Form UPLOAD — SEC-generated letter",
    "DRS": "Form DRS — Draft registration statement",
    "8-A12B": "Form 8-A12B — Registration of securities [Section 12(b)]",
}


class ScanPipeline:
    """Orchestrates: CIK resolve → fetch filings → parse → dilution calc → RAG → store."""

    def __init__(self) -> None:
        self.facts = CompanyFactsClient()
        self.parser = SECParser()
        self.calculator = DilutionCalculator()
        self.enrichment = DataEnrichment()
        self.db = Database()
        self.rag: Optional[RAGEngine] = None

    def _get_rag(self) -> RAGEngine:
        if self.rag is None:
            self.rag = RAGEngine()
        return self.rag

    def resolve_cik(self, ticker: str) -> Optional[str]:
        cik = self.facts.resolve_cik_from_ticker(ticker)
        if cik:
            return cik
        company = self.db.parquet.get_company_by_ticker(ticker)
        return company.cik if company else None

    def scan_ticker(
        self,
        ticker: str,
        *,
        question: Optional[str] = None,
        prompt_type: Optional[str] = None,
        max_filings: int = 10,
        run_rag: bool = True,
    ) -> PipelineResult:
        """Full scan pipeline for a ticker."""
        ticker = ticker.upper()
        logger.info("Starting pipeline scan for %s", ticker)

        cik = self.resolve_cik(ticker)
        if not cik:
            raise ValueError(f"Could not resolve CIK for ticker {ticker}")

        profile = self.enrichment.get_ticker_profile(ticker)
        shares = profile.shares_outstanding or self.facts.get_shares_outstanding(cik)
        price = profile.price

        self.db.save_company(Company(
            cik=cik,
            ticker=ticker,
            company_name=profile.company_name or ticker,
            float_shares=profile.float_shares,
            shares_outstanding=shares,
            sector=profile.sector,
            country=profile.country,
        ))

        filings_meta = self.facts.get_recent_filings(cik, form_filter=ALL_FORMS, limit=max_filings * 3)
        if not filings_meta:
            filings_meta = self.facts.get_recent_filings(cik, limit=max_filings * 3)

        # Priority: offering forms (424B, S-3, S-1) > 8-K > others
        def form_priority(m):
            f = m.form_type.upper()
            if f.startswith("424B") or f.startswith("S-3") or f in ("S-1", "EFFECT"):
                return 0
            if f == "8-K":
                return 1
            return 2
        filings_meta.sort(key=form_priority)

        processed: List[FilingDilution] = []
        rag_results: List[ScanResult] = []
        seen_urls: set[str] = set()

        for meta in filings_meta[:max_filings]:
            try:
                url = str(meta.url)
                if not url.endswith(".htm") and not url.endswith(".html"):
                    url = url.replace("-index.htm", ".htm") if "-index" in url else url

                # Skip duplicate URLs — some filings share the same document
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                parsed = self.parser.parse(url)
                ext = parsed.extraction

                dilution = self.calculator.calculate(
                    parsed.text,
                    current_price=price,
                    shares_outstanding=shares,
                    has_warrants=ext.warrants_found,
                    has_full_ratchet=ext.has_full_ratchet,
                )

                shelf = ext.shelf_amount_usd or dilution.offering_amount_usd
                try:
                    filed = datetime.strptime(meta.filed_date, "%Y-%m-%d").date()
                except ValueError:
                    filed = date.today()

                filing = FilingDilution(
                    accession_number=meta.accession_number,
                    cik=cik,
                    ticker=ticker,
                    form_type=meta.form_type,
                    filed_date=filed,
                    shelf_amount_usd=shelf,
                    dilution_percentage=dilution.dilution_percentage,
                    warrants_found=ext.warrants_found,
                    has_atm=ext.has_atm,
                    has_full_ratchet=ext.has_full_ratchet,
                    has_prefunded_warrants=ext.has_prefunded_warrants,
                    is_shelf_takedown=ext.is_shelf_takedown,
                    is_rights_offering=ext.is_rights_offering,
                    is_overnight_offering=ext.is_overnight_offering,
                    is_block_trade=ext.is_block_trade,
                    is_secondary_offering=ext.is_secondary_offering,
                    is_primary_offering=ext.is_primary_offering,
                    is_best_efforts=ext.is_best_efforts,
                    is_firm_commitment=ext.is_firm_commitment,
                    is_global_offering=ext.is_global_offering,
                    is_continuous_offering=ext.is_continuous_offering,
                    is_spot_offering=ext.is_spot_offering,
                    is_warrant_offering=ext.is_warrant_offering,
                    risk_level=dilution.risk_level,
                    summary=", ".join(ext.matched_keywords) or FORM_DESCRIPTIONS.get(meta.form_type) or None,
                    source_url=url,
                    warrants_detail=ext.warrants_detail,
                )
                self.db.save_dilution_alert(filing)
                processed.append(filing)

                if run_rag and (question or prompt_type):
                    rag = self._get_rag()
                    result = rag.scan_url(
                        url,
                        question=question,
                        prompt_type=prompt_type,
                        ticker=ticker,
                    )
                    rag_results.append(result)

            except Exception as exc:
                logger.error("Failed processing %s: %s", meta.accession_number, exc)

        return PipelineResult(
            ticker=ticker,
            cik=cik,
            profile=profile,
            filings_processed=len(processed),
            filings=processed,
            rag_results=rag_results,
        )
