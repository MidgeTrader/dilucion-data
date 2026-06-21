# Dilución Data

Automatic SEC dilution detection + RAG AI analysis. OpenAI embeddings + DeepSeek LLM.

## Features

| Module | Capability |
|--------|------------|
| **Daily Scanner** | SEC master index → S-3, 424B5, 8-K, EFFECT, RW |
| **Dilution Tracker** | 11 sections: Cash, Shelf, ATMs, Warrants, Convertibles, Offerings... |
| **RAG Extraction** | ChromaDB + DeepSeek → structured JSON extraction |
| **Document Parser** | HTML → text + keyword extraction |
| **Research Report** | AI-generated analysis in Spanish via DeepSeek |
| **Filings UI** | Grouped by category, 2-column grid, AI headlines |
| **Data Layer** | Parquet + SQLite + ChromaDB (all local) |

## Quick Start

```bash
cd ~/Desktop/dilucion_data/backend
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add API keys

python main.py db init
python main.py serve                    # API :8000

# Scan a ticker (full pipeline)
python main.py scan AAPL
python main.py scan SPHL --ask "warrant details?"

# RAG
python main.py rag TICKER --prompt warrants
python main.py rag https://sec.gov/.../filing.htm

# Search + report
python main.py search -q "Full Ratchet"
python main.py report
```

```bash
cd ../frontend && npm install && npm run dev   # :3000
```

## Project Structure

```
dilucion_data/
├── backend/
│   ├── scanners/          # dilution_scanner, rss_monitor, efts_search, company_facts
│   ├── parsers/           # sec_parser, dilution_calculator, table_extractor
│   ├── dilution_rag.py    # RAG extraction (OpenAI + DeepSeek)
│   ├── dilution_tracker.py# Full dilution tracker service
│   ├── rag/               # rag_engine, prompts
│   ├── db/                # parquet_db, database (SQLite)
│   ├── apis/              # polygon, finnhub, stocksera, yfinance
│   ├── pipeline.py        # scan ticker orchestrator
│   ├── seed_data/         # curated seed data (BURU)
│   └── main.py            # CLI + FastAPI
├── frontend/
│   ├── pages/             # index, monitor, filings, ticker/[ticker]
│   └── components/        # ticker views (Filings, Insights, Overview, Dilution...)
└── data/                  # parquet + chroma + sqlite cache (gitignored)
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/rag` | RAG query |
| GET | `/ticker/{t}` | Profile + filings + candles + risk |
| GET | `/ticker/{t}/dilution` | Full dilution tracker data |
| GET | `/dilution/top` | Top dilution risks |
| GET | `/alerts/feed` | Alerts feed |
| GET | `/filings/all` | All tracked filings |
| POST | `/scan/{ticker}` | Trigger pipeline scan |

## Environment Variables

See `backend/.env.example`. Required: `DEEPSEEK_API_KEY`, `OPENAI_API_KEY`, `SEC_USER_AGENT`.

Optional: `POLYGON_API_KEY`, `MASSIVE_API_KEY`, `FINNHUB_API_KEY`, `STOCKSERA_API_KEY`, `EODHD_API_KEY`.

All data lives under `data/` (Parquet, SQLite, Chroma) — no cloud database required.

## Dilution Formula

```
S_new = offering_amount_usd / current_price
Dilution % = S_new / (S_outstanding + S_new) × 100
```

Risk: ≥20% HIGH (red), 10–20% MED (yellow), <10% LOW (green)
