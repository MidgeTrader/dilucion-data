import { useState, useEffect } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import Layout from '../../components/Layout';
import SearchBar from '../../components/SearchBar';
import TickerHeader from '../../components/TickerHeader';
import MetricsGrid from '../../components/MetricsGrid';
import CandlestickChart from '../../components/CandlestickChart';
import RiskIndicator from '../../components/RiskIndicator';
import FilingsTable from '../../components/FilingsTable';
import RagChatModal from '../../components/RagChatModal';

export default function TickerPage() {
  const router = useRouter();
  const { ticker } = router.query;
  const tickerUpper = ticker?.toUpperCase();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [chatOpen, setChatOpen] = useState(false);

  useEffect(() => {
    if (!tickerUpper) return;
    setLoading(true);
    setError(null);
    const backend = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    fetch(`${backend}/ticker/${tickerUpper}`)
      .then((r) => { if (!r.ok) throw new Error(`Failed to load ${tickerUpper}`); return r.json(); })
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [tickerUpper]);

  const profile = data?.profile;
  const risk = data?.risk;
  const filingUrl = data?.filings?.[0]?.source_url;

  return (
    <Layout activeNav="overview">
      <Head><title>{tickerUpper || 'Ticker'} — SEC Dilution Tracker</title></Head>

      <div className="flex flex-1 min-h-0">
        <div className="flex-1 flex flex-col min-w-0">
          <header className="border-b border-surface-border px-6 py-3">
            <SearchBar />
          </header>
          <main className="flex-1 p-6 space-y-5 overflow-auto">
            {error ? (
              <div className="card border-accent-red/30">
                <p className="text-accent-red">{error}</p>
                <p className="text-gray-500 text-sm mt-2">Run: <code className="font-mono">python main.py serve</code></p>
              </div>
            ) : (
              <>
                <TickerHeader
                  ticker={tickerUpper}
                  profile={profile}
                  loading={loading}
                  onAsk={() => setChatOpen(true)}
                />
                <CandlestickChart data={data?.candles} loading={loading} error={null} ticker={tickerUpper} />
                <FilingsTable filings={data?.filings} loading={loading} error={null} />
              </>
            )}
          </main>
        </div>

        <aside className="w-72 shrink-0 border-l border-surface-border p-5 space-y-5 overflow-auto hidden lg:block">
          <MetricsGrid profile={profile} loading={loading} error={error} />
          <div className="card space-y-4">
            <h3 className="text-sm font-semibold text-gray-300 uppercase">Risk Indicators</h3>
            {loading ? (
              <div className="animate-pulse space-y-3">{[...Array(4)].map((_, i) => <div key={i} className="h-8 bg-surface-hover rounded" />)}</div>
            ) : risk ? (
              <>
                <RiskIndicator label="Offering Ability" level={risk.offering_ability} />
                <RiskIndicator label="Dilution" level={risk.dilution} />
                <RiskIndicator label="Cash Need" level={risk.cash_need} />
                <RiskIndicator label="Warrant Exercise Risk" level={risk.warrant_exercise} />
              </>
            ) : (
              <p className="text-gray-500 text-sm">Scan ticker to populate risk data.</p>
            )}
          </div>
        </aside>
      </div>

      <RagChatModal ticker={tickerUpper} isOpen={chatOpen} onClose={() => setChatOpen(false)} filingUrl={filingUrl} />
    </Layout>
  );
}
