# SEC Dilution Tracker + AskEdgar RAG (Unified)

Full-stack system combining **automatic SEC dilution detection** (Dilution Tracker) with **RAG AI analysis** (AskEdgar clone).

## Features

| Module | Capability |
|--------|------------|
| **Daily Scanner** | SEC master index → S-3, 424B5, 8-K, EFFECT, RW |
| **RSS Monitor** | Real-time Atom feed polling with dedup |
| **EFTS Search** | Full-text SEC search for ATM, warrants, full ratchet |
| **Document Parser** | HTML → text + keyword extraction |
| **Dilution Calculator** | M/P = S_new → dilution % + risk classification |
| **RAG Engine** | ChromaDB + DeepSeek + OpenAI embeddings |
| **Data Layer** | Parquet (always) + Supabase (optional) |
| **Dashboard** | Next.js dark theme — overview, filings, monitor |

## Quick Start

```bash
cd ~/Desktop/askedgar_clone/backend
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add API keys

python main.py db init
python main.py serve                    # API :8000

# Scan a ticker (full pipeline)
python main.py scan AAPL
python main.py scan SPHL --ask "warrant details?"
python main.py scan SPHL --prompt warrants

# Monitor SEC feed
python main.py monitor --once
python main.py monitor --daily
python main.py monitor                  # daemon

# RAG
python main.py rag TICKER --prompt warrants
python main.py rag https://sec.gov/.../filing.htm

# Search + report
python main.py search -q "Full Ratchet"
python main.py report
python main.py filings 320193
```

```bash
cd ../frontend && npm install && npm run dev   # :3000
```

## Project Structure

```
askedgar_clone/
├── backend/
│   ├── scanners/          # dilution_scanner, rss_monitor, efts_search, company_facts
│   ├── parsers/           # sec_parser, dilution_calculator
│   ├── rag/               # rag_engine, prompts
│   ├── db/                # parquet_db, database (Supabase)
│   ├── apis/              # polygon, finnhub, stocksera, yfinance
│   ├── pipeline.py        # scan ticker orchestrator
│   └── main.py            # CLI + FastAPI
├── frontend/
│   ├── pages/             # index, monitor, filings, ticker/[ticker]
│   └── components/        # Layout, Sidebar, TickerHeader, etc.
└── data/                  # parquet + chroma (gitignored)
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/rag` | RAG query |
| GET | `/ticker/{t}` | Profile + filings + candles + risk |
| GET | `/dilution/top` | Top dilution risks |
| GET | `/alerts/feed` | Alerts feed |
| GET | `/filings/all` | All tracked filings |
| POST | `/scan/{ticker}` | Trigger pipeline scan |

## Environment Variables

See `backend/.env.example`. Required: `DEEPSEEK_API_KEY`, `OPENAI_API_KEY`, `SEC_USER_AGENT`.

Optional: `POLYGON_API_KEY`, `FINNHUB_API_KEY`, `STOCKSERA_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`.

## Dilution Formula

```
S_new = offering_amount_usd / current_price
Dilution % = S_new / (S_outstanding + S_new) × 100
```

Risk: ≥20% HIGH (red), 10–20% MED (yellow), <10% LOW (green)
