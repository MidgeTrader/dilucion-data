"""Aggregates Polygon, Finnhub, Stocksera, yfinance into unified profiles."""

from __future__ import annotations

import logging

from apis.finnhub_client import FinnhubClient
from apis.finviz_client import FinvizClient
from apis.news_aggregator import NewsAggregator
from apis.polygon_client import PolygonClient
from apis.stocksera_client import StockseraClient
from apis.yfinance_client import YFinanceClient
from cache import TTLCache
from config import get_settings
from db.parquet_db import ParquetDB
from models import Company, NewsArticle, TickerProfile

logger = logging.getLogger(__name__)


class DataEnrichment:
    def __init__(self) -> None:
        settings = get_settings()
        self.cache = TTLCache(settings.cache_db_path)
        self.polygon = PolygonClient(self.cache)
        self.finnhub = FinnhubClient(self.cache)
        self.finviz = FinvizClient(self.cache)
        self.stocksera = StockseraClient(self.cache)
        self.yfinance = YFinanceClient(self.cache)
        self.news = NewsAggregator(self.cache)

    def get_ticker_profile(self, ticker: str) -> TickerProfile:
        profile = TickerProfile(ticker=ticker.upper())
        poly = self.polygon.get_ticker_details(ticker)
        if poly and poly.get("results"):
            r = poly["results"]
            profile.company_name = r.get("name")
            # Polygon's sic_description is the most detailed industry data
            profile.industry = r.get("sic_description")
            profile.country = r.get("locale", "US")
            profile.exchange = r.get("primary_exchange", "").replace("X", "") if r.get("primary_exchange") else None
            if r.get("share_class_shares_outstanding"):
                profile.shares_outstanding = float(r["share_class_shares_outstanding"])
            if r.get("market_cap"):
                profile.market_cap = float(r["market_cap"])
            if r.get("employees"):
                profile.employees = int(r["employees"])

        fh = self.finnhub.get_company_profile(ticker)
        if fh:
            profile.company_name = profile.company_name or fh.get("name")
            profile.industry = profile.industry or fh.get("finnhubIndustry")
            profile.country = fh.get("country", profile.country)
            profile.exchange = profile.exchange or fh.get("exchange", "").split("(")[0].strip()
            if fh.get("marketCapitalization"):
                profile.market_cap = profile.market_cap or float(fh["marketCapitalization"])
            if fh.get("shareOutstanding"):
                profile.shares_outstanding = profile.shares_outstanding or (float(fh["shareOutstanding"]) * 1_000_000)

        # yfinance: única fuente confiable para sector
        yf_profile = self.yfinance.get_profile_fields(ticker)
        profile.company_name = profile.company_name or yf_profile.get("company_name")
        profile.sector = yf_profile.get("sector")  # siempre de yfinance
        profile.industry = profile.industry or yf_profile.get("industry")
        profile.country = profile.country or yf_profile.get("country")
        profile.exchange = profile.exchange or yf_profile.get("exchange")
        profile.description = profile.description or yf_profile.get("longBusinessSummary")
        profile.about = profile.about or profile.description
        profile.website = profile.website or yf_profile.get("website")
        if yf_profile.get("employees"):
            profile.employees = profile.employees or yf_profile.get("employees")
        if yf_profile.get("market_cap"):
            profile.market_cap = profile.market_cap or yf_profile.get("market_cap")
        if yf_profile.get("enterprise_value"):
            profile.enterprise_value = yf_profile.get("enterprise_value")
        if yf_profile.get("avg_volume"):
            profile.avg_volume = yf_profile.get("avg_volume")
        if yf_profile.get("cash_per_share"):
            profile.cash_per_share = yf_profile.get("cash_per_share")
        if yf_profile.get("institutional_ownership"):
            profile.institutional_ownership = yf_profile.get("institutional_ownership")
        if yf_profile.get("days_to_cover"):
            profile.days_to_cover = yf_profile.get("days_to_cover")
        if not profile.shares_outstanding:
            profile.shares_outstanding = yf_profile.get("shares_outstanding")
        if not profile.float_shares:
            profile.float_shares = yf_profile.get("float_shares")
        if not profile.short_percent_float:
            profile.short_percent_float = yf_profile.get("short_percent_float")
        if not profile.days_to_cover:
            profile.days_to_cover = yf_profile.get("days_to_cover")

        quote = self.finnhub.get_quote(ticker)
        if quote:
            profile.price = quote.price
            profile.change_percent = quote.change_percent
        else:
            yf_quote = self.yfinance.get_quote(ticker)
            if yf_quote:
                profile.price = yf_quote.price
                profile.change_percent = yf_quote.change_percent

        if not profile.shares_outstanding:
            profile.shares_outstanding = self.yfinance.get_shares_outstanding(ticker)

        short = self.stocksera.get_short_interest(ticker)
        if short:
            profile.borrow_rate = short.borrow_rate
            profile.short_percent_float = short.short_percent_float

        # Finviz: completa lo que falte de otras fuentes
        fv = self.finviz.get_profile_fields(ticker)
        if not profile.sector:
            profile.sector = fv.get("sector")
        if not profile.industry:
            profile.industry = fv.get("industry")
        if not profile.float_shares:
            profile.float_shares = fv.get("float_shares")
        if not profile.short_percent_float:
            profile.short_percent_float = fv.get("short_percent_float")
        if not profile.days_to_cover:
            profile.days_to_cover = fv.get("days_to_cover")
        if not profile.institutional_ownership:
            profile.institutional_ownership = fv.get("institutional_ownership")
        if not profile.employees:
            profile.employees = fv.get("employees")
        if not profile.country or profile.country.lower() == "us":
            profile.country = fv.get("country") or profile.country
        if not profile.shares_outstanding:
            profile.shares_outstanding = fv.get("shares_outstanding")

        return profile

    def get_company_news(
        self,
        ticker: str,
        company_name: str | None = None,
        filings=None,
        limit: int = 30,
    ) -> list[NewsArticle]:
        return self.news.get_all_news(ticker, company_name, filings, limit=limit)

    def refresh_tickers_to_parquet(self) -> int:
        db = ParquetDB()
        db.inicializar()
        tickers = self.polygon.fetch_active_tickers()
        count = 0
        for item in tickers:
            ticker = item.get("ticker")
            if not ticker:
                continue
            cik = str(item.get("cik", "")).lstrip("0") or "0"
            db.upsert_company(Company(
                cik=cik, ticker=ticker,
                company_name=item.get("name", ticker),
                country=item.get("locale", "US"),
            ))
            count += 1
        return count
