import { useState, useEffect } from 'react';
import Head from 'next/head';
import Layout from '../components/Layout';
import SearchBar from '../components/SearchBar';

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

function fmtUSD(n) {
  if (n == null) return '—';
  if (n >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
  if (n >= 1e6) return `$${(n / 1e6).toFixed(2)}M`;
  if (n >= 1e3) return `$${(n / 1e3).toFixed(2)}K`;
  return `$${n.toLocaleString()}`;
}

function fmtNum(n) {
  if (n == null) return '—';
  if (n >= 1e9) return `${(n / 1e9).toFixed(2)}B`;
  if (n >= 1e6) return `${(n / 1e6).toFixed(1)}M`;
  if (n >= 1e3) return `${(n / 1e3).toFixed(0)}K`;
  return n.toLocaleString();
}

export default function ScreenerPage() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [minGap, setMinGap] = useState(25);

  const fetchData = (gap) => {
    setLoading(true);
    setError(null);
    fetch(`${BACKEND}/screener/gap?min_gap=${gap}&min_price=0.30&limit=30`)
      .then(r => r.ok ? r.json() : Promise.reject('Error'))
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(minGap); }, []);

  return (
    <Layout activeNav="screener">
      <Head><title>Screener — Dilucion Data</title></Head>
      <header className="border-b border-surface-border px-6 py-4">
        <div className="max-w-md"><SearchBar /></div>
      </header>
      <main className="p-6 space-y-6 max-w-6xl">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white">Gap Screener</h2>
            <p className="text-gray-400 text-sm mt-1">
              Penny stocks con gap superior al {minGap}% y precio &gt; $0.30 — Yahoo Finance
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">Min Gap:</span>
            {[15, 25, 50, 100].map(g => (
              <button key={g} onClick={() => { setMinGap(g); fetchData(g); }}
                className={`text-xs px-3 py-1.5 rounded-md border transition-colors ${minGap === g ? 'bg-accent-teal text-black font-semibold border-accent-teal' : 'border-surface-border text-gray-400 hover:text-white'}`}>
                &gt;{g}%
              </button>
            ))}
            <button onClick={() => fetchData(minGap)}
              className="text-xs px-3 py-1.5 rounded-md bg-surface-hover text-gray-300 hover:text-white ml-2">
              ↻ Refresh
            </button>
          </div>
        </div>

        {loading && (
          <div className="space-y-2 animate-pulse">
            {[1,2,3,4,5].map(i => <div key={i} className="h-12 bg-surface-hover rounded" />)}
          </div>
        )}

        {error && (
          <div className="card p-4 text-accent-red text-sm">{error}</div>
        )}

        {!loading && !error && data.length === 0 && (
          <div className="card p-8 text-center">
            <p className="text-gray-500">No se encontraron gaps superiores al {minGap}% hoy.</p>
            <p className="text-xs text-gray-600 mt-2">Prueba con un gap menor o revisa en horario de mercado.</p>
          </div>
        )}

        {!loading && data.length > 0 && (
          <div className="card overflow-hidden p-0">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-500 text-xs border-b border-surface-border">
                  <th className="text-left px-4 py-3 font-medium">Symbol</th>
                  <th className="text-left px-4 py-3 font-medium">Name</th>
                  <th className="text-right px-4 py-3 font-medium">Price</th>
                  <th className="text-right px-4 py-3 font-medium">Gap %</th>
                  <th className="text-right px-4 py-3 font-medium">Volume</th>
                </tr>
              </thead>
              <tbody>
                {data.map((row, i) => (
                  <tr key={row.symbol} className="border-b border-surface-border/30 hover:bg-surface-hover/50">
                    <td className="px-4 py-3">
                      <a href={`/ticker/${row.symbol}`} className="font-mono text-sm font-semibold text-accent-teal hover:text-white">
                        {row.symbol}
                      </a>
                    </td>
                    <td className="px-4 py-3 text-gray-300 text-xs">{row.name}</td>
                    <td className="px-4 py-3 text-right font-mono text-white">${row.price.toFixed(2)}</td>
                    <td className={`px-4 py-3 text-right font-mono font-semibold ${row.gap_pct >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                      {row.gap_pct > 0 ? '+' : ''}{row.gap_pct.toFixed(1)}%
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-gray-400">{fmtNum(row.volume)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </Layout>
  );
}
