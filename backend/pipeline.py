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

CRITICAL_FORMS = ["S-3", "S-3/A", "424B3", "424B5", "424B2", "8-K", "EFFECT", "RW", "S-1"]


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
        max_filings: int = 5,
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
            country=profile.country or "US",
        ))

        filings_meta = self.facts.get_recent_filings(cik, form_filter=CRITICAL_FORMS, limit=max_filings)
        if not filings_meta:
            filings_meta = self.facts.get_recent_filings(cik, limit=max_filings)

        processed: List[FilingDilution] = []
        rag_results: List[ScanResult] = []

        for meta in filings_meta[:max_filings]:
            try:
                url = str(meta.url)
                if not url.endswith(".htm") and not url.endswith(".html"):
                    url = url.replace("-index.htm", ".htm") if "-index" in url else url

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
                    risk_level=dilution.risk_level,
                    summary=", ".join(ext.matched_keywords) or None,
                    source_url=url,
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
