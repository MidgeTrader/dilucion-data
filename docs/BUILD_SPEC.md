# BUILD THIS: COMPLETE SEC DILUTION DETECTION + RAG ANALYSIS SYSTEM (Python + Next.js)

> Full master spec — Dilution Tracker + Dilucion Data + Telegram Private Mode

See user message for complete PART 1-6 + file list (43 files).
Telegram sections 7A-7F appended below.

## PART 7: TELEGRAM BOT ALERTS (Private Mode)

### 7A. telegram_bot.py
- Real-time alerts via Telegram
- Commands: /start, /scan, /alerts, /watch, /unwatch, /watchlist, /top, /ask, /monitor, /status
- python-telegram-bot 21.x async

### 7B. SQLite (data/dilution.db)
- companies, filings_history, watchlist, rag_analyses, api_cache, bot_state

### 7C. database.py
- Local-only: Parquet + SQLite (data/dilution.db)

### 7D. .env
- TELEGRAM_BOT_TOKEN (optional)

### 7E. CLI
- python main.py telegram [--daemon]
- python main.py mode

### 7F. New files
- backend/telegram_bot.py
- backend/db/schema.sqlite.sql
- backend/db/database.py (updated)
