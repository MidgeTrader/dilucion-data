# Project Map — dilucion_data
*Generado: 2026-06-27*

## 📊 Resumen
| Métrica | Valor |
|---|---|
| Archivos Python | 84 |
| Clases | 132 |
| Funciones/métodos | 952 |
| APIs/servicios externos | 6 |
| Paquetes pip | 36 |

## 🚀 Entry Points
- `backend/main.py`
- `backend/main.py::main`
- `backend/telegram_bot.py::run`
- `backend.BAK.20260627_033113/main.py`
- `backend.BAK.20260627_033113/main.py::main`
- `backend.BAK.20260627_033113/telegram_bot.py::run`

## 🔗 Dependencias entre archivos
```mermaid
graph LR;
```

## 📁 Archivos
| Archivo | Clases | Funciones | APIs detectadas | LOCs |
|---|---|---|---|---|
| `backend/apis/__init__.py` | 0 | 0 | — | 13 |
| `backend/apis/_rate_limit.py` | 1 | 2 | — | 21 |
| `backend/apis/benzinga_client.py` | 1 | 3 | — | 80 |
| `backend/apis/connection_pool.py` | 0 | 2 | — | 63 |
| `backend/apis/data_enrichment.py` | 1 | 4 | — | 160 |
| `backend/apis/eodhd_client.py` | 1 | 4 | — | 109 |
| `backend/apis/finnhub_client.py` | 1 | 4 | — | 138 |
| `backend/apis/finviz_client.py` | 1 | 5 | — | 139 |
| `backend/apis/google_news_client.py` | 1 | 2 | — | 79 |
| `backend/apis/news_aggregator.py` | 1 | 7 | — | 138 |
| `backend/apis/polygon_client.py` | 1 | 8 | env_var:apikey | 180 |
| `backend/apis/stonktracker_client.py` | 1 | 4 | — | 104 |
| `backend/apis/yfinance_client.py` | 1 | 6 | yfinance | 163 |
| `backend/cache.py` | 1 | 7 | — | 120 |
| `backend/config.py` | 1 | 8 | env_var:api_key | 104 |
| `backend/db/__init__.py` | 0 | 0 | — | 6 |
| `backend/db/database.py` | 2 | 31 | — | 330 |
| `backend/db/parquet_db.py` | 1 | 16 | pandas | 278 |
| `backend/dilution_rag.py` | 1 | 20 | — | 533 |
| `backend/dilution_tracker.py` | 1 | 10 | — | 411 |
| `backend/langchain_rag.py` | 0 | 0 | — | 2 |
| `backend/main.py` | 1 | 36 | fastapi, streamlit | 854 |
| `backend/models.py` | 31 | 0 | — | 350 |
| `backend/parquet_db.py` | 0 | 0 | — | 2 |
| `backend/parsers/__init__.py` | 0 | 0 | — | 6 |
| `backend/parsers/dilution_calculator.py` | 2 | 3 | — | 140 |
| `backend/parsers/sec_parser.py` | 5 | 10 | — | 381 |
| `backend/parsers/table_extractor.py` | 1 | 19 | — | 400 |
| `backend/pipeline.py` | 1 | 5 | — | 210 |
| `backend/prompts.py` | 0 | 0 | — | 2 |
| `backend/rag/__init__.py` | 0 | 0 | — | 5 |
| `backend/rag/prompts.py` | 0 | 2 | — | 51 |
| `backend/rag/rag_engine.py` | 1 | 7 | — | 186 |
| `backend/scanners/__init__.py` | 0 | 0 | — | 8 |
| `backend/scanners/company_facts.py` | 1 | 7 | — | 137 |
| `backend/scanners/dilution_scanner.py` | 1 | 6 | pandas | 140 |
| `backend/scanners/efts_search.py` | 1 | 3 | — | 103 |
| `backend/scanners/rss_monitor.py` | 1 | 11 | — | 156 |
| `backend/screener.py` | 1 | 6 | yfinance | 139 |
| `backend/sec_loader.py` | 0 | 0 | — | 2 |
| `backend/seed_data/buru_dilution.py` | 0 | 0 | — | 169 |
| `backend/telegram_bot.py` | 1 | 6 | — | 306 |
| `backend.BAK.20260627_033113/apis/__init__.py` | 0 | 0 | — | 13 |
| `backend.BAK.20260627_033113/apis/_rate_limit.py` | 1 | 2 | — | 21 |
| `backend.BAK.20260627_033113/apis/benzinga_client.py` | 1 | 3 | — | 80 |
| `backend.BAK.20260627_033113/apis/connection_pool.py` | 0 | 2 | — | 63 |
| `backend.BAK.20260627_033113/apis/data_enrichment.py` | 1 | 4 | — | 160 |
| `backend.BAK.20260627_033113/apis/eodhd_client.py` | 1 | 4 | — | 109 |
| `backend.BAK.20260627_033113/apis/finnhub_client.py` | 1 | 4 | — | 138 |
| `backend.BAK.20260627_033113/apis/finviz_client.py` | 1 | 5 | — | 139 |
| `backend.BAK.20260627_033113/apis/google_news_client.py` | 1 | 2 | — | 79 |
| `backend.BAK.20260627_033113/apis/news_aggregator.py` | 1 | 7 | — | 138 |
| `backend.BAK.20260627_033113/apis/polygon_client.py` | 1 | 8 | env_var:apikey | 180 |
| `backend.BAK.20260627_033113/apis/stonktracker_client.py` | 1 | 4 | — | 104 |
| `backend.BAK.20260627_033113/apis/yfinance_client.py` | 1 | 6 | yfinance | 163 |
| `backend.BAK.20260627_033113/cache.py` | 1 | 7 | — | 120 |
| `backend.BAK.20260627_033113/config.py` | 1 | 8 | env_var:api_key | 104 |
| `backend.BAK.20260627_033113/db/__init__.py` | 0 | 0 | — | 6 |
| `backend.BAK.20260627_033113/db/database.py` | 2 | 31 | — | 330 |
| `backend.BAK.20260627_033113/db/parquet_db.py` | 1 | 16 | pandas | 276 |
| `backend.BAK.20260627_033113/dilution_rag.py` | 1 | 20 | — | 533 |
| `backend.BAK.20260627_033113/dilution_tracker.py` | 1 | 10 | — | 411 |
| `backend.BAK.20260627_033113/langchain_rag.py` | 0 | 0 | — | 2 |
| `backend.BAK.20260627_033113/main.py` | 1 | 36 | fastapi, streamlit | 830 |
| `backend.BAK.20260627_033113/models.py` | 31 | 0 | — | 350 |
| `backend.BAK.20260627_033113/parquet_db.py` | 0 | 0 | — | 2 |
| `backend.BAK.20260627_033113/parsers/__init__.py` | 0 | 0 | — | 6 |
| `backend.BAK.20260627_033113/parsers/dilution_calculator.py` | 2 | 3 | — | 140 |
| `backend.BAK.20260627_033113/parsers/sec_parser.py` | 5 | 10 | — | 381 |
| `backend.BAK.20260627_033113/parsers/table_extractor.py` | 1 | 19 | — | 400 |
| `backend.BAK.20260627_033113/pipeline.py` | 1 | 5 | — | 210 |
| `backend.BAK.20260627_033113/prompts.py` | 0 | 0 | — | 2 |
| `backend.BAK.20260627_033113/rag/__init__.py` | 0 | 0 | — | 5 |
| `backend.BAK.20260627_033113/rag/prompts.py` | 0 | 2 | — | 51 |
| `backend.BAK.20260627_033113/rag/rag_engine.py` | 1 | 7 | — | 186 |
| `backend.BAK.20260627_033113/scanners/__init__.py` | 0 | 0 | — | 8 |
| `backend.BAK.20260627_033113/scanners/company_facts.py` | 1 | 7 | — | 137 |
| `backend.BAK.20260627_033113/scanners/dilution_scanner.py` | 1 | 6 | pandas | 140 |
| `backend.BAK.20260627_033113/scanners/efts_search.py` | 1 | 3 | — | 103 |
| `backend.BAK.20260627_033113/scanners/rss_monitor.py` | 1 | 11 | — | 156 |
| `backend.BAK.20260627_033113/screener.py` | 1 | 6 | yfinance | 139 |
| `backend.BAK.20260627_033113/sec_loader.py` | 0 | 0 | — | 2 |
| `backend.BAK.20260627_033113/seed_data/buru_dilution.py` | 0 | 0 | — | 169 |
| `backend.BAK.20260627_033113/telegram_bot.py` | 1 | 6 | — | 306 |

## 🏛️ Clases
| Clase | Archivo | Métodos | Hereda de |
|---|---|---|---|
| `RateLimiter` | `backend/apis/_rate_limit.py` | __init__, wait | — |
| `BenzingaClient` | `backend/apis/benzinga_client.py` | __init__, get_news | — |
| `DataEnrichment` | `backend/apis/data_enrichment.py` | __init__, get_ticker_profile, get_company_news, refresh_tickers_to_parquet | — |
| `EodhdClient` | `backend/apis/eodhd_client.py` | __init__, resolve_symbol, _get_json, get_news | — |
| `FinnhubClient` | `backend/apis/finnhub_client.py` | __init__, get_quote, get_company_profile, get_company_news | — |
| `FinvizClient` | `backend/apis/finviz_client.py` | __init__, get_profile_fields, _parse_number, _parse_pct | — |
| `GoogleNewsClient` | `backend/apis/google_news_client.py` | __init__, get_news | — |
| `NewsAggregator` | `backend/apis/news_aggregator.py` | __init__, get_all_news, _filings_to_news, _dedupe_and_sort, _sort_key | — |
| `PolygonClient` | `backend/apis/polygon_client.py` | __init__, _get, fetch_active_tickers, get_ticker_details, get_candles, get_shares_outstanding, get_news | — |
| `StonktrackerClient` | `backend/apis/stonktracker_client.py` | __init__, get_borrow_data, _fetch_page, _extract_borrow_fee | — |
| `YFinanceClient` | `backend/apis/yfinance_client.py` | __init__, get_quote, get_price, get_profile_fields, get_shares_outstanding, get_news | — |
| `TTLCache` | `backend/cache.py` | __init__, _get_conn, _init_db, get, set, delete, purge_expired | — |
| `Settings` | `backend/config.py` | resolve_path, ensure_directories, validate_rag_keys, companies_parquet, filings_parquet, cache_db_path, sqlite_db_path | BaseSettings |
| `SQLiteBackend` | `backend/db/database.py` | __init__, _conn, init_schema, upsert_company, insert_alert, insert_rag, get_top, get_recent_alerts, add_watchlist, remove_watchlist, get_watchlist, get_all_watchers_for_ticker, set_state, get_state, stats | — |
| `Database` | `backend/db/database.py` | __init__, init, get_mode, save_company, save_dilution_alert, save_rag_analysis, get_top, get_recent_alerts, get_alerts_feed, add_watchlist, remove_watchlist, get_watchlist, get_watchers_for_ticker, set_bot_state, get_bot_state, stats | — |
| `ParquetDB` | `backend/db/parquet_db.py` | __init__, inicializar, init, _read_companies, _read_filings, upsert_company, upsert_filing, registrar_alerta, query_top_dilution, query_by_ticker, get_all_filings, get_filings_by_ticker, get_company_by_ticker, search_companies, report_summary, _row_to_filing | — |
| `DilutionRAGExtractor` | `backend/dilution_rag.py` | __init__, _init_cache, _get_cache_conn, _cache_key, _cache_get, _cache_set, _get_llm, _vectorize_filing, _query_json, _parse_json, extract_warrants, extract_cash, extract_offering, extract_convertibles, extract_atms, extract_shelf, extract_equity_lines, generate_headline, generate_research_report, extract_all | — |
| `DilutionTrackerService` | `backend/dilution_tracker.py` | _load_seeds, __init__, _rag_extractor, _get_parsed, _filing_texts, _get_filing_urls, _rag_batch, _check_cache_freshness, get_dilution_data, _guess_exchange | — |
| `RagBody` | `backend/main.py` | — | BaseModel |
| `RiskLevel` | `backend/models.py` | — | str, Enum |
| `Company` | `backend/models.py` | — | BaseModel |
| `FilingDilution` | `backend/models.py` | — | BaseModel |
| `CriticalFiling` | `backend/models.py` | — | BaseModel |
| `RSSAlert` | `backend/models.py` | — | BaseModel |
| `SearchHit` | `backend/models.py` | — | BaseModel |
| `Citation` | `backend/models.py` | — | BaseModel |
| `RAGRequest` | `backend/models.py` | — | BaseModel |
| `RAGResponse` | `backend/models.py` | — | BaseModel |
| `ScanResult` | `backend/models.py` | — | BaseModel |
| `PipelineResult` | `backend/models.py` | — | BaseModel |
| `QuoteData` | `backend/models.py` | — | BaseModel |
| `ShortInterestData` | `backend/models.py` | — | BaseModel |
| `TickerProfile` | `backend/models.py` | — | BaseModel |
| `RiskAssessment` | `backend/models.py` | — | BaseModel |
| `CandlePoint` | `backend/models.py` | — | BaseModel |
| `NewsArticle` | `backend/models.py` | — | BaseModel |
| `SECFilingMeta` | `backend/models.py` | — | BaseModel |
| `CashPosition` | `backend/models.py` | — | BaseModel |
| `PendingOffering` | `backend/models.py` | — | BaseModel |
| `ShelfRegistration` | `backend/models.py` | — | BaseModel |
| `ATMProgram` | `backend/models.py` | — | BaseModel |
| `WarrantIssue` | `backend/models.py` | — | BaseModel |
| `ConvertibleIssue` | `backend/models.py` | — | BaseModel |
| `EquityLine` | `backend/models.py` | — | BaseModel |
| `CompletedOffering` | `backend/models.py` | — | BaseModel |
| `LockUpAgreement` | `backend/models.py` | — | BaseModel |
| `NasdaqComplianceItem` | `backend/models.py` | — | BaseModel |
| `ReverseSplit` | `backend/models.py` | — | BaseModel |
| `DilutionTrackerData` | `backend/models.py` | — | BaseModel |
| `PendingDilutionEvent` | `backend/models.py` | — | BaseModel |
| `DilutionResult` | `backend/parsers/dilution_calculator.py` | — | BaseModel |
| `DilutionCalculator` | `backend/parsers/dilution_calculator.py` | extract_offering_amount, classify_risk, calculate | — |
| `SECRateLimitError` | `backend/parsers/sec_parser.py` | — | Exception |
| `SECAccessError` | `backend/parsers/sec_parser.py` | — | Exception |
| `ExtractionResult` | `backend/parsers/sec_parser.py` | — | BaseModel |
| `ParsedFiling` | `backend/parsers/sec_parser.py` | — | — |
| `SECParser` | `backend/parsers/sec_parser.py` | __init__, extract_accession, extract_cik, download, clean_html, extract_keywords, _parse_amount, parse, _detect_form, load_from_url | — |
| `TableExtractor` | `backend/parsers/table_extractor.py` | __init__, fetch_html, extract_tables, _is_warrant_table, _is_convertible_table, _is_offering_table, _is_shelf_table, _rows_to_text, _find_adjacent_amount, _parse_warrant_table, _row_to_warrant, _parse_convertible_table, _row_to_convertible, _parse_offering_table, _find_header_row, _classify_offering, _parse_shelf_amount, _extract_equity_lines, fetch_and_extract | — |
| `ScanPipeline` | `backend/pipeline.py` | __init__, _get_rag, resolve_cik, scan_ticker | — |
| `RAGEngine` | `backend/rag/rag_engine.py` | __init__, _get_llm, _collection_name, _get_or_create_vectorstore, query_filing, scan_url, query_ticker | — |
| `CompanyFactsClient` | `backend/scanners/company_facts.py` | __init__, _get, resolve_cik_from_ticker, get_submissions, get_recent_filings, get_shares_outstanding, get_company_info | — |
| `DilutionScanner` | `backend/scanners/dilution_scanner.py` | __init__, _download_index, parse_index, filter_critical, scan_date, scan_range | — |
| `EFTSSearch` | `backend/scanners/efts_search.py` | __init__, search, search_all_defaults | — |
| `RSSMonitor` | `backend/scanners/rss_monitor.py` | __init__, _init_dedup_db, _is_seen, _mark_seen, fetch_feed, parse_feed, _extract_form_type, _extract_accession, _extract_cik, poll_once, run_daemon | — |
| `GapScreener` | `backend/screener.py` | __init__, _get_yf_data, scan, _fmt_reason, halts | — |
| `TelegramBot` | `backend/telegram_bot.py` | __init__, run | — |
| `RateLimiter` | `backend.BAK.20260627_033113/apis/_rate_limit.py` | __init__, wait | — |
| `BenzingaClient` | `backend.BAK.20260627_033113/apis/benzinga_client.py` | __init__, get_news | — |
| `DataEnrichment` | `backend.BAK.20260627_033113/apis/data_enrichment.py` | __init__, get_ticker_profile, get_company_news, refresh_tickers_to_parquet | — |
| `EodhdClient` | `backend.BAK.20260627_033113/apis/eodhd_client.py` | __init__, resolve_symbol, _get_json, get_news | — |
| `FinnhubClient` | `backend.BAK.20260627_033113/apis/finnhub_client.py` | __init__, get_quote, get_company_profile, get_company_news | — |
| `FinvizClient` | `backend.BAK.20260627_033113/apis/finviz_client.py` | __init__, get_profile_fields, _parse_number, _parse_pct | — |
| `GoogleNewsClient` | `backend.BAK.20260627_033113/apis/google_news_client.py` | __init__, get_news | — |
| `NewsAggregator` | `backend.BAK.20260627_033113/apis/news_aggregator.py` | __init__, get_all_news, _filings_to_news, _dedupe_and_sort, _sort_key | — |
| `PolygonClient` | `backend.BAK.20260627_033113/apis/polygon_client.py` | __init__, _get, fetch_active_tickers, get_ticker_details, get_candles, get_shares_outstanding, get_news | — |
| `StonktrackerClient` | `backend.BAK.20260627_033113/apis/stonktracker_client.py` | __init__, get_borrow_data, _fetch_page, _extract_borrow_fee | — |
| `YFinanceClient` | `backend.BAK.20260627_033113/apis/yfinance_client.py` | __init__, get_quote, get_price, get_profile_fields, get_shares_outstanding, get_news | — |
| `TTLCache` | `backend.BAK.20260627_033113/cache.py` | __init__, _get_conn, _init_db, get, set, delete, purge_expired | — |
| `Settings` | `backend.BAK.20260627_033113/config.py` | resolve_path, ensure_directories, validate_rag_keys, companies_parquet, filings_parquet, cache_db_path, sqlite_db_path | BaseSettings |
| `SQLiteBackend` | `backend.BAK.20260627_033113/db/database.py` | __init__, _conn, init_schema, upsert_company, insert_alert, insert_rag, get_top, get_recent_alerts, add_watchlist, remove_watchlist, get_watchlist, get_all_watchers_for_ticker, set_state, get_state, stats | — |
| `Database` | `backend.BAK.20260627_033113/db/database.py` | __init__, init, get_mode, save_company, save_dilution_alert, save_rag_analysis, get_top, get_recent_alerts, get_alerts_feed, add_watchlist, remove_watchlist, get_watchlist, get_watchers_for_ticker, set_bot_state, get_bot_state, stats | — |
| `ParquetDB` | `backend.BAK.20260627_033113/db/parquet_db.py` | __init__, inicializar, init, _read_companies, _read_filings, upsert_company, upsert_filing, registrar_alerta, query_top_dilution, query_by_ticker, get_all_filings, get_filings_by_ticker, get_company_by_ticker, search_companies, report_summary, _row_to_filing | — |
| `DilutionRAGExtractor` | `backend.BAK.20260627_033113/dilution_rag.py` | __init__, _init_cache, _get_cache_conn, _cache_key, _cache_get, _cache_set, _get_llm, _vectorize_filing, _query_json, _parse_json, extract_warrants, extract_cash, extract_offering, extract_convertibles, extract_atms, extract_shelf, extract_equity_lines, generate_headline, generate_research_report, extract_all | — |
| `DilutionTrackerService` | `backend.BAK.20260627_033113/dilution_tracker.py` | _load_seeds, __init__, _rag_extractor, _get_parsed, _filing_texts, _get_filing_urls, _rag_batch, _check_cache_freshness, get_dilution_data, _guess_exchange | — |
| `RagBody` | `backend.BAK.20260627_033113/main.py` | — | BaseModel |
| `RiskLevel` | `backend.BAK.20260627_033113/models.py` | — | str, Enum |
| `Company` | `backend.BAK.20260627_033113/models.py` | — | BaseModel |
| `FilingDilution` | `backend.BAK.20260627_033113/models.py` | — | BaseModel |
| `CriticalFiling` | `backend.BAK.20260627_033113/models.py` | — | BaseModel |
| `RSSAlert` | `backend.BAK.20260627_033113/models.py` | — | BaseModel |
| `SearchHit` | `backend.BAK.20260627_033113/models.py` | — | BaseModel |
| `Citation` | `backend.BAK.20260627_033113/models.py` | — | BaseModel |
| `RAGRequest` | `backend.BAK.20260627_033113/models.py` | — | BaseModel |
| `RAGResponse` | `backend.BAK.20260627_033113/models.py` | — | BaseModel |
| `ScanResult` | `backend.BAK.20260627_033113/models.py` | — | BaseModel |
| `PipelineResult` | `backend.BAK.20260627_033113/models.py` | — | BaseModel |
| `QuoteData` | `backend.BAK.20260627_033113/models.py` | — | BaseModel |
| `ShortInterestData` | `backend.BAK.20260627_033113/models.py` | — | BaseModel |
| `TickerProfile` | `backend.BAK.20260627_033113/models.py` | — | BaseModel |
| `RiskAssessment` | `backend.BAK.20260627_033113/models.py` | — | BaseModel |
| `CandlePoint` | `backend.BAK.20260627_033113/models.py` | — | BaseModel |
| `NewsArticle` | `backend.BAK.20260627_033113/models.py` | — | BaseModel |
| `SECFilingMeta` | `backend.BAK.20260627_033113/models.py` | — | BaseModel |
| `CashPosition` | `backend.BAK.20260627_033113/models.py` | — | BaseModel |
| `PendingOffering` | `backend.BAK.20260627_033113/models.py` | — | BaseModel |
| `ShelfRegistration` | `backend.BAK.20260627_033113/models.py` | — | BaseModel |
| `ATMProgram` | `backend.BAK.20260627_033113/models.py` | — | BaseModel |
| `WarrantIssue` | `backend.BAK.20260627_033113/models.py` | — | BaseModel |
| `ConvertibleIssue` | `backend.BAK.20260627_033113/models.py` | — | BaseModel |
| `EquityLine` | `backend.BAK.20260627_033113/models.py` | — | BaseModel |
| `CompletedOffering` | `backend.BAK.20260627_033113/models.py` | — | BaseModel |
| `LockUpAgreement` | `backend.BAK.20260627_033113/models.py` | — | BaseModel |
| `NasdaqComplianceItem` | `backend.BAK.20260627_033113/models.py` | — | BaseModel |
| `ReverseSplit` | `backend.BAK.20260627_033113/models.py` | — | BaseModel |
| `DilutionTrackerData` | `backend.BAK.20260627_033113/models.py` | — | BaseModel |
| `PendingDilutionEvent` | `backend.BAK.20260627_033113/models.py` | — | BaseModel |
| `DilutionResult` | `backend.BAK.20260627_033113/parsers/dilution_calculator.py` | — | BaseModel |
| `DilutionCalculator` | `backend.BAK.20260627_033113/parsers/dilution_calculator.py` | extract_offering_amount, classify_risk, calculate | — |
| `SECRateLimitError` | `backend.BAK.20260627_033113/parsers/sec_parser.py` | — | Exception |
| `SECAccessError` | `backend.BAK.20260627_033113/parsers/sec_parser.py` | — | Exception |
| `ExtractionResult` | `backend.BAK.20260627_033113/parsers/sec_parser.py` | — | BaseModel |
| `ParsedFiling` | `backend.BAK.20260627_033113/parsers/sec_parser.py` | — | — |
| `SECParser` | `backend.BAK.20260627_033113/parsers/sec_parser.py` | __init__, extract_accession, extract_cik, download, clean_html, extract_keywords, _parse_amount, parse, _detect_form, load_from_url | — |
| `TableExtractor` | `backend.BAK.20260627_033113/parsers/table_extractor.py` | __init__, fetch_html, extract_tables, _is_warrant_table, _is_convertible_table, _is_offering_table, _is_shelf_table, _rows_to_text, _find_adjacent_amount, _parse_warrant_table, _row_to_warrant, _parse_convertible_table, _row_to_convertible, _parse_offering_table, _find_header_row, _classify_offering, _parse_shelf_amount, _extract_equity_lines, fetch_and_extract | — |
| `ScanPipeline` | `backend.BAK.20260627_033113/pipeline.py` | __init__, _get_rag, resolve_cik, scan_ticker | — |
| `RAGEngine` | `backend.BAK.20260627_033113/rag/rag_engine.py` | __init__, _get_llm, _collection_name, _get_or_create_vectorstore, query_filing, scan_url, query_ticker | — |
| `CompanyFactsClient` | `backend.BAK.20260627_033113/scanners/company_facts.py` | __init__, _get, resolve_cik_from_ticker, get_submissions, get_recent_filings, get_shares_outstanding, get_company_info | — |
| `DilutionScanner` | `backend.BAK.20260627_033113/scanners/dilution_scanner.py` | __init__, _download_index, parse_index, filter_critical, scan_date, scan_range | — |
| `EFTSSearch` | `backend.BAK.20260627_033113/scanners/efts_search.py` | __init__, search, search_all_defaults | — |
| `RSSMonitor` | `backend.BAK.20260627_033113/scanners/rss_monitor.py` | __init__, _init_dedup_db, _is_seen, _mark_seen, fetch_feed, parse_feed, _extract_form_type, _extract_accession, _extract_cik, poll_once, run_daemon | — |
| `GapScreener` | `backend.BAK.20260627_033113/screener.py` | __init__, _get_yf_data, scan, _fmt_reason, halts | — |
| `TelegramBot` | `backend.BAK.20260627_033113/telegram_bot.py` | __init__, run | — |

## 🌐 APIs y Servicios Externos
| Servicio | Tipo |
|---|---|
| 🔑 `api_key` (variable entorno) | environment |
| 🔑 `apikey` (variable entorno) | environment |
| `fastapi` | web |
| `pandas` | data |
| `streamlit` | viz |
| `yfinance` | market_data |

## 📦 Paquetes Externos
```
apis
asyncio
bs4
cache
config
contextlib
db
dilution_rag
dilution_tracker
email
finvizfinance
hashlib
httpx
langchain_chroma
langchain_core
langchain_openai
langchain_text_splitters
models
parsers
pipeline
playwright
pydantic
pydantic_settings
rag
requests
scanners
screener
seed_data
sqlite3
telegram
telegram_bot
tenacity
threading
urllib
uvicorn
xml
```

## 🧠 Para Claude (memoria rápida)

Relaciones clave del proyecto:
- **`backend/apis/__init__.py`** | deps: apis
- **`backend/apis/benzinga_client.py`** | deps: apis, cache, config, models, xml
- **`backend/apis/connection_pool.py`** | deps: httpx
- **`backend/apis/data_enrichment.py`** | deps: apis, cache, config, db, models
- **`backend/apis/eodhd_client.py`** | deps: apis, cache, config, models, tenacity
- **`backend/apis/finnhub_client.py`** | deps: apis, cache, config, models, tenacity
- **`backend/apis/finviz_client.py`** | deps: cache, config, finvizfinance
- **`backend/apis/google_news_client.py`** | deps: apis, cache, config, email, models
- **`backend/apis/news_aggregator.py`** | deps: apis, cache, config, models
- **`backend/apis/polygon_client.py`** | APIs: env_var:apikey | deps: apis, cache, config, models, tenacity
- **`backend/apis/stonktracker_client.py`** | deps: apis, cache, httpx, models
- **`backend/apis/yfinance_client.py`** | APIs: yfinance | deps: cache, config, models
- **`backend/cache.py`** | deps: sqlite3, threading
- **`backend/config.py`** | APIs: env_var:api_key | deps: pydantic, pydantic_settings
- **`backend/db/__init__.py`** | deps: db
- **`backend/db/database.py`** | deps: config, contextlib, db, models, sqlite3
- **`backend/db/parquet_db.py`** | APIs: pandas | deps: config, models
- **`backend/dilution_rag.py`** | deps: config, hashlib, langchain_chroma, langchain_core, langchain_openai
- **`backend/dilution_tracker.py`** | deps: config, dilution_rag, hashlib, models, parsers

---
*Generado por [graphify-lite](https://github.com/safishamsi/graphify). 84 archivos analizados.*