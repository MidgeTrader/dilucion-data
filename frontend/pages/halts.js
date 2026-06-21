import { useState, useEffect } from 'react';
import Head from 'next/head';

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export default function HaltsPage() {
  const [halts, setHalts] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchHalts = () => {
    setLoading(true);
    fetch(`${BACKEND}/screener/halts`)
      .then(r => r.ok ? r.json() : [])
      .then(setHalts)
      .catch(() => setHalts([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchHalts(); }, []);

  return (
    <>
      <Head><title>Halts — Dilucion Data</title></Head>
      <div className="flex items-center justify-between px-6 py-3 border-b border-surface-border bg-surface">
        <div className="flex items-center gap-4">
          <h1 className="text-lg font-bold text-white">Halts</h1>
          <span className="text-xs text-accent-green">Closed</span>
        </div>
        <div className="text-xs text-gray-500">
          {new Date().toLocaleTimeString('en-US', { hour12: false })} - Local time
          <button onClick={fetchHalts} className="ml-3 text-xs px-2.5 py-1 rounded-md bg-accent-teal text-black font-semibold hover:bg-accent-teal/80">↻</button>
        </div>
      </div>
      <main className="p-4 space-y-4 max-w-full">
        {loading ? (
          <div className="space-y-1 animate-pulse">{[1,2,3,4,5].map(i => <div key={i} className="h-8 bg-surface-hover rounded" />)}</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs whitespace-nowrap">
              <thead><tr className="text-gray-500 border-b border-surface-border">
                <th className="text-left px-3 py-2.5 font-medium">Ticker</th>
                <th className="text-left px-3 py-2.5 font-medium">Status</th>
                <th className="text-left px-3 py-2.5 font-medium">Reason</th>
                <th className="text-left px-3 py-2.5 font-medium">Date</th>
                <th className="text-left px-3 py-2.5 font-medium">Halt</th>
                <th className="text-left px-3 py-2.5 font-medium">Resume</th>
                <th className="text-left px-3 py-2.5 font-medium">Duration</th>
                <th className="text-left px-3 py-2.5 font-medium">Market</th>
              </tr></thead>
              <tbody>
                {halts.length === 0 ? (
                  <tr><td colSpan={8} className="text-center py-8 text-gray-600">No active halts</td></tr>
                ) : halts.map(h => (
                  <tr key={h.symbol} className="border-b border-surface-border/20 hover:bg-surface-hover/50">
                    <td className="px-3 py-2.5 text-accent-yellow font-mono font-semibold">{h.symbol}</td>
                    <td className="px-3 py-2.5"><span className="text-[10px] px-2 py-0.5 rounded bg-accent-red/20 text-accent-red font-semibold">{h.status}</span></td>
                    <td className="px-3 py-2.5 font-mono text-gray-300">{h.reason}</td>
                    <td className="px-3 py-2.5 text-gray-400">{h.date}</td>
                    <td className="px-3 py-2.5 font-mono text-gray-300">{h.halt_time}</td>
                    <td className="px-3 py-2.5 text-gray-500">{h.resume_time || '—'}</td>
                    <td className="px-3 py-2.5 text-gray-500">{h.duration || '—'}</td>
                    <td className="px-3 py-2.5 text-gray-400">{h.market}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </>
  );
}
