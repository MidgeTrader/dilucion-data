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

    OFFERING_PATTERN = re.compile(
        r"aggregate\s+offering\s+price\s+of\s+up\s+to\s+\$?\s*([\d,]+(?:\.\d+)?)\s*(million|billion|M|B)?",
        re.I,
    )

    @staticmethod
    def extract_offering_amount(text: str) -> Optional[float]:
        match = DilutionCalculator.OFFERING_PATTERN.search(text)
        if not match:
            generic = re.search(
                r"\$\s*([\d,]+(?:\.\d+)?)\s*(million|billion|M|B)?",
                text[:50000],
                re.I,
            )
            if not generic:
                return None
            match = generic
        amount = float(match.group(1).replace(",", ""))
        unit = (match.group(2) or "").lower() if match.lastindex and match.lastindex >= 2 else ""
        if unit in {"million", "m"}:
            amount *= 1_000_000
        elif unit in {"billion", "b"}:
            amount *= 1_000_000_000
        return amount

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
