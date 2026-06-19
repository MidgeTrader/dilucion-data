import { useState, useEffect } from 'react';
import Head from 'next/head';
import Layout from '../components/Layout';
import SearchBar from '../components/SearchBar';
import DilutionAlertsFeed from '../components/DilutionAlertsFeed';
import { fetchAlertsFeed } from '../lib/mockData';

export default function MonitorPage() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAlertsFeed(30)
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
          <p className="text-gray-400 text-sm mt-1">Feed de alertas de dilución detectadas.</p>
        </div>
        <DilutionAlertsFeed alerts={alerts} loading={loading} error={error} />
      </main>
    </Layout>
  );
}
