"""Aggregates Polygon, Finnhub, Stocksera, yfinance into unified profiles."""

from __future__ import annotations

import logging

from apis.finnhub_client import FinnhubClient
from apis.polygon_client import PolygonClient
from apis.stocksera_client import StockseraClient
from apis.yfinance_client import YFinanceClient
from cache import TTLCache
from config import get_settings
from db.parquet_db import ParquetDB
from models import Company, TickerProfile

logger = logging.getLogger(__name__)


class DataEnrichment:
    def __init__(self) -> None:
        settings = get_settings()
        self.cache = TTLCache(settings.cache_db_path)
        self.polygon = PolygonClient(self.cache)
        self.finnhub = FinnhubClient(self.cache)
        self.stocksera = StockseraClient(self.cache)
        self.yfinance = YFinanceClient(self.cache)

    def get_ticker_profile(self, ticker: str) -> TickerProfile:
        profile = TickerProfile(ticker=ticker.upper())
        poly = self.polygon.get_ticker_details(ticker)
        if poly and poly.get("results"):
            r = poly["results"]
            profile.company_name = r.get("name")
            profile.sector = r.get("sic_description") or r.get("market")
            profile.country = r.get("locale", "US")
            if r.get("share_class_shares_outstanding"):
                profile.shares_outstanding = float(r["share_class_shares_outstanding"])
        fh = self.finnhub.get_company_profile(ticker)
        if fh:
            profile.company_name = profile.company_name or fh.get("name")
            profile.sector = profile.sector or fh.get("finnhubIndustry")
            profile.country = fh.get("country", profile.country)
            if fh.get("shareOutstanding"):
                profile.shares_outstanding = float(fh["shareOutstanding"]) * 1_000_000
        quote = self.finnhub.get_quote(ticker)
        if quote:
            profile.price = quote.price
            profile.change_percent = quote.change_percent
        else:
            profile.price = self.yfinance.get_price(ticker)
        if not profile.shares_outstanding:
            profile.shares_outstanding = self.yfinance.get_shares_outstanding(ticker)
        short = self.stocksera.get_short_interest(ticker)
        if short:
            profile.borrow_rate = short.borrow_rate
            profile.short_percent_float = short.short_percent_float
        return profile

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
                sector=item.get("sic_description"),
                country=item.get("locale", "US"),
            ))
            count += 1
        return count
