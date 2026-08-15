# Dilucion Data 📉🔍

Rastreador de **dilución accionaria** a partir de filings de la SEC. Detecta eventos de dilución
(warrants, convertibles, ATMs, shelf registrations, equity lines, offerings), calcula su impacto
y riesgo, genera reportes en español con IA, y alerta por Telegram — todo desde una UI web.

> ⚠️ **No es consejo de inversión.** Herramienta de investigación y seguimiento para uso personal.

## Características

- **Detección de dilución desde SEC EDGAR**: escanea 10-K, 10-Q, 8-K, S-1 y otros forms, extrayendo
  warrants, convertibles, programas ATM, shelf registrations, equity lines y offerings.
- **Análisis RAG con IA**: preguntas en lenguaje natural sobre un ticker con respuestas citadas
  (LangChain + ChromaDB + DeepSeek/OpenAI).
- **Reportes y resúmenes generados automáticamente** por LLM (en español).
- **Alertas de Telegram**: bot que avisa de nuevos filings críticos y eventos (RSS monitor).
- **Screener de gaps y halts**: ganadores/perdedores, pre-market/after-market, y halts reales.
- **Watchlist y alertas**: seguimiento de tickers con feed de eventos.
- **Datos de mercado agregados**: Polygon, Finnhub, Benzinga, EODHD, Stonktracker, Finviz,
  Yahoo Finance (yfinance) y noticias de Google News — con rate limiting y caché.

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Python + **FastAPI** + Uvicorn |
| Frontend | **Next.js** (React) |
| Datos | **SQLite** + **Parquet** (pandas) + **ChromaDB** (vectores) |
| IA | **LangChain** + DeepSeek/OpenAI |
| Notificaciones | Bot de **Telegram** |
| APIs de mercado | Polygon, Finnhub, Benzinga, EODHD, Stonktracker, Finviz, yfinance, Google News |

## Estructura

```
backend/
  main.py            # API FastAPI + entry point CLI
  config.py          # Settings (pydantic-settings), lee de .env
  models.py          # Modelos Pydantic del dominio
  dilution_tracker.py# Servicio principal de detección de dilución
  dilution_rag.py    # Extracción RAG de eventos desde filings
  pipeline.py        # Pipeline de escaneo por ticker
  screener.py        # Gap screener + halts
  telegram_bot.py    # Bot de alertas de Telegram
  apis/              # Clientes de APIs de mercado (con rate limiting)
  parsers/           # SEC parser + extracción de tablas + cálculo de dilución
  scanners/          # Scanners: EDGAR index, company facts, EFTS, RSS monitor
  rag/               # Motor RAG (vector store + consultas)
  db/                # SQLite + Parquet
frontend/            # Next.js UI
  pages/             # Rutas (index, ticker, screener, halts, …)
  lib/               # mockData y cliente API
data/                # Datos generados (SQLite, parquet, chroma) — gitignored
_meta/SPEC.md        # Especificación técnica del proyecto
```

## Requisitos

- **Python 3.12+**
- **Node.js 18+** (para el frontend)
- Claves de API para las fuentes que quieras usar (ver `.env.example`)

## Configuración

1. Copia la plantilla y rellena con tus claves:

   ```sh
   cp backend/.env.example backend/.env
   ```

2. Variables principales (todas opcionales salvo las que uses):

   | Variable | Uso |
   |---|---|
   | `DEEPSEEK_API_KEY` / `OPENAI_API_KEY` | LLM para RAG y reportes |
   | `POLYGON_API_KEY`, `FINNHUB_API_KEY`, `BENZINGA_API_KEY`, `EODHD_API_KEY`, `NEWS_API_KEY` | Datos de mercado y noticias |
   | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ADMIN_CHAT_ID` | Alertas de Telegram |
   | `SEC_USER_AGENT` | User-Agent requerido por SEC EDGAR (usa tu email real) |
   | `DATA_DIR`, `CHROMA_DIR` | Rutas de datos y vector store |
   | `API_HOST`, `API_PORT` | Dónde escucha el backend |
   | `FRONTEND_URL` | Origen permitido en CORS |

## Ejecución

### Backend (FastAPI)

```sh
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python main.py serve          # puerto por defecto :8000 (API_PORT para cambiarlo)
```

Swagger/docs en `http://localhost:8000/docs` (o el `API_PORT` configurado).

### Frontend (Next.js)

```sh
cd frontend
npm install
npm run dev                              # http://localhost:3000
```

El frontend apunta al backend vía `NEXT_PUBLIC_BACKEND_URL` (por defecto `http://localhost:8000`).

### Script de arranque todo-en-uno

```sh
./start.command        # lanza backend + frontend, health check, y detiene al cerrar
```

### CLI del backend

`main.py` expone subcomandos además de `serve`:

```sh
.venv/bin/python main.py db init                    # inicializa la base de datos
.venv/bin/python main.py scan AAPL                  # pipeline completo (filings → dilución)
.venv/bin/python main.py scan SPHL --ask "warrant details?"  # con pregunta RAG propia
.venv/bin/python main.py rag AAPL --prompt warrants # consulta RAG por ticker
.venv/bin/python main.py rag <url_filing> --question "..."  # RAG sobre un filing concreto
.venv/bin/python main.py search -q "Full Ratchet"   # búsqueda full-text en SEC EDGAR
.venv/bin/python main.py report                     # reporte de riesgo de dilución
.venv/bin/python main.py monitor                    # monitor RSS/diario de la SEC
.venv/bin/python main.py telegram                   # lanza el bot de alertas
```

Lista completa de subcomandos: `.venv/bin/python main.py --help`.

## API (resumen)

| Endpoint | Descripción |
|---|---|
| `GET /health` | Estado del servicio |
| `POST /rag` | Pregunta RAG sobre un ticker/filing (respuestas citadas) |
| `GET /ticker/{ticker}` | Perfil, quote y valoración de riesgo |
| `GET /ticker/{ticker}/dilution` | Análisis completo de dilución |
| `GET /ticker/{ticker}/news` | Noticias agregadas |
| `GET /dilution/top` | Tickers con mayor dilución detectada |
| `GET /alerts/feed` | Feed de alertas |
| `GET /filings/all` | Filings procesados |
| `GET /search` | Búsqueda de tickers |
| `POST /scan/{ticker}` | Escaneo manual de un ticker |
| `GET /screener/gap` | Gap screener (ganadores/perdedores, pre/post-market) |
| `GET /screener/halts` | Halts reales |

## Seguridad

- Las claves de API **solo** viven en `backend/.env` (gitignored) — nunca en el código.
- `backend/.env.example` es la plantilla pública con placeholders.
- El historial de git no contiene secrets.
- Los datos locales (`data/`) están gitignored.

## Cómo se calcula la dilución

```
S_new = monto_ofrecido / precio_actual
Dilution % = S_new / (acciones_en_circulación + S_new) × 100
```

Niveles de riesgo:

| Dilución | Nivel |
|---|---|
| ≥ 20% | 🔴 Alto |
| 10 – 20% | 🟡 Medio |
| < 10% | 🟢 Bajo |

## Notas

- Los reportes RAG se generan en **español**.
- Las consultas a APIs externas tienen **rate limiting** y caché en SQLite (`data/api_cache.sqlite`).
- El primer escaneo descarga y procesa los filings; puede tardar (se cachea).
