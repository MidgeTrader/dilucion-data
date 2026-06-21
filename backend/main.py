#!/usr/bin/env python3
"""Dilucion Data — unified CLI and API server."""

from __future__ import annotations

import argparse
import logging
import sys
from typing import List, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("sec_dilution")


def cmd_scan_ticker(args: argparse.Namespace) -> int:
    from pipeline import ScanPipeline
    from rag.prompts import list_prompts

    pipeline = ScanPipeline()
    prompt_type = args.prompt if args.prompt in list_prompts() else None
    question = args.ask or (args.prompt if prompt_type is None else None)
    result = pipeline.scan_ticker(
        args.target,
        question=question,
        prompt_type=prompt_type,
        run_rag=bool(question or prompt_type),
    )
    print(f"\n{'='*60}")
    print(f"Ticker: {result.ticker} | CIK: {result.cik}")
    print(f"Filings processed: {result.filings_processed}")
    print(f"Price: ${result.profile.price or 'N/A'}")
    print(f"{'='*60}")
    for f in result.filings:
        pct = f"{f.dilution_percentage:.1f}%" if f.dilution_percentage else "N/A"
        print(f"  {f.form_type} | {f.filed_date} | Dilution: {pct} | Risk: {f.risk_level}")
        if f.summary:
            print(f"    Keywords: {f.summary}")
    for r in result.rag_results:
        print(f"\n--- RAG Answer ---\n{r.answer[:2000]}")
    return 0


def cmd_scan_url(args: argparse.Namespace) -> int:
    from rag.rag_engine import RAGEngine
    from rag.prompts import list_prompts

    engine = RAGEngine()
    prompt_type = args.prompt if args.prompt in list_prompts() else None
    result = engine.scan_url(args.target, prompt_type=prompt_type or "dilution")
    print(result.answer)
    return 0


def cmd_monitor(args: argparse.Namespace) -> int:
    from db.database import Database
    from scanners.dilution_scanner import DilutionScanner
    from scanners.rss_monitor import RSSMonitor

    db = Database()

    def on_alert(alert):
        db.save_dilution_alert_from_rss(alert) if hasattr(db, "save_dilution_alert_from_rss") else None
        print(f"🚨 {alert.form_type} | {alert.company_name} | {alert.filing_url}")

    if args.daily:
        scanner = DilutionScanner()
        filings = scanner.scan_date()
        print(f"Daily scan: {len(filings)} critical filings")
        for f in filings:
            print(f"  {f.alert_level} {f.form_type} | {f.company_name} | {f.filing_url}")
        return 0

    monitor = RSSMonitor()
    if args.once:
        alerts = monitor.poll_once()
        for a in alerts:
            print(f"🚨 {a.form_type} | {a.company_name} | {a.filing_url}")
        return 0

    monitor.run_daemon(interval_seconds=args.interval, on_alert=on_alert)
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    from scanners.efts_search import EFTSSearch

    search = EFTSSearch()
    hits = search.search(args.query, limit=args.limit) if args.query else search.search_all_defaults(args.limit)
    for h in hits:
        print(f"\n[{h.form_type}] {h.company_name} ({h.cik}) — {h.filed_date}")
        print(f"  Query: {h.query}")
        print(f"  URL: {h.filing_url}")
        if h.excerpt:
            print(f"  Excerpt: {h.excerpt[:200]}...")
    print(f"\nTotal hits: {len(hits)}")
    return 0


def cmd_filings(args: argparse.Namespace) -> int:
    from scanners.company_facts import CompanyFactsClient

    facts = CompanyFactsClient()
    cik = args.cik.lstrip("0")
    filings = facts.get_recent_filings(cik, limit=args.limit)
    for f in filings:
        print(f"{f.filed_date} | {f.form_type} | {f.accession_number} | {f.url}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    from db.parquet_db import ParquetDB

    db = ParquetDB()
    summary = db.report_summary()
    print("\n=== Dilution Risk Report ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    print("\nTop risks:")
    for i, f in enumerate(db.query_top_dilution(args.limit), 1):
        pct = f"{f.dilution_percentage:.1f}%" if f.dilution_percentage else "N/A"
        print(f"  {i}. {f.ticker or f.cik} | {f.form_type} | {pct} | {f.risk_level}")
    return 0


def cmd_db_init(_: argparse.Namespace) -> int:
    from db.database import Database
    Database().init()
    print("Database initialized (Parquet + SQLite).")
    return 0


def cmd_db_stats(_: argparse.Namespace) -> int:
    from db.database import Database
    import json
    print(json.dumps(Database().stats(), indent=2, default=str))
    return 0


def cmd_rag(args: argparse.Namespace) -> int:
    from rag.prompts import list_prompts
    from rag.rag_engine import RAGEngine

    engine = RAGEngine()
    if args.target.startswith("http"):
        result = engine.scan_url(args.target, prompt_type=args.prompt, question=args.question)
        print(result.answer)
    else:
        prompt_type = args.prompt if args.prompt in list_prompts() else None
        response = engine.query_ticker(
            args.target.upper(),
            question=args.question,
            prompt_type=prompt_type,
            use_reasoning=args.prompt == "convertible",
        )
        print(response.answer)
    return 0


def cmd_tickers_refresh(_: argparse.Namespace) -> int:
    from apis.data_enrichment import DataEnrichment
    count = DataEnrichment().refresh_tickers_to_parquet()
    print(f"Refreshed {count} tickers.")
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    import uvicorn
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel

    from apis.data_enrichment import DataEnrichment
    from config import get_settings
    from db.database import Database
    from models import RAGResponse, RiskAssessment, RiskLevel
    from rag.prompts import get_prompt
    from rag.rag_engine import RAGEngine

    settings = get_settings()
    app = FastAPI(title="SEC Dilution Tracker API", version="2.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url, "http://localhost:3000", "http://localhost:3001"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # --- IP-based rate limiter for /rag endpoint ---
    import time as _time
    from collections import defaultdict
    _rag_requests: dict[str, list[float]] = defaultdict(list)
    _RAG_RATE_LIMIT = 20
    _RAG_RATE_WINDOW = 60.0

    def _check_rag_rate_limit(client_ip: str) -> None:
        now = _time.time()
        window_start = now - _RAG_RATE_WINDOW
        ts_list = _rag_requests[client_ip]
        _rag_requests[client_ip] = [t for t in ts_list if t > window_start]
        if len(_rag_requests[client_ip]) >= _RAG_RATE_LIMIT:
            raise HTTPException(429, "Rate limit exceeded for /rag (20 req/min). Try again later.")
        _rag_requests[client_ip].append(now)

    db = Database()
    enrichment = DataEnrichment()

    class RagBody(BaseModel):
        question: str = ""
        ticker: Optional[str] = None
        url: Optional[str] = None
        prompt_type: Optional[str] = None
        use_reasoning: bool = False

    @app.get("/health")
    def health():
        return {"status": "ok", "version": "2.0.0"}

    @app.post("/rag", response_model=RAGResponse)
    def rag_endpoint(body: RagBody, request: Request):
        client_ip = request.client.host if request.client else "unknown"
        _check_rag_rate_limit(client_ip)
        try:
            engine = RAGEngine()
            question = body.question
            if body.prompt_type:
                question = get_prompt(body.prompt_type)
            if body.url:
                r = engine.scan_url(body.url, question=question, ticker=body.ticker,
                                    use_reasoning=body.use_reasoning or body.prompt_type == "convertible")
                return RAGResponse(answer=r.answer, citations=r.citations, model=settings.deepseek_model,
                                   ticker=body.ticker, source_url=r.source_url)
            if body.ticker:
                return engine.query_ticker(body.ticker, question=question, prompt_type=body.prompt_type,
                                           use_reasoning=body.use_reasoning)
            raise HTTPException(400, "Provide url or ticker")
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
        except Exception as e:
            logger.exception("RAG error")
            raise HTTPException(500, str(e)) from e

    @app.get("/ticker/{ticker}")
    def ticker_profile(ticker: str):
        profile = enrichment.get_ticker_profile(ticker)
        company = db.parquet.get_company_by_ticker(ticker)
        if company:
            profile.cik = company.cik
            profile.company_name = profile.company_name or company.company_name
            profile.shares_outstanding = profile.shares_outstanding or company.shares_outstanding
        filings = db.parquet.get_filings_by_ticker(ticker)

        # Auto-scan si el ticker no tiene filings todavia
        if not filings:
            try:
                from pipeline import ScanPipeline
                result = ScanPipeline().scan_ticker(ticker, run_rag=False)
                if result and result.filings_processed > 0:
                    filings = result.filings
                    profile = result.profile
                    logger.info("Auto-scan completado para %s: %d filings", ticker, result.filings_processed)
            except Exception as exc:
                logger.warning("Auto-scan fallo para %s: %s", ticker, exc)

        # Si faltan filings, traerlos de SEC directo (desde SEC)
        from models import FilingDilution
        from datetime import datetime as _dt
        if len(filings) < 30 and profile.cik:
            try:
                from scanners.company_facts import CompanyFactsClient
                sec = CompanyFactsClient()
                sec_filings = sec.get_recent_filings(profile.cik, limit=80)
                seen = set(f.accession_number for f in filings if f.accession_number)
                for sf in sec_filings:
                    if sf.accession_number not in seen:
                        seen.add(sf.accession_number)
                        filings.append(FilingDilution(
                            accession_number=sf.accession_number,
                            cik=profile.cik, ticker=ticker.upper(),
                            form_type=sf.form_type,
                            filed_date=_dt.strptime(sf.filed_date, '%Y-%m-%d').date() if isinstance(sf.filed_date, str) else sf.filed_date,
                            source_url=str(sf.url),
                            summary=sf.description or f'Form {sf.form_type}',
                        ))
                # Generate rich headlines with DeepSeek for recent filings
                try:
                    from dilution_rag import DilutionRAGExtractor
                    _rag_h = DilutionRAGExtractor()
                    for _sf in sec_filings[:20]:
                        _url = str(_sf.url)
                        _h = _rag_h.generate_headline(_url)
                        if _h:
                            for _f in filings:
                                if getattr(_f, 'accession_number', None) == _sf.accession_number:
                                    _f.summary = _h
                                    break
                except Exception:
                    pass
                logger.info("Complementados %d filings desde SEC para %s", len(sec_filings), ticker)
            except Exception as exc:
                logger.warning("SEC complement fallo para %s: %s", ticker, exc)

        candles = enrichment.polygon.get_candles(ticker, days=365)
        news = enrichment.get_company_news(
            ticker,
            company_name=profile.company_name,
            filings=filings,
            limit=30,
        )
        # Solo noticias reales — los filings ya van en la sección filings
        real_news = [n for n in news if n.source_type not in ("sec", "edgar")]
        news_payload = [n.model_dump() for n in real_news]
        risk = _risk(filings, profile)
        result = {
            "profile": profile.model_dump(),
            "filings": [f.model_dump() for f in filings],
            "candles": [c.model_dump() for c in candles],
            "risk": risk.model_dump(),
            "news": news_payload,
            "articles": news_payload,
            "insights": _insights(filings, profile, risk),
            "research_summary": _research_summary(ticker.upper(), filings, profile, risk,
                                                    _insights(filings, profile, risk)),
            "dilution": _dilution_detail(filings, profile, risk),
        }
        # Generate AI research report in Spanish via DeepSeek
        try:
            from dilution_rag import DilutionRAGExtractor
            _rag_r = DilutionRAGExtractor()
            _ai_report = _rag_r.generate_research_report(ticker.upper(), {
                "profile": profile.model_dump() if hasattr(profile, "model_dump") else profile,
                "filings": [f.model_dump() if hasattr(f, "model_dump") else f for f in filings],
                "risk": risk.model_dump() if hasattr(risk, "model_dump") else risk,
            })
            if _ai_report:
                result["research_summary"] = _ai_report
        except Exception:
            pass
        return result

    @app.get("/ticker/{ticker}/dilution")
    def ticker_dilution_detail(ticker: str):
        """Full dilution tracker data for a ticker."""
        profile = enrichment.get_ticker_profile(ticker)
        company = db.parquet.get_company_by_ticker(ticker)
        filings = db.parquet.get_filings_by_ticker(ticker)

        if not filings:
            try:
                from pipeline import ScanPipeline
                result = ScanPipeline().scan_ticker(ticker, run_rag=False)
                if result and result.filings_processed > 0:
                    filings = result.filings
                    profile = result.profile
            except Exception as exc:
                logger.warning("Auto-scan falló para dilution de %s: %s", ticker, exc)

        from dilution_tracker import DilutionTrackerService
        tracker = DilutionTrackerService()
        data = tracker.get_dilution_data(
            ticker=ticker,
            company=company,
            filings=filings,
            price=profile.price,
        )
        # Merge profile data
        data.price = profile.price
        data.market_cap = profile.market_cap
        data.country = profile.country
        data.sector = profile.sector
        data.exchange = profile.exchange
        return data.model_dump()

    @app.get("/ticker/{ticker}/news")
    def ticker_news(ticker: str, limit: int = 30):
        profile = enrichment.get_ticker_profile(ticker)
        filings = db.parquet.get_filings_by_ticker(ticker)
        if not filings:
            try:
                from pipeline import ScanPipeline
                result = ScanPipeline().scan_ticker(ticker, run_rag=False)
                if result and result.filings_processed > 0:
                    filings = result.filings
            except Exception as exc:
                logger.warning("Auto-scan falló para news de %s: %s", ticker, exc)
        news = enrichment.get_company_news(
            ticker,
            company_name=profile.company_name,
            filings=filings,
            limit=limit,
        )
        return [n.model_dump() for n in news if n.source_type not in ("sec", "edgar")]

    @app.get("/dilution/top")
    def top_dilution(limit: int = 20):
        return [f.model_dump() for f in db.parquet.query_top_dilution(limit)]

    @app.get("/alerts/feed")
    def alerts_feed(limit: int = 50):
        return db.get_alerts_feed(limit)

    @app.get("/filings/all")
    def all_filings(limit: int = 100):
        return [f.model_dump() for f in db.parquet.get_all_filings(limit)]

    @app.get("/search")
    def search(q: str, limit: int = 10):
        return db.parquet.search_companies(q, limit)

    @app.post("/scan/{ticker}")
    def scan_ticker_api(ticker: str, max_filings: int = 30):
        from pipeline import ScanPipeline
        result = ScanPipeline().scan_ticker(ticker, run_rag=False, max_filings=max_filings)
        return result.model_dump()

    @app.get("/screener/gap")
    def gap_screener(sort_type: str = "gainers", min_gap: float = 25.0, min_price: float = 0.30, limit: int = 30):
        from screener import GapScreener
        return GapScreener().scan(sort_type=sort_type, min_gap=min_gap, min_price=min_price, max_results=limit)

    def _risk(filings, profile=None) -> RiskAssessment:
        if not filings:
            return RiskAssessment()
        max_d = max((f.dilution_percentage or 0 for f in filings), default=0)
        has_w = any(f.warrants_found for f in filings)
        max_shelf = max((f.shelf_amount_usd or 0 for f in filings), default=0)
        # Count capital-raising filings (S-1, S-3, 424Bx)
        offering_forms = sum(1 for f in filings if f.form_type and (
            f.form_type.startswith("S-") or f.form_type.startswith("424B")
        ))
        stock_price = profile.price if profile and profile.price else 0
        cash = (profile.cash_per_share or 0) if profile else 0
        # offering_ability: shelf size
        offering_ability = RiskLevel.HIGH if max_shelf > 50_000_000 else RiskLevel.MEDIUM if max_shelf > 10_000_000 else RiskLevel.LOW
        # offering_frequency: number of offering filings
        offering_frequency = RiskLevel.HIGH if offering_forms >= 6 else RiskLevel.MEDIUM if offering_forms >= 3 else RiskLevel.LOW
        # dilution: consider pct first, else warrants + offerings as proxy
        if max_d >= 20:
            dilution = RiskLevel.HIGH
        elif max_d >= 10:
            dilution = RiskLevel.MEDIUM
        elif has_w and offering_forms >= 2:
            dilution = RiskLevel.HIGH
        elif has_w and offering_forms > 0:
            dilution = RiskLevel.MEDIUM
        elif offering_forms >= 3:
            dilution = RiskLevel.MEDIUM
        else:
            dilution = RiskLevel.LOW
        # cash_need: cash/share + offering activity
        if cash < 0.50:
            cash_need = RiskLevel.HIGH
        elif cash < 2.0 and offering_forms > 0:
            cash_need = RiskLevel.HIGH
        elif cash < 3.0 and has_w and offering_forms > 0:
            cash_need = RiskLevel.MEDIUM
        elif cash < 3.0:
            cash_need = RiskLevel.MEDIUM if has_w else RiskLevel.LOW
        elif has_w and offering_forms > 0:
            cash_need = RiskLevel.MEDIUM
        else:
            cash_need = RiskLevel.LOW
        # warrant_exercise: contextual without warrants_detail access
        warrant_exercise = RiskLevel.LOW
        if has_w:
            # Low stock price → warrants likely OTM (stock has been diluted down)
            if stock_price < 1.0:
                warrant_exercise = RiskLevel.LOW
            elif stock_price < 5.0 and offering_forms >= 3:
                warrant_exercise = RiskLevel.MEDIUM
            elif stock_price < 5.0 and offering_forms >= 1:
                warrant_exercise = RiskLevel.MEDIUM if has_w else RiskLevel.LOW
            elif offering_forms >= 3:
                warrant_exercise = RiskLevel.MEDIUM
            else:
                warrant_exercise = RiskLevel.LOW
        # overall: primarily based on ability + frequency
        if offering_ability == RiskLevel.HIGH or offering_frequency == RiskLevel.HIGH:
            overall_offering_risk = RiskLevel.HIGH
        elif offering_ability == RiskLevel.MEDIUM or offering_frequency == RiskLevel.MEDIUM:
            overall_offering_risk = RiskLevel.MEDIUM
        else:
            overall_offering_risk = RiskLevel.LOW
        return RiskAssessment(
            offering_ability=offering_ability,
            offering_frequency=offering_frequency,
            dilution=dilution,
            cash_need=cash_need,
            overall_offering_risk=overall_offering_risk,
            warrant_exercise=warrant_exercise,
        )

    def _insights(filings, profile, risk) -> list:
        """Generate insights array from filing data for the frontend."""
        result = []
        seen = set()
        def add(category, severity, title, body, source_form, date):
            key = str(category) + str(title)
            if key in seen:
                return
            seen.add(key)
            result.append({
                "id": len(result) + 1,
                "category": category,
                "severity": severity,
                "title": title,
                "body": body,
                "source_form": source_form,
                "date": date,
            })
        for f in filings:
            d = f.filed_date.isoformat() if hasattr(f.filed_date, 'isoformat') else str(f.filed_date)
            pct = f.dilution_percentage
            if pct and pct >= 10:
                s = "high" if pct >= 20 else "medium"
                add("Dilution Risk", s,
                    f"Dilución estimada del {pct:.1f}% en {f.form_type}",
                    f"El filing {f.form_type} del {d} indica una dilución estimada de {pct:.1f}% sobre shares outstanding actuales.",
                    f.form_type, d)
            if f.has_atm:
                add("Dilution Risk", "high",
                    "ATM offering provision activo",
                    "El filing contiene una cláusula de at-the-market offering que permite la emisión discrecional de acciones.",
                    f.form_type, d)
            if f.has_full_ratchet:
                add("Anti-Dilution", "high",
                    "Full ratchet anti-dilution detectado",
                    "Full ratchet anti-dilution provision activa: futuras rondas por debajo del precio actual ajustarán shares a favor del inversor.",
                    f.form_type, d)
            if f.warrants_found:
                add("Warrants", "medium" if not f.has_prefunded_warrants else "high",
                    "Warrants detectados en filing SEC",
                    "Se detectaron warrants en el filing. Revise el detalle del documento para términos específicos (ejercicio, expiración).",
                    f.form_type, d)
            if f.shelf_amount_usd and f.shelf_amount_usd >= 10_000_000:
                add("Dilution Risk", "high",
                    f"Shelf de ${f.shelf_amount_usd/1_000_000:,.0f}M activo",
                    f"Shelf registration por ${f.shelf_amount_usd/1_000_000:,.0f}M. Potencial de dilución significativo si se utiliza completamente.",
                    f.form_type, d)
        if risk:
            for level, label, cat in [
                (risk.dilution, "Dilution", "Dilution Risk"),
                (risk.warrant_exercise, "Warrants", "Warrants"),
                (risk.offering_ability, "Offering", "Dilution Risk"),
            ]:
                if level == RiskLevel.HIGH:
                    add(cat, "high", f"Riesgo de {label} alto",
                        f"El análisis de riesgo clasifica {label} como nivel alto. Monitorear actualizaciones y nuevos filings.",
                        "Risk Assessment", "")
        cash = profile.cash_per_share
        if cash and cash < 1:
            add("Cash Runway", "medium",
                f"Cash per share bajo (${cash:.2f})",
                f"Efectivo disponible por acción es de ${cash:.2f}. Podría indicar necesidad de capital en próximos trimestres.",
                "Financial Data", "")
        return result

    def _research_summary(ticker, filings, profile, risk, insights) -> str:
        """Generate a one-paragraph research summary from available data."""
        parts = []
        n_filings = len(filings)
        if n_filings > 0:
            forms = ", ".join(sorted(set(f.form_type for f in filings)))
            parts.append(f"{ticker} has {n_filings} recent filings ({forms}).")

        high_risk = [f for f in filings if f.risk_level == RiskLevel.HIGH]
        warrant_filings = [f for f in filings if f.warrants_found]
        atm_filings = [f for f in filings if f.has_atm]
        if high_risk:
            parts.append(f"{len(high_risk)} filing(s) flagged HIGH dilution risk.")
        if warrant_filings:
            parts.append(f"Warrants detected in {len(warrant_filings)} filing(s).")
        if atm_filings:
            parts.append(f"ATM provisions active in {len(atm_filings)} filing(s).")

        max_dil = max((f.dilution_percentage or 0 for f in filings), default=0)
        if max_dil >= 10:
            parts.append(f"Max estimated dilution: {max_dil:.1f}%.")

        if risk:
            high_risks = []
            if risk.dilution == RiskLevel.HIGH:
                high_risks.append("dilution")
            if risk.warrant_exercise == RiskLevel.HIGH:
                high_risks.append("warrant exercise")
            if risk.offering_ability == RiskLevel.HIGH:
                high_risks.append("offering capacity")
            if high_risks:
                parts.append(f"High risk flags: {' & '.join(high_risks)}.")

        p = profile
        if p and p.cash_per_share:
            parts.append(f"Cash per share: ${p.cash_per_share:.2f}.")
        if p and p.short_percent_float:
            parts.append(f"Short interest: {p.short_percent_float:.2f}%.")
        if p and p.employees:
            parts.append(f"Employees: {p.employees}.")

        if insights:
            high_ins = [i for i in insights if i["severity"] == "high"]
            if high_ins:
                parts.append(f"{len(high_ins)} high-priority insight(s) available.")

        if not parts:
            return f"No research data available for {ticker}. Run a scan to generate analysis."

        return " ".join(parts)

    def _merge_warrants(filings) -> list:
        """Merge warrant details from all filings, dedup by type."""
        seen = set()
        result = []
        for f in filings:
            for w in getattr(f, 'warrants_detail', []) or []:
                key = w.get("type", "Unknown")
                if key in seen:
                    continue
                seen.add(key)
                result.append({
                    "type": w.get("type", "Detected"),
                    "count": w.get("count"),
                    "exercise_price": w.get("exercise_price"),
                    "expiration": w.get("expiration", "See filing"),
                    "in_the_money": None,
                })
        if not result:
            result.append({
                "type": "Detected", "count": None,
                "exercise_price": None, "expiration": "See filing", "in_the_money": None,
            })
        return result

    def _dilution_detail(filings, profile, risk) -> dict:
        """Build dilution detail object for the frontend."""
        max_dil = max((f.dilution_percentage or 0 for f in filings), default=0)
        shelf_filings = [f for f in filings if (f.shelf_amount_usd or 0) > 0]
        shelf_active = len(shelf_filings) > 0
        shelf_total = max((f.shelf_amount_usd or 0 for f in shelf_filings), default=0)
        atm_active = any(f.has_atm for f in filings)
        warrant_active = any(f.warrants_found for f in filings)

        flags = {
            "warrants_found": warrant_active,
            "has_atm": atm_active,
            "has_full_ratchet": any(f.has_full_ratchet for f in filings),
            "has_prefunded_warrants": any(f.has_prefunded_warrants for f in filings),
        }

        events = []
        for f in sorted(filings, key=lambda x: x.filed_date, reverse=True)[:10]:
            d = f.filed_date.isoformat() if hasattr(f.filed_date, 'isoformat') else str(f.filed_date)
            desc = f.summary or f"{f.form_type} filing"
            events.append({
                "date": d,
                "type": f.form_type,
                "description": desc[:120],
                "impact_pct": f.dilution_percentage,
            })

        risk_lvl = "HIGH" if max_dil >= 20 else "MEDIUM" if max_dil >= 10 else "LOW"
        if risk and risk.dilution:
            risk_lvl = risk.dilution.value

        p = profile
        return {
            "estimated_dilution_pct": max_dil or None,
            "risk_level": risk_lvl,
            "shelf": {
                "active": shelf_active,
                "capacity_usd": shelf_total or None,
                "remaining_usd": shelf_total * 0.65 if shelf_active else None,
                "expiration": str(shelf_filings[0].filed_date) if shelf_filings else None,
            },
            "atm": {
                "active": atm_active,
                "capacity_usd": shelf_total * 0.3 if atm_active else None,
                "used_usd": None,
                "agent": "TBA",
            },
            "warrants": _merge_warrants(filings) if warrant_active else [],


            "flags": flags,
            "events": events,
            "share_structure": {
                "float": p.float_shares,
                "outstanding": p.shares_outstanding,
                "fully_diluted": p.shares_outstanding * 1.35 if p.shares_outstanding else None,
                "cash_months": None,
            },
        }

    uvicorn.run(app, host=settings.api_host, port=args.port or settings.api_port)
    return 0


def cmd_dashboard(_: argparse.Namespace) -> int:
    """DEPRECATED — use the Next.js frontend (npm run dev in frontend/) instead."""
    logger.warning("Streamlit dashboard is deprecated. Use the Next.js frontend (cd frontend && npm run dev) instead.")
    import streamlit as st
    from apis.data_enrichment import DataEnrichment
    from db.parquet_db import ParquetDB
    from pipeline import ScanPipeline
    from rag.prompts import list_prompts

    st.set_page_config(page_title="SEC Dilution Tracker", layout="wide")
    st.title("SEC Dilution Tracker + RAG")
    db = ParquetDB()
    ticker = st.sidebar.text_input("Ticker", "AAPL").upper()
    if st.sidebar.button("Scan Ticker"):
        with st.spinner("Scanning..."):
            try:
                r = ScanPipeline().scan_ticker(ticker, run_rag=False)
                st.success(f"Processed {r.filings_processed} filings")
                st.dataframe([f.model_dump() for f in r.filings])
            except Exception as e:
                st.error(str(e))
    st.subheader("Top Dilution Risks")
    st.dataframe([f.model_dump() for f in db.query_top_dilution(15)])
    return 0


def cmd_telegram(args: argparse.Namespace) -> int:
    from telegram_bot import run_telegram_bot
    run_telegram_bot(daemon=args.daemon)
    return 0


def cmd_mode(_: argparse.Namespace) -> int:
    from config import get_settings
    from db.database import Database
    s = get_settings()
    db = Database()
    print(f"Mode:           {db.get_mode()}")
    print(f"Storage:        local (Parquet + SQLite)")
    print(f"SQLite path:    {s.sqlite_db_path}")
    print(f"Telegram token: {'set' if s.telegram_bot_token else 'NOT SET'}")
    print(f"Admin chat ID:  {s.telegram_admin_chat_id or 'NOT SET'}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Dilucion Data")
    sub = p.add_subparsers(dest="command")

    s = sub.add_parser("scan", help="Scan ticker or URL")
    s.add_argument("target", help="Ticker symbol or SEC URL")
    s.add_argument("--ask", help="Custom RAG question")
    s.add_argument("--prompt", default="dilution", help="Prompt name or custom question")
    s.set_defaults(func=lambda a: cmd_scan_url(a) if a.target.startswith("http") else cmd_scan_ticker(a))

    sv = sub.add_parser("serve", help="Start API server")
    sv.add_argument("--port", type=int, default=None)
    sv.set_defaults(func=cmd_serve)

    m = sub.add_parser("monitor", help="RSS/daily SEC monitor")
    m.add_argument("--daily", action="store_true", help="Run daily index scan once")
    m.add_argument("--once", action="store_true", help="Poll RSS once")
    m.add_argument("--interval", type=int, default=120)
    m.set_defaults(func=cmd_monitor)

    sr = sub.add_parser("search", help="SEC full-text search")
    sr.add_argument("--query", "-q", help="Search term")
    sr.add_argument("--limit", type=int, default=20)
    sr.set_defaults(func=cmd_search)

    fl = sub.add_parser("filings", help="List filings for CIK")
    fl.add_argument("cik")
    fl.add_argument("--limit", type=int, default=30)
    fl.set_defaults(func=cmd_filings)

    rp = sub.add_parser("report", help="Dilution risk report")
    rp.add_argument("--limit", type=int, default=20)
    rp.set_defaults(func=cmd_report)

    db = sub.add_parser("db", help="Database operations")
    db_sub = db.add_subparsers(dest="db_cmd")
    db_sub.add_parser("init").set_defaults(func=cmd_db_init)
    db_sub.add_parser("stats").set_defaults(func=cmd_db_stats)

    rg = sub.add_parser("rag", help="RAG query on ticker or URL")
    rg.add_argument("target", help="Ticker or SEC URL")
    rg.add_argument("--prompt", default="dilution")
    rg.add_argument("--question", help="Custom question")
    rg.set_defaults(func=cmd_rag)

    tk = sub.add_parser("tickers", help="Ticker list")
    tk_sub = tk.add_subparsers(dest="tickers_cmd")
    tk_sub.add_parser("refresh").set_defaults(func=cmd_tickers_refresh)

    sub.add_parser("dashboard", help="Streamlit dashboard").set_defaults(func=cmd_dashboard)

    tg = sub.add_parser("telegram", help="Start Telegram bot")
    tg.add_argument("--daemon", action="store_true", help="Also run RSS scanner in background")
    tg.set_defaults(func=cmd_telegram)

    sub.add_parser("mode", help="Show private vs SaaS mode").set_defaults(func=cmd_mode)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 1
    if args.command == "db" and not getattr(args, "db_cmd", None):
        parser.parse_args(["db", "init"])
        return cmd_db_init(args)
    func = getattr(args, "func", None)
    return func(args) if func else (parser.print_help() or 1)


if __name__ == "__main__":
    sys.exit(main())
