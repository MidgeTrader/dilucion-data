-- SQLite schema for private/Telegram mode
-- File: data/dilution.db

CREATE TABLE IF NOT EXISTS companies (
    cik TEXT PRIMARY KEY,
    ticker TEXT UNIQUE NOT NULL,
    company_name TEXT,
    sector TEXT,
    float_shares REAL,
    shares_outstanding REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS filings_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cik TEXT NOT NULL,
    ticker TEXT,
    form_type TEXT NOT NULL,
    accession_number TEXT UNIQUE NOT NULL,
    filed_date DATE,
    shelf_amount_usd REAL,
    dilution_percentage REAL,
    has_atm BOOLEAN DEFAULT 0,
    has_full_ratchet BOOLEAN DEFAULT 0,
    has_prefunded_warrants BOOLEAN DEFAULT 0,
    warrants_found BOOLEAN DEFAULT 0,
    is_shelf_takedown BOOLEAN DEFAULT 0,
    is_rights_offering BOOLEAN DEFAULT 0,
    is_overnight_offering BOOLEAN DEFAULT 0,
    is_block_trade BOOLEAN DEFAULT 0,
    is_secondary_offering BOOLEAN DEFAULT 0,
    is_primary_offering BOOLEAN DEFAULT 0,
    is_best_efforts BOOLEAN DEFAULT 0,
    is_firm_commitment BOOLEAN DEFAULT 0,
    is_global_offering BOOLEAN DEFAULT 0,
    is_continuous_offering BOOLEAN DEFAULT 0,
    is_spot_offering BOOLEAN DEFAULT 0,
    is_warrant_offering BOOLEAN DEFAULT 0,
    warrants_exercise_price REAL,
    risk_level TEXT CHECK(risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    filing_url TEXT,
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cik) REFERENCES companies(cik)
);

CREATE INDEX IF NOT EXISTS idx_filings_cik ON filings_history(cik);
CREATE INDEX IF NOT EXISTS idx_filings_ticker ON filings_history(ticker);
CREATE INDEX IF NOT EXISTS idx_filings_created ON filings_history(created_at);
CREATE INDEX IF NOT EXISTS idx_filings_dilution ON filings_history(dilution_percentage);

CREATE TABLE IF NOT EXISTS watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    cik TEXT NOT NULL,
    ticker TEXT NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(chat_id, ticker),
    FOREIGN KEY (cik) REFERENCES companies(cik)
);

CREATE INDEX IF NOT EXISTS idx_watchlist_chat ON watchlist(chat_id);

CREATE TABLE IF NOT EXISTS rag_analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cik TEXT NOT NULL,
    accession_number TEXT,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    source_chunks TEXT,
    model_used TEXT DEFAULT 'deepseek-chat',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS api_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    endpoint TEXT NOT NULL,
    cache_key TEXT NOT NULL,
    response_json TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    UNIQUE(endpoint, cache_key)
);

CREATE TABLE IF NOT EXISTS bot_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
