"""Local data layer: Parquet files + SQLite."""

from __future__ import annotations

import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

from config import get_settings
from db.parquet_db import ParquetDB
from models import Company, FilingDilution, RAGResponse, RiskLevel

logger = logging.getLogger(__name__)

RISK_TO_SQL = {
    RiskLevel.LOW: "LOW",
    RiskLevel.MEDIUM: "MEDIUM",
    RiskLevel.HIGH: "HIGH",
}


class SQLiteBackend:
    """SQLite storage for alerts, watchlist, RAG history, bot state."""

    def __init__(self, db_path: Path, schema_path: Path) -> None:
        self.db_path = db_path
        self.schema_path = schema_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def _conn(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_schema(self) -> None:
        sql = self.schema_path.read_text(encoding="utf-8")
        with self._conn() as conn:
            conn.executescript(sql)
        logger.info("SQLite schema initialized at %s", self.db_path)

    def upsert_company(self, company: Company) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO companies (cik, ticker, company_name, sector, float_shares, shares_outstanding)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(cik) DO UPDATE SET
                    ticker=excluded.ticker,
                    company_name=excluded.company_name,
                    sector=excluded.sector,
                    float_shares=excluded.float_shares,
                    shares_outstanding=excluded.shares_outstanding
                """,
                (
                    company.cik,
                    company.ticker.upper(),
                    company.company_name,
                    company.sector,
                    company.float_shares,
                    company.shares_outstanding,
                ),
            )

    def insert_alert(self, filing: FilingDilution) -> None:
        risk = RISK_TO_SQL.get(filing.risk_level, filing.risk_level.value if filing.risk_level else None)
        if risk == "Med":
            risk = "MEDIUM"
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO filings_history (
                    cik, ticker, form_type, accession_number, filed_date,
                    shelf_amount_usd, dilution_percentage, has_atm, has_full_ratchet,
                    has_prefunded_warrants, warrants_found, risk_level, filing_url, summary
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(accession_number) DO UPDATE SET
                    dilution_percentage=excluded.dilution_percentage,
                    shelf_amount_usd=excluded.shelf_amount_usd,
                    has_atm=excluded.has_atm,
                    has_full_ratchet=excluded.has_full_ratchet,
                    has_prefunded_warrants=excluded.has_prefunded_warrants,
                    risk_level=excluded.risk_level,
                    summary=excluded.summary
                """,
                (
                    filing.cik,
                    filing.ticker.upper() if filing.ticker else None,
                    filing.form_type,
                    filing.accession_number,
                    filing.filed_date.isoformat(),
                    filing.shelf_amount_usd,
                    filing.dilution_percentage,
                    int(filing.has_atm),
                    int(filing.has_full_ratchet),
                    int(filing.has_prefunded_warrants),
                    int(filing.warrants_found),
                    risk,
                    filing.source_url,
                    filing.summary,
                ),
            )

    def insert_rag(
        self,
        cik: str,
        accession: str,
        question: str,
        response: RAGResponse,
    ) -> None:
        chunks = json.dumps([c.content[:500] for c in response.citations[:5]])
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO rag_analyses (cik, accession_number, question, answer, source_chunks, model_used)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (cik, accession, question, response.answer[:10000], chunks, response.model),
            )

    def get_top(self, limit: int = 10) -> List[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT * FROM filings_history
                ORDER BY CASE WHEN dilution_percentage IS NULL THEN 1 ELSE 0 END,
                         dilution_percentage DESC, created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_recent_alerts(self, hours: int = 24, limit: int = 50) -> List[dict]:
        since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT * FROM filings_history
                WHERE created_at >= ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (since, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def add_watchlist(self, chat_id: int, cik: str, ticker: str) -> bool:
        with self._conn() as conn:
            try:
                conn.execute(
                    "INSERT INTO watchlist (chat_id, cik, ticker) VALUES (?, ?, ?)",
                    (chat_id, cik, ticker.upper()),
                )
                return True
            except sqlite3.IntegrityError:
                return False

    def remove_watchlist(self, chat_id: int, ticker: str) -> bool:
        with self._conn() as conn:
            cur = conn.execute(
                "DELETE FROM watchlist WHERE chat_id=? AND ticker=?",
                (chat_id, ticker.upper()),
            )
            return cur.rowcount > 0

    def get_watchlist(self, chat_id: int) -> List[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT ticker, cik, added_at FROM watchlist WHERE chat_id=? ORDER BY added_at",
                (chat_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_all_watchers_for_ticker(self, ticker: str) -> List[int]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT DISTINCT chat_id FROM watchlist WHERE ticker=?",
                (ticker.upper(),),
            ).fetchall()
        return [int(r["chat_id"]) for r in rows]

    def set_state(self, key: str, value: str) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO bot_state (key, value, updated_at) VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
                """,
                (key, value, datetime.now(timezone.utc).isoformat()),
            )

    def get_state(self, key: str) -> Optional[str]:
        with self._conn() as conn:
            row = conn.execute("SELECT value FROM bot_state WHERE key=?", (key,)).fetchone()
            return row["value"] if row else None

    def stats(self) -> Dict[str, Any]:
        with self._conn() as conn:
            companies = conn.execute("SELECT COUNT(*) AS n FROM companies").fetchone()["n"]
            filings = conn.execute("SELECT COUNT(*) AS n FROM filings_history").fetchone()["n"]
            watchlist = conn.execute("SELECT COUNT(*) AS n FROM watchlist").fetchone()["n"]
            avg = conn.execute(
                "SELECT AVG(dilution_percentage) AS a FROM filings_history WHERE dilution_percentage IS NOT NULL"
            ).fetchone()["a"]
        return {
            "mode": "sqlite",
            "companies": companies,
            "filings": filings,
            "watchlist_entries": watchlist,
            "avg_dilution": round(avg, 2) if avg else None,
        }


class Database:
    """Parquet lake + SQLite for local-only storage."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.parquet = ParquetDB()
        self.parquet.inicializar()
        schema = Path(__file__).parent / "schema.sqlite.sql"
        self.sqlite = SQLiteBackend(self.settings.sqlite_db_path, schema)
        self.sqlite.init_schema()

    def init(self) -> None:
        self.parquet.inicializar()
        self.sqlite.init_schema()
        logger.info("Database ready — Parquet + SQLite")

    def get_mode(self) -> str:
        return "sqlite"

    def save_company(self, company: Company) -> None:
        self.parquet.upsert_company(company)
        self.sqlite.upsert_company(company)

    def save_dilution_alert(self, filing: FilingDilution) -> None:
        self.parquet.upsert_filing(filing)
        self.sqlite.insert_alert(filing)

    def save_rag_analysis(
        self,
        cik: str,
        accession: str,
        question: str,
        response: RAGResponse,
    ) -> None:
        self.sqlite.insert_rag(cik, accession, question, response)

    def get_top(self, limit: int = 10) -> List[dict]:
        rows = self.sqlite.get_top(limit)
        if rows:
            return rows
        return [f.model_dump() for f in self.parquet.query_top_dilution(limit)]

    def get_recent_alerts(self, hours: int = 24, limit: int = 50) -> List[dict]:
        rows = self.sqlite.get_recent_alerts(hours, limit)
        if rows:
            return rows
        return [f.model_dump() for f in self.parquet.query_top_dilution(limit)]

    def get_alerts_feed(self, limit: int = 50) -> List[dict]:
        return self.get_recent_alerts(hours=168, limit=limit)

    def add_watchlist(self, chat_id: int, cik: str, ticker: str) -> bool:
        return self.sqlite.add_watchlist(chat_id, cik, ticker)

    def remove_watchlist(self, chat_id: int, ticker: str) -> bool:
        return self.sqlite.remove_watchlist(chat_id, ticker)

    def get_watchlist(self, chat_id: int) -> List[dict]:
        return self.sqlite.get_watchlist(chat_id)

    def get_watchers_for_ticker(self, ticker: str) -> List[int]:
        return self.sqlite.get_all_watchers_for_ticker(ticker)

    def set_bot_state(self, key: str, value: str) -> None:
        self.sqlite.set_state(key, value)

    def get_bot_state(self, key: str) -> Optional[str]:
        return self.sqlite.get_state(key)

    def stats(self) -> Dict[str, Any]:
        base = self.parquet.report_summary()
        base["mode"] = "sqlite"
        base["storage"] = "local"
        base.update(self.sqlite.stats())
        return base
