/** API client — fetches real data from backend. No mock data. */

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export async function fetchTopDilution(limit = 15) {
  const r = await fetch(`${BACKEND}/dilution/top?limit=${limit}`);
  if (!r.ok) throw new Error('Failed to load dilution data');
  return r.json();
}

export async function fetchAlertsFeed(limit = 10) {
  const r = await fetch(`${BACKEND}/alerts/feed?limit=${limit}`);
  if (!r.ok) throw new Error('Failed to load alerts');
  return r.json();
}

export async function fetchAllFilings(limit = 100) {
  const r = await fetch(`${BACKEND}/filings/all?limit=${limit}`);
  if (!r.ok) throw new Error('Failed to load filings');
  return r.json();
}

export async function fetchTickerNews(ticker, limit = 20) {
  const r = await fetch(`${BACKEND}/ticker/${ticker.toUpperCase()}/news?limit=${limit}`);
  if (!r.ok) throw new Error(`Failed to load news for ${ticker}`);
  return r.json();
}

export async function fetchTicker(ticker) {
  const r = await fetch(`${BACKEND}/ticker/${ticker.toUpperCase()}`);
  if (!r.ok) throw new Error(`Failed to load ${ticker}`);
  const data = await r.json();
  const news = data.news || data.articles || [];
  return { ...data, news, articles: data.articles || news };
}

export async function searchTickers(q, limit = 8) {
  const r = await fetch(`${BACKEND}/search?q=${encodeURIComponent(q)}&limit=${limit}`);
  if (!r.ok) throw new Error('Search failed');
  return r.json();
}

export async function fetchDilutionTracker(ticker) {
  const r = await fetch(`${BACKEND}/ticker/${ticker.toUpperCase()}/dilution`);
  if (!r.ok) throw new Error(`Failed to load dilution tracker for ${ticker}`);
  return r.json();
}
