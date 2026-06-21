import { useState, useEffect } from 'react';
import Head from 'next/head';
import Layout from '../components/Layout';

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

function fmtNum(n) {
  if (n == null) return '—';
  if (n >= 1e9) return `${(n / 1e9).toFixed(2)}B`;
  if (n >= 1e6) return `${(n / 1e6).toFixed(1)}M`;
  if (n >= 1e3) return `${(n / 1e3).toFixed(0)}K`;
  return n.toLocaleString();
}

function Clock() {
  const [time, setTime] = useState('');
  useEffect(() => {
    const t = setInterval(() => {
      setTime(new Date().toLocaleTimeString('en-US', { hour12: false }));
    }, 1000);
    return () => clearInterval(t);
  }, []);
  return <span>{time}</span>;
}

const TABS = ['gainers', 'losers', 'premarket', 'aftermarket'];

export default function ScreenerPage() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sortType, setSortType] = useState('gainers');
  const [minGap, setMinGap] = useState(25);

  const fetchData = (type, gap) => {
    setLoading(true);
    const url = `${BACKEND}/screener/gap?sort_type=${type}&min_gap=${gap}&min_price=0.30&limit=30`;
    fetch(url).then(r => r.ok ? r.json() : []).then(setData).catch(() => setData([])).finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(sortType, minGap); }, []);

  const switchTab = (tab) => {
    setSortType(tab);
    const gap = tab === 'losers' ? 10 : tab === 'premarket' || tab === 'aftermarket' ? 0 : minGap;
    setMinGap(tab === 'premarket' || tab === 'aftermarket' ? 0 : minGap);
    fetchData(tab, gap);
  };

  return (
    <Layout activeNav="screener">
      <Head><title>Screener — Dilucion Data</title></Head>
      <div className="flex items-center justify-between px-6 py-3 border-b border-surface-border bg-surface">
        <div className="flex items-center gap-4">
          <h1 className="text-lg font-bold text-white">My Dashboard</h1>
          <span className="text-xs text-gray-500">Scanner</span>
          <span className="text-xs text-gray-500">Halts</span>
          <span className="text-xs text-accent-yellow">Alerts</span>
          <span className="text-xs text-accent-green">Closed</span>
        </div>
        <div className="text-xs text-gray-500"><Clock /> - Local time</div>
      </div>
      <main className="p-4 space-y-4 max-w-full">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-1">
            {TABS.map(tab => (
              <button key={tab} onClick={() => switchTab(tab)}
                className={`text-xs px-3 py-1.5 rounded-md border transition-colors ${sortType === tab ? 'bg-accent-teal text-black font-semibold border-accent-teal' : 'border-surface-border text-gray-400 hover:text-white hover:border-gray-600'}`}>
                {tab === 'gainers' ? 'Top gainers' : tab === 'losers' ? 'Top losers' : tab === 'premarket' ? 'Premarket' : 'Aftermarket'}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-600">Watchlist</span>
            <button onClick={() => fetchData(sortType, minGap)} className="text-xs px-3 py-1.5 rounded-md bg-accent-teal text-black font-semibold hover:bg-accent-teal/80">↻ Refresh</button>
          </div>
        </div>
        {sortType !== 'premarket' && sortType !== 'aftermarket' && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">{sortType === 'losers' ? 'Max loss:' : 'Gap:'}</span>
            {[10, 25, 50, 100].map(g => (
              <button key={g} onClick={() => { setMinGap(g); fetchData(sortType, g); }}
                className={`text-xs px-2.5 py-1 rounded-md border transition-colors ${minGap === g ? 'bg-accent-teal/20 border-accent-teal text-accent-teal' : 'border-surface-border text-gray-500 hover:text-white'}`}>
                &gt;{g}%
              </button>
            ))}
          </div>
        )}
        {loading ? (
          <div className="space-y-1 animate-pulse">{[1,2,3,4,5].map(i => <div key={i} className="h-8 bg-surface-hover rounded" />)}</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs whitespace-nowrap">
              <thead><tr className="text-gray-500 border-b border-surface-border">
                <th className="text-left px-2 py-2 font-medium">Ticker</th>
                <th className="text-right px-2 py-2 font-medium">Price</th>
                <th className="text-right px-2 py-2 font-medium">Change %</th>
                <th className="text-right px-2 py-2 font-medium">Gap</th>
                <th className="text-right px-2 py-2 font-medium">Prev Close</th>
                <th className="text-right px-2 py-2 font-medium">Open</th>
                <th className="text-right px-2 py-2 font-medium">High</th>
                <th className="text-right px-2 py-2 font-medium">Low</th>
                <th className="text-right px-2 py-2 font-medium">Volume</th>
                <th className="text-right px-2 py-2 font-medium">R vol</th>
              </tr></thead>
              <tbody>
                {data.length === 0 ? (
                  <tr><td colSpan={10} className="text-center py-8 text-gray-600 text-sm">Sin datos</td></tr>
                ) : data.map((row, i) => (
                  <tr key={row.symbol} className={`border-b border-surface-border/20 hover:bg-surface-hover/50 ${i % 2 === 0 ? 'bg-surface-muted/20' : ''}`}>
                    <td className="px-2 py-2.5">
                      <a href={`/ticker/${row.symbol}`} className="font-mono text-sm font-semibold text-accent-teal hover:text-white">
                        {row.symbol} <span className="text-[10px] text-accent-green">▴</span>
                      </a>
                    </td>
                    <td className="px-2 py-2.5 text-right font-mono text-white">{row.price.toFixed(2)}</td>
                    <td className={`px-2 py-2.5 text-right font-mono font-semibold ${row.change >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                      {row.change >= 0 ? '+' : ''}{row.change_pct.toFixed(2)}%
                    </td>
                    <td className={`px-2 py-2.5 text-right font-mono ${row.gap_pct >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                      {row.gap_pct >= 0 ? '+' : ''}{row.gap_pct.toFixed(2)}%
                    </td>
                    <td className="px-2 py-2.5 text-right font-mono text-gray-400">{row.prev_close.toFixed(2)}</td>
                    <td className="px-2 py-2.5 text-right font-mono text-gray-300">{row.open.toFixed(2)}</td>
                    <td className="px-2 py-2.5 text-right font-mono text-accent-green">{row.high.toFixed(2)}</td>
                    <td className="px-2 py-2.5 text-right font-mono text-accent-red">{row.low.toFixed(2)}</td>
                    <td className="px-2 py-2.5 text-right font-mono text-gray-300">{fmtNum(row.volume)}</td>
                    <td className="px-2 py-2.5 text-right font-mono text-gray-400">
                      {row.avg_volume > 0 ? (row.volume / row.avg_volume).toFixed(2) : '—'}
                    </td>
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
