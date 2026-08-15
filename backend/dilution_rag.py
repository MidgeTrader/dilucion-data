"""RAG-based dilution data extraction — OpenAI embeddings + DeepSeek LLM.

Replaces fragile regex extraction with AI-powered structured data extraction
from SEC filings. Caches results in SQLite to avoid re-processing.
"""

from __future__ import annotations

import json
import logging
import re
import sqlite3
import hashlib
import threading
from datetime import datetime
from typing import Optional

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import get_settings
from parsers.sec_parser import SECParser, ParsedFiling

logger = logging.getLogger(__name__)

# ─── Structured JSON Extraction Prompts ──────────────────────────────────

JSON_SYSTEM_PROMPT = """You are a financial analyst extracting structured data from SEC filings.
Return ONLY valid JSON. No explanation, no markdown, no extra text.
If data is not found, use null or empty arrays."""

EXTRACT_WARRANTS = """Look for OUTSTANDING warrants (warrants that have already been issued and are currently exercisable). Ignore generic descriptions of what warrants "may" be offered in the future.
Extract all warrant issues found. Return a JSON array. Each warrant object:
{
  "issue_label": "string (e.g. 'Outstanding Warrants', 'Series A', 'Pre-Funded', '2024 Warrants')",
  "remaining": number (share count of outstanding warrants, integer or null),
  "exercise_price": number (USD per share or null),
  "owners": ["string list of investor names if mentioned"],
  "protection": "Full Ratchet" | "Customary Anti-Dilution" | "N/A"
}
IMPORTANT: Look for phrases like "outstanding warrants", "warrants outstanding", "shares issuable upon exercise of outstanding warrants". Include the count and price even if owners are not listed."""

EXTRACT_CASH = """Extract cash position data from this financial filing.
Return a JSON object:
{
  "cash_estimated": number (USD, or null),
  "quarterly_burn": number (USD operating cash outflow per quarter, or null),
  "months_of_cash": number (or null),
  "going_concern": boolean,
  "cash_balance_filing_date": "string (date or null)"
}"""

EXTRACT_OFFERING = """Extract pending/public offering details from this SEC filing.
Return a JSON object:
{
  "type": "Best Efforts Public Offering" | "Firm Commitment" | "Registered Direct Offering" | "Public Offering" | null,
  "shares": number (integer or null),
  "price": number (USD per share or null),
  "warrants": number (warrants included or null),
  "date": "string (date or null)",
  "filing_type": "string (form type or null)"
}"""

EXTRACT_CONVERTIBLES = """Extract all convertible notes from this SEC filing.
Return a JSON array. Each convertible:
{
  "issue_label": "string",
  "total": number (USD principal or null),
  "remaining": number (USD remaining or null),
  "conversion_price": number (USD or null),
  "protection": "Full Ratchet" | "N/A" | null,
  "owner": "string (holder name or null)"
}"""

EXTRACT_ATM = """Does this filing mention an At-The-Market (ATM) offering/program?
Return a JSON array. Each ATM program:
{
  "name": "string",
  "remaining": number (USD remaining or null),
  "total_amt": number (USD total or null),
  "bank": "string (agent name or null)",
  "date": "string (date or null)"
}"""

EXTRACT_SHELF = """Extract shelf registration details from this S-3 filing.
Return a JSON object:
{
  "active": true,
  "total_offering": number (USD total shelf amount or null),
  "raisable_total": number (USD currently raisable or null),
  "amt_sold_last_12m": number (USD sold in last 12 months or null),
  "expiration": "string (date or null)"
}"""

EXTRACT_EQUITY_LINES = """Does this filing mention an equity line / SPA / committed equity facility?
Return a JSON array. Each equity line:
{
  "total_amt": number (USD or null),
  "shares": number (shares or null),
  "atm_remaining": number (USD remaining or null),
  "pricing_mechanism": "string (description or null)",
  "date": "string (date or null)"
}"""


class DilutionRAGExtractor:
    """Extract structured dilution data from SEC filings using RAG.

    OpenAI embeddings → vector store → DeepSeek JSON extraction.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.settings.validate_rag_keys()
        self.parser = SECParser()
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
        )
        self.embeddings = OpenAIEmbeddings(
            model=self.settings.embedding_model,
            api_key=self.settings.openai_api_key,
        )
        self._init_cache()

    def _init_cache(self) -> None:
        """SQLite cache for extracted results (thread-local connection)."""
        path = self.settings.data_dir / "extraction_cache.sqlite"
        self._cache_path = str(path)
        self._cache_local = threading.local()
        try:
            # Initialize schema in the current thread
            conn = self._get_cache_conn()
            conn.execute("""
                CREATE TABLE IF NOT EXISTS extraction_cache (
                    url_hash TEXT PRIMARY KEY,
                    extraction_type TEXT,
                    result_json TEXT,
                    model TEXT,
                    created_at TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_extraction_type ON extraction_cache(extraction_type)")
        except Exception as exc:
            logger.warning("Cache init failed (non-fatal): %s", exc)

    def _get_cache_conn(self) -> Optional[sqlite3.Connection]:
        """Thread-local cache connection — one per thread."""
        conn: Optional[sqlite3.Connection] = getattr(self._cache_local, "conn", None)
        if conn is None:
            try:
                conn = sqlite3.connect(self._cache_path, timeout=10)
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA busy_timeout=5000")
                self._cache_local.conn = conn
            except Exception as exc:
                logger.warning("Cache conn failed: %s", exc)
                return None
        return conn

    def _cache_key(self, url: str, extraction_type: str) -> str:
        return hashlib.sha256(f"{url}:{extraction_type}".encode()).hexdigest()[:32]

    def _cache_get(self, url: str, extraction_type: str) -> Optional[dict]:
        conn = self._get_cache_conn()
        if conn is None:
            return None
        try:
            key = self._cache_key(url, extraction_type)
            row = conn.execute(
                "SELECT result_json FROM extraction_cache WHERE url_hash = ? AND extraction_type = ?",
                (key, extraction_type)
            ).fetchone()
            if row:
                return json.loads(row[0])
        except Exception:
            pass
        return None

    def _cache_set(self, url: str, extraction_type: str, data: dict) -> None:
        conn = self._get_cache_conn()
        if conn is None:
            return
        try:
            key = self._cache_key(url, extraction_type)
            conn.execute(
                "INSERT OR REPLACE INTO extraction_cache VALUES (?, ?, ?, ?, ?)",
                (key, extraction_type, json.dumps(data), self.settings.deepseek_model,
                 datetime.utcnow().isoformat())
            )
            # Sin commit el INSERT queda solo en la conexión thread-local y se
            # pierde al reiniciar el proceso — la caché nunca persistía.
            conn.commit()
        except Exception as exc:
            logger.debug("Cache set failed: %s", exc)

    def _get_llm(self) -> ChatOpenAI:
        return ChatOpenAI(
            model=self.settings.deepseek_model,
            temperature=0.0,
            api_key=self.settings.deepseek_api_key,
            base_url="https://api.deepseek.com/v1",
        )

    def _vectorize_filing(self, parsed: ParsedFiling) -> Chroma:
        """Create or retrieve Chroma vector store for a filing."""
        accession = parsed.accession_number or ""
        safe = re.sub(r'[^a-zA-Z0-9.-]', '_', (accession[-40:] or parsed.url[-40:]).replace('/', '_'))
        safe = safe[:255]  # ChromaDB max collection name length
        coll = f"dr_{safe}"
        existing = Chroma(
            collection_name=coll,
            embedding_function=self.embeddings,
            persist_directory=str(self.settings.chroma_dir),
        )
        try:
            existing_count = existing._collection.count()
        except Exception:
            existing_count = 0
        if existing_count > 0:
            logger.info("Reusing existing vector store (%d docs) for %s", existing_count, coll)
            return existing
        chunks = self.splitter.split_text(parsed.text)
        meta = {"source_url": parsed.url, "form_type": parsed.form_type or ""}
        docs = [Document(page_content=c, metadata={**meta, "chunk_index": i}) for i, c in enumerate(chunks)]
        return Chroma.from_documents(
            documents=docs, embedding=self.embeddings,
            collection_name=coll, persist_directory=str(self.settings.chroma_dir),
        )

    def _query_json(self, parsed: ParsedFiling, question: str):
        """Query DeepSeek with RAG context and parse JSON response."""
        try:
            vs = self._vectorize_filing(parsed)
            count = vs._collection.count()
            logger.info("RAG query on %s (form=%s, chunks=%d)", parsed.url[-60:], parsed.form_type, count)
            if count == 0:
                logger.warning("Empty vector store for %s", parsed.url[-60:])
                return None

            retriever = vs.as_retriever(search_kwargs={"k": 10})
            llm = self._get_llm()
            prompt = ChatPromptTemplate.from_messages([
                ("system", JSON_SYSTEM_PROMPT),
                ("human", "Context:\n{context}\n\n{input}")
            ])
            docs = retriever.invoke(question)
            if not docs:
                logger.info("No relevant chunks retrieved")
                return None

            context = "\n\n---\n\n".join(d.page_content[:2000] for d in docs)
            response = llm.invoke(prompt.format_messages(context=context, input=question))
            text = response.content if hasattr(response, "content") else str(response)
            logger.info("DeepSeek response (%d chars): %s", len(text), text[:200])
            result = self._parse_json(text)
            if result is not None:
                return result
            logger.warning("Could not parse JSON from DeepSeek response: %s", text[:300])
            return None
        except Exception as exc:
            logger.warning("RAG extraction failed for %s: %s", parsed.url[-60:], exc)
            return None

    def _parse_json(self, text: str) -> Optional[dict]:
        """Extract JSON from LLM response (handles code fences)."""
        text = text.strip()
        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        # Try extracting from markdown code fence
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if m:
            try:
                return json.loads(m.group(1).strip())
            except json.JSONDecodeError:
                pass
        # Try to find the first { or [ and parse from there
        for start_char, end_char in [("{", "}"), ("[", "]")]:
            s = text.find(start_char)
            if s >= 0:
                e = text.rfind(end_char)
                if e > s:
                    try:
                        return json.loads(text[s:e+1])
                    except json.JSONDecodeError:
                        pass
        logger.warning("Could not parse JSON from: %s", text[:200])
        return None

    # ─── Public extraction methods ───────────────────────────────────────

    def extract_warrants(self, parsed: ParsedFiling) -> list[dict]:
        """Extract warrant issues from an offering filing."""
        cached = self._cache_get(parsed.url, "warrants")
        if cached:
            return cached
        result = self._query_json(parsed, EXTRACT_WARRANTS)
        data = result if isinstance(result, list) else (result if isinstance(result, dict) else [])
        if isinstance(data, dict):
            data = [data]
        # Validate each warrant
        valid = []
        for w in data:
            if w.get("remaining") and w["remaining"] > 0:
                valid.append(w)
        self._cache_set(parsed.url, "warrants", valid)
        return valid

    def extract_cash(self, parsed: ParsedFiling) -> Optional[dict]:
        """Extract cash position from a 10-Q/10-K filing."""
        cached = self._cache_get(parsed.url, "cash")
        if cached:
            return cached
        result = self._query_json(parsed, EXTRACT_CASH)
        if result and isinstance(result, dict):
            self._cache_set(parsed.url, "cash", result)
            return result
        return None

    def extract_offering(self, parsed: ParsedFiling) -> Optional[dict]:
        """Extract offering details from S-1 filing."""
        cached = self._cache_get(parsed.url, "offering")
        if cached:
            return cached
        result = self._query_json(parsed, EXTRACT_OFFERING)
        if result and isinstance(result, dict):
            self._cache_set(parsed.url, "offering", result)
            return result
        return None

    def extract_convertibles(self, parsed: ParsedFiling) -> list[dict]:
        """Extract convertible notes from 8-K filing."""
        cached = self._cache_get(parsed.url, "convertibles")
        if cached:
            return cached
        result = self._query_json(parsed, EXTRACT_CONVERTIBLES)
        data = result if isinstance(result, list) else []
        valid = [c for c in data if isinstance(c, dict) and c.get("total")]
        self._cache_set(parsed.url, "convertibles", valid)
        return valid

    def extract_atms(self, parsed: ParsedFiling) -> list[dict]:
        """Extract ATM programs from S-3/424B filing."""
        cached = self._cache_get(parsed.url, "atms")
        if cached:
            return cached
        result = self._query_json(parsed, EXTRACT_ATM)
        data = result if isinstance(result, list) else []
        valid = [a for a in data if isinstance(a, dict)]
        self._cache_set(parsed.url, "atms", valid)
        return valid

    def extract_shelf(self, parsed: ParsedFiling) -> Optional[dict]:
        """Extract shelf registration from S-3 filing."""
        cached = self._cache_get(parsed.url, "shelf")
        if cached:
            return cached
        result = self._query_json(parsed, EXTRACT_SHELF)
        if result and isinstance(result, dict):
            self._cache_set(parsed.url, "shelf", result)
            return result
        return None

    def extract_equity_lines(self, parsed: ParsedFiling) -> list[dict]:
        """Extract equity lines from 8-K/S-1 filing."""
        cached = self._cache_get(parsed.url, "equity_lines")
        if cached:
            return cached
        result = self._query_json(parsed, EXTRACT_EQUITY_LINES)
        data = result if isinstance(result, list) else []
        valid = [e for e in data if isinstance(e, dict)]
        self._cache_set(parsed.url, "equity_lines", valid)
        return valid

    HEADLINE_PROMPT = """Generate a short, descriptive one-line headline for this SEC filing.
Return ONLY a JSON object: {"headline": "string"}
The headline should describe what the filing is about. Examples:
- "IceCure Reports 70% Growth in Active U.S. Commercial Install Base"
- "At-the-Market Sales Agreement with A.G.P."
- "Annual report for fiscal year 2025"
- "Registration statement for resale of shares"
Make it informative but concise (max 120 chars)."""

    def generate_headline(self, url: str) -> Optional[str]:
        """Generate a rich headline for a filing using DeepSeek."""
        cached = self._cache_get(url, "headline")
        if cached and isinstance(cached, dict) and cached.get("headline"):
            return cached["headline"]
        try:
            parsed = self.parser.load_from_url(url)
            if not parsed or len(parsed.text) < 100:
                return None
            # Take first 4000 chars of text for context
            text = parsed.text[:4000]
            from langchain_openai import ChatOpenAI
            from langchain_core.prompts import ChatPromptTemplate
            llm = ChatOpenAI(model=self.settings.deepseek_model, temperature=0.0,
                            api_key=self.settings.deepseek_api_key, base_url="https://api.deepseek.com/v1")
            prompt = ChatPromptTemplate.from_messages([
                ("system", JSON_SYSTEM_PROMPT),
                ("human", "Filing text:\n{text}\n\n{input}")
            ])
            resp = llm.invoke(prompt.format_messages(text=text[:3000], input=self.HEADLINE_PROMPT))
            result = self._parse_json(resp.content if hasattr(resp, "content") else str(resp))
            if result and isinstance(result, dict) and result.get("headline"):
                self._cache_set(url, "headline", result)
                return result["headline"]
        except Exception as exc:
            logger.debug("Headline gen failed for %s: %s", url[-40:], exc)
        return None

    RESEARCH_PROMPT_BEFORE = """Eres un analista financiero especializado en small caps. Genera un reporte de investigacion en espanol sobre {ticker}.
Datos disponibles:
- {n_filings} filings recientes: {forms}
- Warrants detectados: {warrants_txt}
- ATMs activos: {atms_txt}
- Dilucion maxima estimada: {dil_pct}%
- Riesgos: {risks_txt}
- Cash por accion: ${cash}
- Short interest: {short}%
- Market cap: ${mkt_cap}
- Empleados: {employees}

Estructura:
**Resumen** — 2 lineas maximo
**Analisis de Dilucion y Riesgos** — 3 lineas maximo
Sin conclusion ni consejo.

Formato: usa ** para los encabezados, separados por linea en blanco. Texto conciso y directo."""

    def generate_research_report(self, ticker: str, data: dict) -> Optional[str]:
        """Generate a Spanish research report using DeepSeek."""
        cache_key = f"research_{ticker}"
        cached = self._cache_get(cache_key, "research")
        if cached and isinstance(cached, dict) and cached.get("report"):
            return cached["report"]
        try:
            profile = data.get("profile", {})
            risk = data.get("risk", {})
            n = len(data.get("filings", []))
            forms = sorted(set(f.get("form_type", "") for f in data.get("filings", [])))
            ws = sum(1 for f in data.get("filings", []) if f.get("warrants_found"))
            atms = sum(1 for f in data.get("filings", []) if f.get("has_atm"))
            dil = max((f.get("dilution_percentage", 0) or 0 for f in data.get("filings", [])), default=0)
            high_risks = [k for k, v in (risk or {}).items() if v == "High"]

            cash_raw = data.get("profile", {}).get("cash_per_share", None)
            short_raw = data.get("profile", {}).get("short_percent_float", None)
            mkt_cap_raw = data.get("profile", {}).get("market_cap", None)
            prompt_data = {
                "ticker": ticker,
                "n_filings": n,
                "forms": ", ".join(forms[:15]),
                "warrants_txt": f"Si en {ws} filing(s)" if ws else "No detectados",
                "atms_txt": f"Si en {atms} filing(s)" if atms else "No detectados",
                "dil_pct": f"{dil:.1f}",
                "risks_txt": ", ".join(high_risks) if high_risks else "Ninguno",
                "cash": f"${cash_raw:.2f}" if cash_raw else "N/A",
                "short": f"{short_raw:.2f}%" if short_raw else "N/A",
                "mkt_cap": f"${mkt_cap_raw/1e6:.1f}M" if mkt_cap_raw else "N/A",
                "employees": data.get("profile", {}).get("employees", "N/A"),
            }

            from langchain_openai import ChatOpenAI
            from langchain_core.prompts import ChatPromptTemplate
            llm = ChatOpenAI(model=self.settings.deepseek_model, temperature=0.0,
                            api_key=self.settings.deepseek_api_key, base_url="https://api.deepseek.com/v1")
            prompt_text = self.RESEARCH_PROMPT_BEFORE.format(**prompt_data)
            prompt = ChatPromptTemplate.from_messages([("system", "Eres un analista financiero."), ("human", prompt_text)])
            resp = llm.invoke(prompt.format_messages())
            text = resp.content if hasattr(resp, "content") else str(resp)
            text = text.strip().strip('"').strip("'")
            if text and len(text) > 50:
                self._cache_set(cache_key, "research", {"report": text})
                return text
        except Exception as exc:
            logger.warning("Research report failed for %s: %s", ticker, exc)
        return None

    def extract_all(self, url: str, form_type: str = "") -> dict:
        """Run all relevant extractions based on form type.

        Returns dict merged from all extractions.
        """
        parsed = self.parser.load_from_url(url)
        result = {"form_type": parsed.form_type or form_type, "url": url}

        if parsed.form_type in ("10-Q", "10-K"):
            if c := self.extract_cash(parsed):
                result["cash"] = c

        elif parsed.form_type in ("S-1", "S-1/A"):
            if o := self.extract_offering(parsed):
                result["offering"] = o
            ws = self.extract_warrants(parsed)
            if ws:
                result["warrants"] = ws
            cs = self.extract_convertibles(parsed)
            if cs:
                result["convertibles"] = cs
            els = self.extract_equity_lines(parsed)
            if els:
                result["equity_lines"] = els

        elif parsed.form_type in ("S-3", "S-3/A"):
            if s := self.extract_shelf(parsed):
                result["shelf"] = s
            atms = self.extract_atms(parsed)
            if atms:
                result["atms"] = atms

        elif parsed.form_type.startswith("424B"):
            ws = self.extract_warrants(parsed)
            if ws:
                result["warrants"] = ws
            atms = self.extract_atms(parsed)
            if atms:
                result["atms"] = atms
            if o := self.extract_offering(parsed):
                result["offering"] = o

        elif parsed.form_type == "8-K":
            cs = self.extract_convertibles(parsed)
            if cs:
                result["convertibles"] = cs
            els = self.extract_equity_lines(parsed)
            if els:
                result["equity_lines"] = els

        return result
