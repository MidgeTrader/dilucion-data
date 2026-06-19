"""Dilution percentage calculator."""

from __future__ import annotations

import logging
import re
from typing import Optional

from pydantic import BaseModel

from models import RiskLevel

logger = logging.getLogger(__name__)


class DilutionResult(BaseModel):
    offering_amount_usd: Optional[float] = None
    current_price: Optional[float] = None
    shares_new: Optional[float] = None
    shares_outstanding: Optional[float] = None
    dilution_percentage: Optional[float] = None
    risk_level: RiskLevel = RiskLevel.MEDIUM
    warrant_exercise_risk: RiskLevel = RiskLevel.LOW
    cash_need_score: RiskLevel = RiskLevel.MEDIUM
    notes: list[str] = []


class DilutionCalculator:
    """
    Calculate dilution % from filing text and market data.

    Formula:
      S_new = M / P_current
      Dilution % = S_new / (S_current + S_new) × 100
    """

    OFFERING_PATTERNS = [
        # "aggregate offering price of up to $X million"
        re.compile(r"(?:aggregate\s+)?offering\s+(?:price|amount|of)\s+(?:of\s+)?(?:up\s+to\s+)?\$?\s*([\d,]+(?:\.\d+)?)\s*(million|billion|M|B)?", re.I),
        # "registered direct offering of $X million"
        re.compile(r"(?:registered\s+)?direct\s+offering\s+(?:of\s+)?\$?\s*([\d,]+(?:\.\d+)?)\s*(million|billion|M|B)?", re.I),
        # "private placement financing of $X million"
        re.compile(r"(?:private\s+)?placement\s+(?:financing\s+)?(?:of\s+)?\$?\s*([\d,]+(?:\.\d+)?)\s*(million|billion|M|B)?", re.I),
        # "securities purchase agreement for $X million"
        re.compile(r"(?:securities\s+)?purchase\s+agreement\s+(?:for\s+)?\$?\s*([\d,]+(?:\.\d+)?)\s*(million|billion|M|B)?", re.I),
        # "gross proceeds ... $X million"
        re.compile(r"gross\s+proceeds.*?\$\s*([\d,]+(?:\.\d+)?)\s*(million|billion|M|B)", re.I),
        # "public offering of $X million" / "underwritten public offering of $X million"
        re.compile(r"(?:underwritten\s+)?public\s+offering\s+(?:of\s+)?\$?\s*([\d,]+(?:\.\d+)?)\s*(million|billion|M|B)?", re.I),
        # "may offer and sell ... having an aggregate offering price of up to $X" (S-3 shelf)
        re.compile(r"aggregate\s+offering\s+price\s+of\s+up\s+to\s+\$?\s*([\d,]+(?:\.\d+)?)\s*(million|billion|M|B)?", re.I),
        # "shelf registration ... $X million" / "shelf ... $X million"
        re.compile(r"shelf\s+(?:registration\s+)?(?:of\s+)?(?:up\s+to\s+)?\$?\s*([\d,]+(?:\.\d+)?)\s*(million|billion|M|B)?", re.I),
        # "proposed public offering of $X million"
        re.compile(r"proposed\s+(?:public\s+)?offering\s+(?:of\s+)?\$?\s*([\d,]+(?:\.\d+)?)\s*(million|billion|M|B)?", re.I),
        # "sell up to $X million of common stock" / "sale of $X million"
        re.compile(r"(?:sell|sale)\s+(?:of\s+)?(?:up\s+to\s+)?\$?\s*([\d,]+(?:\.\d+)?)\s*(million|billion|M|B)?\s+(?:of\s+)?(?:common\s+)?stock", re.I),
        # "raise approximately $X million" / "raise up to $X million"
        re.compile(r"raise\s+(?:approximately\s+)?(?:up\s+to\s+)?\$?\s*([\d,]+(?:\.\d+)?)\s*(million|billion|M|B)?", re.I),
        # "at the market offering ... aggregate offering price of up to $X"
        re.compile(r"at[-\s]the[-\s]market.*?(?:aggregate\s+)?offering\s+price.*?(?:up\s+to\s+)?\$?\s*([\d,]+(?:\.\d+)?)\s*(million|billion|M|B)?", re.I),
    ]

    @staticmethod
    def extract_offering_amount(text: str) -> Optional[float]:
        best = None
        for pattern in DilutionCalculator.OFFERING_PATTERNS:
            for match in pattern.finditer(text):
                raw = match.group(1)
                if not raw:
                    continue
                unit = match.group(2).lower() if match.lastindex and match.lastindex >= 2 and match.group(2) else ""
                amount = float(raw.replace(",", ""))
                if unit in {"million", "m"}:
                    amount *= 1_000_000
                elif unit in {"billion", "b"}:
                    amount *= 1_000_000_000
                # Skip par values (stock par value is always < $1)
                if amount is not None and amount >= 1_000:
                    if best is None or amount > best:
                        best = amount
        return best

    @staticmethod
    def classify_risk(dilution_pct: Optional[float]) -> RiskLevel:
        if dilution_pct is None:
            return RiskLevel.MEDIUM
        if dilution_pct >= 20:
            return RiskLevel.HIGH
        if dilution_pct >= 10:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def calculate(
        self,
        filing_text: str,
        *,
        current_price: Optional[float] = None,
        shares_outstanding: Optional[float] = None,
        has_warrants: bool = False,
        has_full_ratchet: bool = False,
        cash_on_hand: Optional[float] = None,
        quarterly_burn: Optional[float] = None,
    ) -> DilutionResult:
        """Compute dilution metrics from filing text and market data."""
        result = DilutionResult()
        m = self.extract_offering_amount(filing_text)
        result.offering_amount_usd = m
        result.current_price = current_price
        result.shares_outstanding = shares_outstanding

        if m and current_price and current_price > 0:
            s_new = m / current_price
            result.shares_new = s_new
            if shares_outstanding and shares_outstanding > 0:
                dilution = (s_new / (shares_outstanding + s_new)) * 100
                result.dilution_percentage = round(dilution, 2)
                result.risk_level = self.classify_risk(dilution)
                result.notes.append(
                    f"S_new={s_new:,.0f} shares from ${m:,.0f} @ ${current_price:.2f}"
                )
            else:
                result.notes.append("Shares outstanding unavailable — dilution % skipped")
        elif m:
            result.notes.append(f"Offering amount ${m:,.0f} found but price unavailable")

        if has_warrants or has_full_ratchet:
            result.warrant_exercise_risk = RiskLevel.HIGH if has_full_ratchet else RiskLevel.MEDIUM

        if cash_on_hand is not None and quarterly_burn and quarterly_burn > 0:
            quarters = cash_on_hand / quarterly_burn
            if quarters < 2:
                result.cash_need_score = RiskLevel.HIGH
            elif quarters < 4:
                result.cash_need_score = RiskLevel.MEDIUM
            else:
                result.cash_need_score = RiskLevel.LOW
            result.notes.append(f"Cash runway ~{quarters:.1f} quarters")

        return result
