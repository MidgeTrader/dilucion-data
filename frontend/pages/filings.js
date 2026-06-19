import { useState, useEffect } from 'react';
import Head from 'next/head';
import Layout from '../components/Layout';
import SearchBar from '../components/SearchBar';
import FilingsTable from '../components/FilingsTable';

export default function FilingsPage() {
  const [filings, setFilings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const backend = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    fetch(`${backend}/filings/all?limit=100`)
      .then((r) => { if (!r.ok) throw new Error('Failed to load filings'); return r.json(); })
      .then(setFilings)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <Layout activeNav="filings">
      <Head><title>Filings — SEC Dilution Tracker</title></Head>
      <header className="border-b border-surface-border px-6 py-4 flex items-center gap-4">
        <div className="flex-1 max-w-md"><SearchBar /></div>
        <span className="text-sm text-gray-500">{filings.length} filings tracked</span>
      </header>
      <main className="p-6">
        <FilingsTable filings={filings} loading={loading} error={error} />
      </main>
    </Layout>
  );
}
