"""Parquet data lake — companies + dilution filings."""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import List, Optional

import pandas as pd

from config import get_settings
from models import Company, DilutionAlert, FilingDilution, RiskLevel

logger = logging.getLogger(__name__)

COMPANIES_COLUMNS = [
    "cik", "ticker", "company_name", "float_shares",
    "shares_outstanding", "sector", "country", "market_cap", "updated_at",
]

FILINGS_COLUMNS = [
    "accession_number", "cik", "ticker", "form_type", "filed_date",
    "shelf_amount_usd", "dilution_percentage", "warrants_found",
    "has_atm", "has_full_ratchet", "has_prefunded_warrants",
    "risk_level", "summary", "source_url",
]


class ParquetDB:
    """CRUD over local Parquet files with dedup by accession_number."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.companies_path = self.settings.companies_parquet
        self.filings_path = self.settings.filings_parquet

    def inicializar(self) -> None:
        self.settings.data_dir.mkdir(parents=True, exist_ok=True)
        if not self.companies_path.exists():
            pd.DataFrame(columns=COMPANIES_COLUMNS).to_parquet(
                self.companies_path, compression="snappy", index=False
            )
        if not self.filings_path.exists():
            pd.DataFrame(columns=FILINGS_COLUMNS).to_parquet(
                self.filings_path, compression="snappy", index=False
            )
        logger.info("Parquet DB initialized at %s", self.settings.data_dir)

    def init(self) -> None:
        self.inicializar()

    def _read_companies(self) -> pd.DataFrame:
        if not self.companies_path.exists():
            self.inicializar()
        return pd.read_parquet(self.companies_path)

    def _read_filings(self) -> pd.DataFrame:
        if not self.filings_path.exists():
            self.inicializar()
        return pd.read_parquet(self.filings_path)

    def upsert_company(self, company: Company) -> None:
        df = self._read_companies()
        record = company.model_dump()
        record["updated_at"] = datetime.now(timezone.utc).isoformat()
        if not df.empty and str(company.cik) in df["cik"].astype(str).values:
            mask = df["cik"].astype(str) == str(company.cik)
            for col, val in record.items():
                if col in df.columns:
                    df.loc[mask, col] = val
        else:
            df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
        df.drop_duplicates(subset=["cik"], keep="last", inplace=True)
        df.to_parquet(self.companies_path, compression="snappy", index=False)

    def upsert_filing(self, filing: FilingDilution) -> None:
        df = self._read_filings()
        record = filing.model_dump()
        record["filed_date"] = pd.Timestamp(filing.filed_date)
        if not df.empty and filing.accession_number in df["accession_number"].astype(str).values:
            mask = df["accession_number"].astype(str) == filing.accession_number
            for col, val in record.items():
                if col in df.columns:
                    df.loc[mask, col] = val
        else:
            df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
        df.drop_duplicates(subset=["accession_number"], keep="last", inplace=True)
        df.to_parquet(self.filings_path, compression="snappy", index=False)

    def registrar_alerta(
        self,
        accession_number: str,
        cik: str,
        form_type: str,
        filed_date: date,
        *,
        ticker: Optional[str] = None,
        shelf_amount_usd: Optional[float] = None,
        dilution_percentage: Optional[float] = None,
        warrants_found: bool = False,
        has_atm: bool = False,
        has_full_ratchet: bool = False,
        has_prefunded_warrants: bool = False,
        risk_level: Optional[RiskLevel] = None,
        summary: Optional[str] = None,
        source_url: Optional[str] = None,
    ) -> FilingDilution:
        if risk_level is None and dilution_percentage is not None:
            if dilution_percentage >= 20:
                risk_level = RiskLevel.HIGH
            elif dilution_percentage >= 10:
                risk_level = RiskLevel.MEDIUM
            else:
                risk_level = RiskLevel.LOW
        filing = FilingDilution(
            accession_number=accession_number,
            cik=cik,
            ticker=ticker,
            form_type=form_type,
            filed_date=filed_date,
            shelf_amount_usd=shelf_amount_usd,
            dilution_percentage=dilution_percentage,
            warrants_found=warrants_found,
            has_atm=has_atm,
            has_full_ratchet=has_full_ratchet,
            has_prefunded_warrants=has_prefunded_warrants,
            risk_level=risk_level,
            summary=summary,
            source_url=source_url,
        )
        self.upsert_filing(filing)
        return filing

    def query_top_dilution(self, limit: int = 20) -> List[FilingDilution]:
        df = self._read_filings()
        if df.empty:
            return []
        df = df.copy()
        df["dilution_percentage"] = pd.to_numeric(df["dilution_percentage"], errors="coerce")
        df = df.sort_values("dilution_percentage", ascending=False, na_position="last")
        return [self._row_to_filing(row) for _, row in df.head(limit).iterrows()]

    def query_by_ticker(self, ticker: str) -> List[FilingDilution]:
        return self.get_filings_by_ticker(ticker)

    def get_all_filings(self, limit: int = 100) -> List[FilingDilution]:
        df = self._read_filings()
        if df.empty:
            return []
        df = df.sort_values("filed_date", ascending=False)
        return [self._row_to_filing(row) for _, row in df.head(limit).iterrows()]

    def get_filings_by_ticker(self, ticker: str) -> List[FilingDilution]:
        df = self._read_filings()
        if df.empty:
            return []
        subset = df[df["ticker"].astype(str).str.upper() == ticker.upper()]
        return [self._row_to_filing(row) for _, row in subset.iterrows()]

    def get_company_by_ticker(self, ticker: str) -> Optional[Company]:
        df = self._read_companies()
        if df.empty:
            return None
        match = df[df["ticker"].astype(str).str.upper() == ticker.upper()]
        if match.empty:
            return None
        row = match.iloc[0]
        return Company(
            cik=str(row["cik"]),
            ticker=str(row["ticker"]),
            company_name=str(row["company_name"]),
            float_shares=float(row["float_shares"]) if pd.notna(row.get("float_shares")) else None,
            shares_outstanding=float(row["shares_outstanding"]) if pd.notna(row.get("shares_outstanding")) else None,
            sector=row.get("sector") if pd.notna(row.get("sector")) else None,
            country=row.get("country") if pd.notna(row.get("country")) else "US",
            market_cap=float(row["market_cap"]) if pd.notna(row.get("market_cap")) else None,
        )

    def search_companies(self, query: str, limit: int = 10) -> List[dict]:
        df = self._read_companies()
        if df.empty:
            return []
        mask = (
            df["ticker"].astype(str).str.upper().str.contains(query.upper(), na=False)
            | df["company_name"].astype(str).str.upper().str.contains(query.upper(), na=False)
        )
        return df[mask].head(limit).to_dict(orient="records")

    def report_summary(self) -> dict:
        filings = self._read_filings()
        companies = self._read_companies()
        return {
            "total_companies": len(companies),
            "total_filings": len(filings),
            "warrants_filings": int(filings["warrants_found"].sum()) if not filings.empty and "warrants_found" in filings else 0,
            "high_risk": int((pd.to_numeric(filings.get("dilution_percentage"), errors="coerce") >= 20).sum()) if not filings.empty else 0,
            "avg_dilution": float(pd.to_numeric(filings["dilution_percentage"], errors="coerce").mean())
            if not filings.empty and filings["dilution_percentage"].notna().any() else None,
        }

    def _row_to_filing(self, row) -> FilingDilution:
        filed = row["filed_date"]
        if isinstance(filed, (pd.Timestamp, datetime)):
            filed = filed.date()
        risk = row.get("risk_level")
        if pd.notna(risk) and risk:
            try:
                risk_level = RiskLevel(str(risk))
            except ValueError:
                risk_level = None
        else:
            risk_level = None
        return FilingDilution(
            accession_number=str(row["accession_number"]),
            cik=str(row["cik"]),
            ticker=str(row["ticker"]) if pd.notna(row.get("ticker")) else None,
            form_type=str(row["form_type"]),
            filed_date=filed,
            shelf_amount_usd=float(row["shelf_amount_usd"]) if pd.notna(row.get("shelf_amount_usd")) else None,
            dilution_percentage=float(row["dilution_percentage"]) if pd.notna(row.get("dilution_percentage")) else None,
            warrants_found=bool(row.get("warrants_found", False)),
            has_atm=bool(row.get("has_atm", False)),
            has_full_ratchet=bool(row.get("has_full_ratchet", False)),
            has_prefunded_warrants=bool(row.get("has_prefunded_warrants", False)),
            risk_level=risk_level,
            summary=str(row["summary"]) if pd.notna(row.get("summary")) else None,
            source_url=str(row["source_url"]) if pd.notna(row.get("source_url")) else None,
        )
