---
tags: [project/spec]
aliases: [SEC Dilution Radar Spec, Dilución Data Spec]
---

# 📋 SPEC — SEC Dilution Radar / Dilución Data

> [!important] Fuente única de verdad del proyecto.
> Si el código, la documentación y la implementación entran en conflicto, esta especificación tiene prioridad.

| Campo | Valor |
|---|---|
| Versión | 1.0 |
| Estado | En revisión |
| Owner | rafael |
| Última actualización | 2026-07-14 |

---

## 0. Glosario

| Término | Definición |
|---|---|
| Dilución | Emisión de nuevas acciones que reduce el porcentaje de ownership de los accionistas existentes |
| Shelf registration | Registro S-3 que permite emitir acciones incrementalmente sin nuevo filing |
| ATM | At-The-Market offering — venta discrecional de acciones al precio de mercado |
| Warrant | Opción de compra de acciones emitida como parte de una oferta |
| Full ratchet | Cláusula anti-dilución que ajusta el precio de conversión al menor precio de futuras rondas |
| RAG | Retrieval-Augmented Generation — extracción de datos estructurados vía LLM + embeddings |
| CIK | Central Index Key — identificador único de la SEC para cada compañía |
| SEC EDGAR | Sistema de la SEC donde las empresas públicas presentan sus filings |

---

## 1. Propósito

### Objetivo

Detectar anuncios de dilución de equity en filings de la SEC **antes de que se ejecuten en el mercado**, dando ~1 día de ventaja sobre el público.

- **Usuarios:** Trader retail/institucional que busca anticipar dilución antes de que impacte el precio
- **Problema que resuelve:** NewsEdge Alert cuesta $221/mes; esta app es ~$0.03/día
- **Filosofía:** SEC anuncia (filing) → luego ejecuta (diluye). Con RSS polling + 1 llamada LLM/día ganas la ventaja

### No-objetivos

- No es un ejecutor de trades (solo análisis/señal)
- No reemplaza due diligence fundamental
- No cubre mercados fuera de US (solo SEC EDGAR)
- No predice precio — solo identifica riesgo de dilución

### Stakeholders

| Rol | Nombre | Responsabilidad |
|---|---|---|
| Owner/Dev | rafael | Desarrollo completo, despliegue, monitoreo |

### Supuestos y dependencias

- SEC.gov y data.sec.gov están disponibles (sin SLA)
- APIs externas (Polygon, Finnhub, yfinance, etc.) pueden fallar — el sistema debe degradarse, no romperse
- El DNS/resolución de nombres puede fallar intermitentemente → timeouts cortos (5s connect)
- Las API keys están en `.env` (gitignored) — NUNCA en código

---

## 2. Requisitos Funcionales

### FR-001: Escaneo de ticker individual

- **Prioridad:** Must
- **Estado:** Done
- **Descripción:** Dado un ticker, obtener su perfil financiero + últimos filings SEC + calcular riesgo de dilución
- **Criterios de aceptación:**
  - GIVEN un ticker válido WHEN se consulta `/ticker/{ticker}` THEN devuelve profile + filings + risk en < 30s
  - GIVEN un ticker sin filings en caché WHEN se consulta THEN auto-scan desde SEC
  - GIVEN un ticker inválido WHEN se consulta THEN devuelve error 400
- **Tests relacionados:** FR-001-T001, FR-001-T002 (por crear)

### FR-002: Monitoreo RSS SEC en tiempo real

- **Prioridad:** Must
- **Estado:** Done
- **Descripción:** Polear el RSS de EDGAR cada ~2 minutos para detectar filings de dilución (S-1, S-3, 424B5, 8-K items 3.02/5.03)
- **Criterios de aceptación:**
  - GIVEN un nuevo filing de dilución WHEN el RSS se polea THEN se registra en DB y se notifica
  - GIVEN un filing duplicado WHEN se polea de nuevo THEN se ignora (dedup por accession_number)

### FR-003: Dashboard web

- **Prioridad:** Must
- **Estado:** Done
- **Descripción:** Frontend Next.js que muestra top diluciones, heatmap, alerts feed, detalle por ticker
- **Endpoints:**
  - `GET /ticker/{ticker}` — perfil completo (cache 15min)
  - `GET /ticker/{ticker}/dilution` — detalle de dilución (cache 15min)
  - `GET /dilution/top` — top 20 riesgos de dilución
  - `GET /alerts/feed` — últimas alertas (7 días)
  - `GET /search?q=` — búsqueda de tickers/companies

### FR-004: RAG Analysis

- **Prioridad:** Should
- **Estado:** Done
- **Descripción:** Extracción de datos estructurados de filings SEC vía LLM (DeepSeek + OpenAI embeddings) para identificar warrants, ATMs, convertibles, cash position
- **Criterios de aceptación:**
  - GIVEN un filing con warrants WHEN se ejecuta RAG THEN extrae count, exercise_price, protección
  - GIVEN un filing sin datos relevantes WHEN se ejecuta RAG THEN retorna null sin error

### FR-005: Screener de gaps y halts

- **Prioridad:** Could
- **Estado:** Done
- **Descripción:** Escanea Yahoo Finance penny stocks activos y halts de Nasdaq para identificar movimientos de precio anómalos
- **Endpoints:** `GET /screener/gap`, `GET /screener/halts`

### FR-006: Telegram bot

- **Prioridad:** Could
- **Estado:** Done
- **Descripción:** Bot de Telegram para recibir alertas de dilución y consultar tickers
- **Comandos:** watchlist, alertas, top diluciones

---

## 3. Reglas de Código

- **Lenguaje:** Código existente en inglés (no traducir). Código nuevo en inglés (consistente con el proyecto)
- **Type hints:** Obligatorios en toda función pública (tipado nominal)
- **Manejo de errores:** NUNCA `except: pass`. Capturar excepción específica, loguear con contexto
- **Docstrings:** Formato Google (`Args:` / `Returns:` / `Raises:`) en funciones públicas
- **Secrets:** Siempre en `.env` (gitignored). Validar existencia al startup con `raise`
- **Logging:** Con contexto (`logger.warning("X failed for %s: %s", ticker, exc)`)
- **SRP:** Funciones pequeñas, una responsabilidad. La función `get_dilution_data` (~220 líneas) es deuda técnica conocida
- **APIs externas:** Timeout connect=5s, read=15s. Degradación controlada si fallan
- **Cache:** Parquet en memoria (TTL 10s). Respuesta API cacheada 15min. No abrir archivos por request

---

## 4. Manejo de Errores

### Taxonomía

| Tipo | Ejemplo | Manejo |
|---|---|---|
| Validación | Ticker inválido, CIK no resuelto | HTTP 400, mensaje claro |
| Negocio | Sin filings disponibles, sin datos de precio | Devuelve perfil parcial, no error |
| Infraestructura | API externa caída, timeout DNS, DB lockeada | Log warning, degradación controlada, try/except con fallback |
| Cache | SQLite lock, archivo no encontrado | Retorna None, log debug, continúa |

### Reglas

- **NUNCA** `except: pass` — mínimo `logger.debug("context: %s", exc)`
- **NUNCA** secrets en logs (API keys, tokens)
- Fallos de API externa → warning + continuar con datos parciales
- Fallos de cache → retry transparente (TTLCache con reconnect por thread)
- Timeouts de red → 5s connect / 15s read (connection_pool.py)
- Si DNS falla → timeout rápido, no cascada de FDs

---

## 5. Definición de Terminado (DoD)

Una tarea está completa solo si:

- [ ] Código compila sin errores de sintaxis
- [ ] Type hints presentes en funciones nuevas/modificadas
- [ ] `except: pass` no introducidos (revisar diff)
- [ ] API keys no hardcodeadas (solo `.env`)
- [ ] Logging con contexto (no mensajes genéricos)
- [ ] Sin deuda técnica no documentada (agregar a Known Debt si aplica)
- [ ] La app arranca sin errores

### Deuda Técnica Conocida

| Ítem | Impacto | Plan |
|---|---|---|
| `get_dilution_data()` ~220 líneas en `dilution_tracker.py` | Violación SRP, difícil de testear | Extraer métodos de extracción en próxima iteración |
| Sin tests automatizados | Riesgo de regresiones | Prioridad post-MVP |
| API keys en `.env` sin cifrar | Riesgo si el equipo crece | Evaluar secret manager si hay >1 developer |

---

## 6. Change Log

| Versión | Fecha | Cambios | Autor |
|---|---|---|---|
| v1.0 | 2026-07-14 | Especificación inicial (light: secciones 0, 1, 2, 3, 4, 5) | rafael |
