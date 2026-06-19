import { useState, useEffect } from 'react';
import Head from 'next/head';
import Layout from '../components/Layout';
import SearchBar from '../components/SearchBar';
import DilutionAlertsFeed from '../components/DilutionAlertsFeed';

export default function MonitorPage() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const backend = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    fetch(`${backend}/alerts/feed?limit=30`)
      .then((r) => { if (!r.ok) throw new Error('Failed to load alerts'); return r.json(); })
      .then(setAlerts)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <Layout activeNav="monitor">
      <Head><title>Monitor — SEC Dilution Tracker</title></Head>
      <header className="border-b border-surface-border px-6 py-4">
        <div className="max-w-md"><SearchBar /></div>
      </header>
      <main className="p-6 space-y-6 max-w-4xl">
        <div>
          <h2 className="text-2xl font-bold text-white">Real-time Monitor</h2>
          <p className="text-gray-400 text-sm mt-1">
            Dilution alerts from RSS scanner and pipeline. Start backend monitor:{' '}
            <code className="font-mono text-xs">python main.py monitor --once</code>
          </p>
        </div>
        <DilutionAlertsFeed alerts={alerts} loading={loading} error={error} />
        <div className="card font-mono text-xs text-gray-400 space-y-1">
          <p><span className="text-accent">$</span> python main.py monitor --daily</p>
          <p><span className="text-accent">$</span> python main.py monitor --once</p>
          <p><span className="text-accent">$</span> python main.py monitor  <span className="text-gray-600"># daemon</span></p>
        </div>
      </main>
    </Layout>
  );
}
