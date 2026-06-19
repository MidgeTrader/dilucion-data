const KEY = 'askedgar:lastTicker';
const DEFAULT = 'SPHL';

export function getLastTicker() {
  if (typeof window === 'undefined') return DEFAULT;
  return localStorage.getItem(KEY) || DEFAULT;
}

export function setLastTicker(ticker) {
  if (typeof window === 'undefined' || !ticker) return;
  localStorage.setItem(KEY, ticker.toUpperCase());
}

export function lastTickerHref() {
  return `/ticker/${getLastTicker()}`;
}
