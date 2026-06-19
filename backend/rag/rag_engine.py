"""LangChain RAG: ChromaDB + OpenAI embeddings + DeepSeek LLM."""

from __future__ import annotations

import logging
import re
from datetime import date
from typing import List, Optional

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import get_settings
from db.parquet_db import ParquetDB
from models import Citation, RAGResponse, ScanResult
from parsers.sec_parser import ParsedFiling, SECParser
from rag.prompts import SYSTEM_PROMPT, get_prompt

logger = logging.getLogger(__name__)

HUMAN_TEMPLATE = """Contexto del filing SEC:
{context}

Pregunta: {input}

Responde con citas exactas del contexto."""


class RAGEngine:
    """RAG pipeline for SEC filing Q&A."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.settings.validate_rag_keys()
        self.parser = SECParser()
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
            length_function=len,
        )
        self.embeddings = OpenAIEmbeddings(
            model=self.settings.embedding_model,
            api_key=self.settings.openai_api_key,
        )

    def _get_llm(self, use_reasoning: bool = False) -> ChatOpenAI:
        model = (
            self.settings.deepseek_reasoning_model
            if use_reasoning
            else self.settings.deepseek_model
        )
        return ChatOpenAI(
            model=model,
            temperature=self.settings.llm_temperature,
            api_key=self.settings.deepseek_api_key,
            base_url="https://api.deepseek.com/v1",
        )

    def _collection_name(self, accession: Optional[str], url: str) -> str:
        if accession:
            safe = re.sub(r"[^a-zA-Z0-9_-]", "_", accession)
            return f"filing_{safe}"
        return f"filing_{re.sub(r'[^a-zA-Z0-9_-]', '_', url[-40:])}"

    def _get_or_create_vectorstore(self, parsed: ParsedFiling) -> Chroma:
        collection = self._collection_name(parsed.accession_number, parsed.url)
        existing = Chroma(
            collection_name=collection,
            embedding_function=self.embeddings,
            persist_directory=str(self.settings.chroma_dir),
        )
        if existing._collection.count() > 0:
            return existing
        chunks = self.splitter.split_text(parsed.text)
        meta = {
            "source_url": parsed.url,
            "accession_number": parsed.accession_number or "",
            "cik": parsed.cik or "",
            "form_type": parsed.form_type or "",
        }
        docs = [Document(page_content=c, metadata={**meta, "chunk_index": i}) for i, c in enumerate(chunks)]
        return Chroma.from_documents(
            documents=docs,
            embedding=self.embeddings,
            collection_name=collection,
            persist_directory=str(self.settings.chroma_dir),
        )

    def query_filing(
        self,
        parsed: ParsedFiling,
        question: str,
        *,
        use_reasoning: bool = False,
        ticker: Optional[str] = None,
    ) -> RAGResponse:
        vectorstore = self._get_or_create_vectorstore(parsed)
        retriever = vectorstore.as_retriever(search_kwargs={"k": self.settings.retriever_k})
        llm = self._get_llm(use_reasoning)
        prompt = ChatPromptTemplate.from_messages([("system", SYSTEM_PROMPT), ("human", HUMAN_TEMPLATE)])
        docs = retriever.invoke(question)
        context = "\n\n---\n\n".join(
            f"[{i+1}|{d.metadata.get('form_type')}] {d.page_content}" for i, d in enumerate(docs)
        )
        response = llm.invoke(prompt.format_messages(context=context, input=question))
        answer = response.content if hasattr(response, "content") else str(response)
        citations = [Citation(content=d.page_content[:800], metadata=dict(d.metadata)) for d in docs]
        return RAGResponse(
            answer=answer,
            citations=citations,
            model=self.settings.deepseek_reasoning_model if use_reasoning else self.settings.deepseek_model,
            ticker=ticker,
            source_url=parsed.url,
        )

    def scan_url(
        self,
        url: str,
        question: Optional[str] = None,
        *,
        prompt_type: Optional[str] = None,
        use_reasoning: bool = False,
        ticker: Optional[str] = None,
    ) -> ScanResult:
        parsed = self.parser.load_from_url(url)
        if prompt_type:
            question = get_prompt(prompt_type)
            if prompt_type == "convertible":
                use_reasoning = True
        if not question:
            question = get_prompt("dilution")
        rag = self.query_filing(parsed, question, use_reasoning=use_reasoning, ticker=ticker)
        ext = parsed.extraction
        db = ParquetDB()
        db.inicializar()
        filing_record = None
        if parsed.accession_number and parsed.cik:
            from datetime import datetime as dt
            filed = date.today()
            filing_record = db.registrar_alerta(
                accession_number=parsed.accession_number,
                cik=parsed.cik,
                form_type=parsed.form_type or "UNKNOWN",
                filed_date=filed,
                ticker=ticker,
                shelf_amount_usd=ext.shelf_amount_usd,
                dilution_percentage=None,
                warrants_found=ext.warrants_found,
                has_atm=ext.has_atm,
                has_full_ratchet=ext.has_full_ratchet,
                has_prefunded_warrants=ext.has_prefunded_warrants,
                summary=rag.answer[:500],
                source_url=parsed.url,
            )
        return ScanResult(
            ticker=ticker,
            cik=parsed.cik,
            form_type=parsed.form_type,
            accession_number=parsed.accession_number,
            source_url=parsed.url,
            answer=rag.answer,
            citations=rag.citations,
            filing_record=filing_record,
        )

    def query_ticker(
        self,
        ticker: str,
        question: Optional[str] = None,
        *,
        prompt_type: Optional[str] = None,
        use_reasoning: bool = False,
    ) -> RAGResponse:
        db = ParquetDB()
        filings = db.get_filings_by_ticker(ticker)
        if not filings or not filings[0].source_url:
            raise ValueError(f"No indexed filings for {ticker}. Run: python main.py scan {ticker}")
        parsed = self.parser.load_from_url(filings[0].source_url)
        if prompt_type:
            question = get_prompt(prompt_type)
        if not question:
            question = get_prompt("dilution")
        return self.query_filing(parsed, question, use_reasoning=use_reasoning, ticker=ticker)
