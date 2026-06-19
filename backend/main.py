#!/usr/bin/env python3
"""SEC Dilution Tracker + AskEdgar RAG — unified CLI and API server."""

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
    print("Database initialized (Parquet + optional Supabase).")
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
    from fastapi import FastAPI, HTTPException
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
        allow_origins=[settings.frontend_url, "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
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
    def rag_endpoint(body: RagBody):
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
        candles = enrichment.polygon.get_candles(ticker)
        return {
            "profile": profile.model_dump(),
            "filings": [f.model_dump() for f in filings],
            "candles": [c.model_dump() for c in candles],
            "risk": _risk(filings).model_dump(),
        }

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
    def scan_ticker_api(ticker: str):
        from pipeline import ScanPipeline
        result = ScanPipeline().scan_ticker(ticker, run_rag=False)
        return result.model_dump()

    def _risk(filings) -> RiskAssessment:
        if not filings:
            return RiskAssessment()
        max_d = max((f.dilution_percentage or 0 for f in filings), default=0)
        has_w = any(f.warrants_found for f in filings)
        has_shelf = any((f.shelf_amount_usd or 0) > 10_000_000 for f in filings)
        def lvl(v, lo, hi):
            return RiskLevel.HIGH if v >= hi else RiskLevel.MEDIUM if v >= lo else RiskLevel.LOW
        return RiskAssessment(
            offering_ability=RiskLevel.HIGH if has_shelf else RiskLevel.MEDIUM,
            dilution=lvl(max_d, 10, 20),
            cash_need=RiskLevel.MEDIUM,
            warrant_exercise=RiskLevel.HIGH if has_w else RiskLevel.LOW,
        )

    uvicorn.run(app, host=settings.api_host, port=args.port or settings.api_port)
    return 0


def cmd_dashboard(_: argparse.Namespace) -> int:
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
    print(f"PRIVATE_MODE:   {s.private_mode}")
    print(f"Supabase:       {'yes' if db.supabase_enabled else 'no'}")
    print(f"SQLite path:    {s.sqlite_db_path}")
    print(f"Telegram token: {'set' if s.telegram_bot_token else 'NOT SET'}")
    print(f"Admin chat ID:  {s.telegram_admin_chat_id or 'NOT SET'}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="SEC Dilution Tracker + AskEdgar RAG")
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
