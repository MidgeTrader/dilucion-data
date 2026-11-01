"""Seed data for SLND (Southland Holdings) — warrants identified from 8-K.

Ticker: SLND
Company: Southland Holdings, Inc.
CIK: 0001883814
Source: 8-K filed 2026-06-10 (annual meeting) — confirms redeemable warrants at $11.50
"""

from models import DilutionTrackerData, CashPosition, WarrantIssue


SLND_SEED = DilutionTrackerData(
    ticker="SLND",
    company_name="Southland Holdings, Inc.",
    sector="Construction / Infrastructure",

    # ── Cash Position ──
    cash_position=CashPosition(
        cash_estimated=0,
        quarterly_burn=0,
        months_of_cash=0,
        going_concern=False,
        cash_balance_filing_date=None,
    ),

    # ── Warrants ──
    warrants=[
        WarrantIssue(
            issue_label="SPAC Warrants",
            remaining=0,  # unknown exact count
            exercise_price=11.50,
            owners=["Public warrant holders"],
            protection="Standard",
        ),
    ],

    # ── Outstanding Shares ──
    # As of 2026-06-10 annual meeting: 54,218,882 shares outstanding
)
