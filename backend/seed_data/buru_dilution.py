"""Seed data for BURU (SeaStar Medical) — seed data reference.

Ticker: BURU (filing CIK references ICU)
Company: SeaStar Medical Holdings Corporation
Reference data
Extracted: 2026-06-21

These data are manually curated from the above page. Use as seed/reference
while the SEC filing parser is improved.
"""

from models import DilutionTrackerData, CashPosition, PendingOffering, \
    ShelfRegistration, ATMProgram, WarrantIssue, ConvertibleIssue, \
    EquityLine, CompletedOffering, LockUpAgreement, NasdaqComplianceItem, \
    ReverseSplit


BURU_SEED = DilutionTrackerData(
    ticker="BURU",
    company_name="SeaStar Medical Holdings Corporation",
    sector="Healthcare / Medical Devices",

    # ── Cash Position ──
    cash_position=CashPosition(
        cash_estimated=2_000_000,           # ~$2M estimated current cash
        quarterly_burn=7_070_000,           # $7.07M quarterly burn
        months_of_cash=0.8,                 # 0.8 months cash left
        going_concern=True,
        cash_balance_filing_date="2025-03-31",
    ),

    # ── Pending Offering ──
    pending_offering=PendingOffering(
        type="Best Efforts Public Offering",
        shares=4_240_000,
        price=1.18,
        warrants=4_240_000,
        date="2025-06-15",
        filing_type="S-1",
    ),

    # ── Shelf Registration ──
    shelf=ShelfRegistration(
        active=True,
        raisable_total=71_102_150,
        total_offering=100_000_000,
        amt_sold_last_12m=0,
        float_shares=10_210_000,
        sixty_day_high_price=176.00,
        price_to_exceed_baby_shelf=7.35,
        float_value=1_800_000_000,
        expiration="2026-12-25",
        over_baby_shelf=False,
    ),

    # ── ATM Programs ──
    atms=[
        ATMProgram(name="April 2025 ATM", remaining=6_530_000, total_amt=7_430_000,
                   bank="H.C. Wainwright", date="2025-04-01"),
        ATMProgram(name="August 2024 ATM", remaining=6_530_000, total_amt=25_000_000,
                   bank="H.C. Wainwright", date="2024-08-19"),
    ],

    # ── Warrants (10 issues, reference) ──
    warrants=[
        WarrantIssue(issue_label="Feb 2025", remaining=3_529_412, exercise_price=1.70,
                     owners=["Armistice"], protection="Customary Anti-Dilution"),
        WarrantIssue(issue_label="Jul 2024", remaining=947_868, exercise_price=10.55,
                     owners=["Armistice", "Alto", "Intracoastal", "Sabby"],
                     protection="Customary Anti-Dilution"),
        WarrantIssue(issue_label="Jan 2024 Series B", remaining=216_815, exercise_price=20.75,
                     owners=["3i, LP"], protection="N/A"),
        WarrantIssue(issue_label="Jan 2024 Series A", remaining=433_630, exercise_price=20.75,
                     owners=["3i, LP"], protection="N/A"),
        WarrantIssue(issue_label="Dec 2023", remaining=63_324, exercise_price=14.00,
                     owners=["3i, LP"], protection="Full Ratchet"),
        WarrantIssue(issue_label="Nov 2023", remaining=29_551, exercise_price=5.00,
                     owners=["3i, LP"], protection="Full Ratchet"),
        WarrantIssue(issue_label="Aug 2023", remaining=88_654, exercise_price=5.00,
                     owners=["HB Strategies", "Vellar"], protection="Full Ratchet"),
        WarrantIssue(issue_label="Mar 2023", remaining=212_514, exercise_price=5.00,
                     owners=["3i"], protection="Full Ratchet"),
        WarrantIssue(issue_label="Oct 2022 (first)", remaining=422_000, exercise_price=287.50,
                     owners=[], protection="N/A"),
        WarrantIssue(issue_label="Oct 2022 (second)", remaining=249_520, exercise_price=287.50,
                     owners=[], protection="N/A"),
    ],

    # ── Convertibles (all fully converted — $0 remaining) ──
    convertibles=[
        ConvertibleIssue(issue_label="Dec 2023", total=2_170_000, remaining=0,
                         conversion_price=14.00, protection="Full Ratchet", owner="3i, LP"),
        ConvertibleIssue(issue_label="Nov 2023", total=543_000, remaining=0,
                         conversion_price=9.25, protection="Full Ratchet", owner="3i, LP"),
        ConvertibleIssue(issue_label="Aug 2023", total=1_630_000, remaining=0,
                         conversion_price=5.00, protection="Full Ratchet", owner="N/A"),
        ConvertibleIssue(issue_label="Mar 2023", total=5_470_000, remaining=0,
                         conversion_price=5.00, protection="Full Ratchet", owner="3i"),
    ],

    # ── Equity Line (Lincoln Park SPA) ──
    equity_lines=[
        EquityLine(
            total_amt=15_000_000, shares=4_740_000, atm_remaining=0,
            pricing_mechanism="97% of the lower of two values — lowest sale price or "
                              "avg of three lowest closing prices over 10 days",
            date="2025-05-18",
            max_daily_shares="40,000 (can increase to 75,000)",
            max_daily_amount="$500,000 per Regular Purchase",
        ),
    ],

    # ── Completed Offerings (13 events, chronological) ──
    completed_offerings=[
        CompletedOffering(date="2025-05-08", type="ATM USED", amount=900_000,
                          shares=623_650, price=1.44, bank="H.C. Wainwright"),
        CompletedOffering(date="2025-04-24", type="NEW EQUITY LINE", amount=15_000_000,
                          shares=236_410, bank="Lincoln Park"),
        CompletedOffering(date="2025-03-30", type="ATM USED", amount=3_430_000,
                          bank="H.C. Wainwright"),
        CompletedOffering(date="2025-02-02", type="REGISTERED OFFERING", amount=6_000_000,
                          shares=3_529_412, price=1.70, warrants=3_529_412, bank="Armistice"),
        CompletedOffering(date="2024-07-09", type="RDO", amount=10_000_000,
                          shares=947_868, price=10.55, warrants=947_868),
        CompletedOffering(date="2024-01-25", type="RDO", amount=9_000_000,
                          shares=433_630, price=20.75, warrants=650_445, bank="Armistice"),
        CompletedOffering(date="2024-01-23", type="PRIVATE", amount=815_220,
                          shares=58_230, price=14.00, warrants=31_660, bank="3i"),
        CompletedOffering(date="2024-01-11", type="PRIVATE", amount=271_740,
                          shares=19_410, price=14.00, warrants=10_550),
        CompletedOffering(date="2023-11-26", type="PRIVATE", amount=543_480,
                          price=9.25, warrants=29_550, bank="3i"),
        CompletedOffering(date="2023-10-09", type="ATM USED", amount=3_460_000,
                          shares=234_420, price=14.75, bank="Tumim Stone"),
        CompletedOffering(date="2023-08-06", type="PRIVATE", amount=543_480,
                          shares=108_700, price=5.00, warrants=29_550, bank="3i"),
        CompletedOffering(date="2023-03-15", type="PRIVATE", amount=3_300_000,
                          shares=48_890, price=67.50, warrants=13_130, bank="Maxim/3i"),
        CompletedOffering(date="2021-01-26", type="RDO", amount=90_000_000,
                          shares=360_000, price=250.00, warrants=360_000, bank="Maxim Group"),
    ],

    # ── Lock-Up Agreements ──
    lock_up_agreements=[
        LockUpAgreement(description="60-day post-closing (officers & directors)",
                        duration_days=60, date_filed="2025-06-15", filing_type="S-1"),
        LockUpAgreement(description="Amended Registration Rights (Apr 21, 2022)",
                        date_filed="2025-05-18", filing_type="S-1"),
        LockUpAgreement(description="Officers/Directors post-offering",
                        duration_days=120, date_filed="2023-09-07", filing_type="S-1"),
    ],

    # ── NASDAQ Compliance ──
    nasdaq_compliance=[
        NasdaqComplianceItem(
            date="2025-04-28",
            rule="Section 1003(a)(i) — equity below $2M",
            exchange="NYSE American",
            status="RESOLVED",
            details="Positive equity of $2.17M as of March 31, 2025; "
                    "compliance plan deadline Oct 29, 2025",
        ),
    ],

    # ── Reverse Splits ──
    reverse_splits=[
        ReverseSplit(date="2024-06-09", ratio="25-to-1"),
    ],
)
