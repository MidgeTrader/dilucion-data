"""Pydantic data models — unified Dilution Tracker + AskEdgar."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, Field, HttpUrl


class RiskLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Med"
    HIGH = "High"


class Company(BaseModel):
    cik: str
    ticker: str
    company_name: str
    float_shares: Optional[float] = None
    shares_outstanding: Optional[float] = None
    sector: Optional[str] = None
    country: Optional[str] = "US"
    market_cap: Optional[float] = None


class FilingDilution(BaseModel):
    accession_number: str
    cik: str
    ticker: Optional[str] = None
    form_type: str
    filed_date: date
    shelf_amount_usd: Optional[float] = None
    dilution_percentage: Optional[float] = None
    warrants_found: bool = False
    has_atm: bool = False
    has_full_ratchet: bool = False
    has_prefunded_warrants: bool = False
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
    risk_level: Optional[RiskLevel] = None
    summary: Optional[str] = None
    source_url: Optional[str] = None
    warrants_detail: list[dict] = Field(default_factory=list)


DilutionAlert = FilingDilution


class CriticalFiling(BaseModel):
    cik: str
    company_name: str
    form_type: str
    filed_date: date
    file_path: str
    filing_url: str
    alert_level: str = "🔴"


class RSSAlert(BaseModel):
    accession_number: str
    cik: str
    company_name: str
    form_type: str
    filing_url: str
    summary: Optional[str] = None
    detected_at: datetime


class SearchHit(BaseModel):
    query: str
    cik: str
    company_name: str
    form_type: str
    filed_date: str
    accession_number: str
    filing_url: str
    excerpt: Optional[str] = None


class Citation(BaseModel):
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    score: Optional[float] = None


class RAGRequest(BaseModel):
    question: str
    ticker: Optional[str] = None
    url: Optional[str] = None
    prompt_type: Optional[str] = None
    use_reasoning: bool = False


class RAGResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    model: str
    ticker: Optional[str] = None
    source_url: Optional[str] = None


class ScanResult(BaseModel):
    ticker: Optional[str] = None
    cik: Optional[str] = None
    form_type: Optional[str] = None
    accession_number: Optional[str] = None
    source_url: str
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    filing_record: Optional[FilingDilution] = None


class PipelineResult(BaseModel):
    ticker: str
    cik: str
    profile: "TickerProfile"
    filings_processed: int
    filings: List[FilingDilution] = Field(default_factory=list)
    rag_results: List[ScanResult] = Field(default_factory=list)


class QuoteData(BaseModel):
    ticker: str
    price: Optional[float] = None
    change_percent: Optional[float] = None
    timestamp: Optional[datetime] = None
    source: str = "finnhub"


class ShortInterestData(BaseModel):
    ticker: str
    short_interest: Optional[float] = None
    borrow_rate: Optional[float] = None
    short_percent_float: Optional[float] = None
    source: str = "stocksera"


class TickerProfile(BaseModel):
    ticker: str
    cik: Optional[str] = None
    company_name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    exchange: Optional[str] = None
    float_shares: Optional[float] = None
    shares_outstanding: Optional[float] = None
    market_cap: Optional[float] = None
    enterprise_value: Optional[float] = None
    price: Optional[float] = None
    change_percent: Optional[float] = None
    borrow_rate: Optional[float] = None
    short_percent_float: Optional[float] = None
    avg_volume: Optional[float] = None
    cash_per_share: Optional[float] = None
    days_to_cover: Optional[float] = None
    institutional_ownership: Optional[float] = None
    employees: Optional[int] = None
    description: Optional[str] = None
    about: Optional[str] = None
    website: Optional[str] = None


class RiskAssessment(BaseModel):
    offering_ability: RiskLevel = RiskLevel.MEDIUM
    offering_frequency: RiskLevel = RiskLevel.MEDIUM
    dilution: RiskLevel = RiskLevel.MEDIUM
    cash_need: RiskLevel = RiskLevel.MEDIUM
    overall_offering_risk: RiskLevel = RiskLevel.MEDIUM
    warrant_exercise: RiskLevel = RiskLevel.LOW


class CandlePoint(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None


class NewsArticle(BaseModel):
    title: str
    source: str
    date: str
    url: str
    summary: Optional[str] = None
    source_type: Optional[str] = None  # sec, massive, eodhd, yfinance, finnhub, polygon, google, benzinga
    sentiment: Optional[float] = None  # EODHD polarity -1..1


class SECFilingMeta(BaseModel):
    accession_number: str
    form_type: str
    filed_date: str
    description: Optional[str] = None
    url: HttpUrl
    ai_summary: Optional[str] = None
