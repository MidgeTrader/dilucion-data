import { useState, useCallback, useEffect } from 'react';
import { useRouter } from 'next/router';
import { searchTickers } from '../lib/mockData';
import { setLastTicker } from '../lib/lastTicker';

export default function SearchBar({ onSelect, placeholder = 'Search ticker or company...' }) {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [open, setOpen] = useState(false);

  const search = useCallback(async (q) => {
    if (!q || q.length < 1) {
      setResults([]);
      setOpen(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await searchTickers(q, 8);
      setResults(data);
      setOpen(true);
    } catch (err) {
      setError(err.message);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => search(query), 300);
    return () => clearTimeout(timer);
  }, [query, search]);

  const handleChange = (e) => {
    setQuery(e.target.value);
  };

  const handleSelect = (item) => {
    setQuery(item.ticker);
    setOpen(false);
    setLastTicker(item.ticker);
    if (onSelect) onSelect(item);
    router.push(`/ticker/${item.ticker}`);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      const t = query.trim().toUpperCase();
      setLastTicker(t);
      router.push(`/ticker/${t}`);
      setOpen(false);
    }
  };

  return (
    <div className="relative w-full">
      <form onSubmit={handleSubmit}>
        <div className="relative">
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            value={query}
            onChange={handleChange}
            onFocus={() => results.length > 0 && setOpen(true)}
            placeholder={placeholder}
            className="input-dark pl-10"
          />
          {loading && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2">
              <div className="w-4 h-4 border-2 border-accent border-t-transparent rounded-full animate-spin" />
            </div>
          )}
        </div>
      </form>

      {error && (
        <p className="text-accent-red text-xs mt-1">{error}</p>
      )}

      {open && results.length > 0 && (
        <ul className="absolute z-50 w-full mt-1 bg-surface-card border border-surface-border rounded-lg shadow-xl overflow-hidden">
          {results.map((item) => (
            <li key={item.ticker}>
              <button
                type="button"
                onClick={() => handleSelect(item)}
                className="w-full text-left px-4 py-2.5 hover:bg-surface-hover transition-colors flex justify-between items-center"
              >
                <span className="font-mono font-semibold text-accent">{item.ticker}</span>
                <span className="text-gray-400 text-sm truncate ml-2">{item.company_name}</span>
              </button>
            </li>
          ))}
        </ul>
      )}

      {open && !loading && query.length >= 1 && results.length === 0 && !error && (
        <div className="absolute z-50 w-full mt-1 bg-surface-card border border-surface-border rounded-lg p-3 text-sm text-gray-500">
          No results. Press Enter to search &quot;{query.toUpperCase()}&quot; directly.
        </div>
      )}
    </div>
  );
}
