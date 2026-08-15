/** API client — fetches real data from backend. Backend caches in parquet + SQLite. */

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

// Dedup de peticiones en vuelo: React StrictMode (dev) ejecuta los effects
// dos veces, disparando cada fetch por duplicado. Compartiendo la misma
// promesa, la segunda llamada no genera otra petición de red.
const _inflight = new Map();

function dedup(key, fn) {
  if (_inflight.has(key)) return _inflight.get(key);
  const p = fn().finally(() => _inflight.delete(key));
  _inflight.set(key, p);
  return p;
}

export async function fetchTopDilution(limit = 15) {
  return dedup(`top:${limit}`, async () => {
    const r = await fetch(`${BACKEND}/dilution/top?limit=${limit}`);
    if (!r.ok) throw new Error('Failed to load dilution data');
    return r.json();
  });
}

export async function fetchAlertsFeed(limit = 10) {
  return dedup(`alerts:${limit}`, async () => {
    const r = await fetch(`${BACKEND}/alerts/feed?limit=${limit}`);
    if (!r.ok) throw new Error('Failed to load alerts');
    return r.json();
  });
}

export async function fetchAllFilings(limit = 100) {
  return dedup(`filings:${limit}`, async () => {
    const r = await fetch(`${BACKEND}/filings/all?limit=${limit}`);
    if (!r.ok) throw new Error('Failed to load filings');
    return r.json();
  });
}

export async function fetchTickerNews(ticker, limit = 20) {
  return dedup(`news:${ticker.toUpperCase()}:${limit}`, async () => {
    const r = await fetch(`${BACKEND}/ticker/${ticker.toUpperCase()}/news?limit=${limit}`);
    if (!r.ok) throw new Error(`Failed to load news for ${ticker}`);
    return r.json();
  });
}

export async function fetchTicker(ticker) {
  return dedup(`ticker:${ticker.toUpperCase()}`, async () => {
    const r = await fetch(`${BACKEND}/ticker/${ticker.toUpperCase()}`);
    if (!r.ok) throw new Error(`Failed to load ${ticker}`);
    const data = await r.json();
    const news = data.news || data.articles || [];
    return { ...data, news, articles: data.articles || news };
  });
}

export async function searchTickers(q, limit = 8) {
  return dedup(`search:${q}:${limit}`, async () => {
    const r = await fetch(`${BACKEND}/search?q=${encodeURIComponent(q)}&limit=${limit}`);
    if (!r.ok) throw new Error('Search failed');
    return r.json();
  });
}

export async function fetchDilutionTracker(ticker) {
  return dedup(`dilution:${ticker.toUpperCase()}`, async () => {
    const r = await fetch(`${BACKEND}/ticker/${ticker.toUpperCase()}/dilution`);
    if (!r.ok) throw new Error(`Failed to load dilution tracker for ${ticker}`);
    return r.json();
  });
}
