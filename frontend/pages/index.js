import { useState, useEffect } from 'react';
import Head from 'next/head';
import TopNav from '../components/TopNav';
import DilutionHeatmap from '../components/DilutionHeatmap';
import DilutionAlertsFeed from '../components/DilutionAlertsFeed';
import { fetchTopDilution, fetchAlertsFeed } from '../lib/mockData';

export default function Home() {
  const [topDilution, setTopDilution] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([fetchTopDilution(15), fetchAlertsFeed(10)])
      .then(([top, feed]) => { setTopDilution(top); setAlerts(feed); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      <Head>
        <title>SEC Dilution Tracker + RAG</title>
      </Head>
      <div className="flex flex-col min-h-screen">
        <TopNav />
        <main className="flex-1 p-6 space-y-6 max-w-6xl mx-auto w-full">
          <div>
            <h2 className="text-2xl font-bold text-white">Overview</h2>
            <p className="text-gray-500 text-sm mt-1">Automatic SEC dilution detection + DeepSeek RAG analysis.</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {[
              { label: 'Filings Indexed', value: topDilution.length },
              { label: 'High Risk (≥20%)', value: topDilution.filter((d) => (d.dilution_percentage || 0) >= 20).length },
              { label: 'Warrants Found', value: topDilution.filter((d) => d.warrants_found).length },
            ].map((s) => (
              <div key={s.label} className="card card-inner">
                <p className="text-xs text-gray-500 uppercase tracking-wide">{s.label}</p>
                <p className="text-3xl font-bold text-white mt-1">{loading ? '—' : s.value}</p>
              </div>
            ))}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <DilutionHeatmap data={topDilution} loading={loading} error={error} />
            <DilutionAlertsFeed alerts={alerts} loading={loading} error={error} />
          </div>
        </main>
      </div>
    </>
  );
}
