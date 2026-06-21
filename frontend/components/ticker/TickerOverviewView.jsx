import { useState } from 'react';
import dynamic from 'next/dynamic';
import CompanyAbout from '../CompanyAbout';
import InfoCard from '../InfoCard';
import RiskPanel from '../RiskPanel';
import RecentArticles from '../RecentArticles';
import RecentFilings from '../RecentFilings';
import EarningsPanel from '../EarningsPanel';

const CandlestickChart = dynamic(() => import('../CandlestickChart'), {
  ssr: false,
  loading: () => (
    <div className="card min-h-[360px] flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-accent-teal border-t-transparent rounded-full animate-spin" />
    </div>
  ),
});

function fmtM(n) {
  if (n == null) return '—';
  if (n >= 1e6) return `${(n / 1e6).toFixed(2)} M`;
  if (n >= 1e3) return `${(n / 1e3).toFixed(2)} K`;
  return String(n);
}

export default function TickerOverviewView({ data, loading, tickerUpper }) {
  const p = data?.profile;
  const risk = data?.risk;

  const countryFlag = (c) => {
    const flags = {
      'USA': '🇺🇸', 'us': '🇺🇸', 'United States': '🇺🇸',
      'United States of America': '🇺🇸',
      'SG': '🇸🇬', 'Singapore': '🇸🇬',
      'CA': '🇨🇦', 'Canada': '🇨🇦',
      'GB': '🇬🇧', 'UK': '🇬🇧', 'United Kingdom': '🇬🇧',
      'IL': '🇮🇱', 'Israel': '🇮🇱',
      'CN': '🇨🇳', 'China': '🇨🇳',
      'JP': '🇯🇵', 'Japan': '🇯🇵',
      'HK': '🇭🇰', 'Hong Kong': '🇭🇰',
      'AU': '🇦🇺', 'Australia': '🇦🇺',
      'IE': '🇮🇪', 'Ireland': '🇮🇪',
      'CH': '🇨🇭', 'Switzerland': '🇨🇭',
      'DE': '🇩🇪', 'Germany': '🇩🇪',
      'FR': '🇫🇷', 'France': '🇫🇷',
    };
    const flag = flags[c] || flags[p?.country] || '';
    return flag ? `${flag} ${c}` : c;
  };

  const card1 = p ? [
    { label: 'Sector', value: p.sector },
    { label: 'Industry', value: p.industry },
    { label: 'Country', value: countryFlag(p.country) },
    { label: 'Exchange', value: p.exchange },
    { label: 'Vol Avg.', value: fmtM(p.avg_volume) },
    { label: 'Inst Own', value: p.institutional_ownership != null ? `${p.institutional_ownership.toFixed(3)}%` : 'N/A' },
  ] : [];

  const floatOs = p?.float_shares != null && p?.shares_outstanding != null
    ? `${fmtM(p.float_shares)} / ${fmtM(p.shares_outstanding)}`
    : '—';

  const card2 = p ? [
    { label: 'Float & OS', value: floatOs },
    { label: 'Cash/Shr', value: p.cash_per_share != null ? `$${p.cash_per_share.toFixed(2)}` : '—' },
    { label: 'Market Cap & Ev', value: `${fmtM(p.market_cap)} / ${fmtM(p.enterprise_value)}` },
    { label: 'Short Interest', value: p.short_percent_float != null ? `${p.short_percent_float}%` : '—' },
    { label: 'Borrow Rate', value: p.borrow_rate != null ? `${p.borrow_rate.toFixed(4)}%` : '—', highlight: p.borrow_rate > 100 ? 'text-accent-red' : '' },
    { label: 'Days to Cover', value: p.days_to_cover ?? '—' },
  ] : [];

  const [scanning, setScanning] = useState(false);
  const [scanMsg, setScanMsg] = useState(null);

  const handleScan = async () => {
    setScanning(true);
    setScanMsg(null);
    try {
      const backend = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8001';
      const r = await fetch(`${backend}/scan/${tickerUpper}`, { method: 'POST' });
      if (!r.ok) throw new Error(await r.text());
      setScanMsg({ type: 'success', text: '✅ Scan completado. Recarga la página para ver los datos.' });
    } catch (e) {
      setScanMsg({ type: 'error', text: `❌ Error: ${e.message}` });
    } finally {
      setScanning(false);
    }
  };

  return (
    <div className="space-y-3">
      {/* Botón Scan + mensaje */}
      <div className="flex items-center gap-3">
        <button
          onClick={handleScan}
          disabled={scanning}
          className="px-4 py-2 text-sm font-semibold rounded-lg bg-accent-teal text-black hover:bg-accent-teal/80 disabled:opacity-50 transition-colors"
        >
          {scanning ? '🔍 Escaneando...' : '🔍 Scan SEC Filings'}
        </button>
        {scanMsg && (
          <span className={`text-sm ${scanMsg.type === 'success' ? 'text-green-400' : 'text-red-400'}`}>
            {scanMsg.text}
          </span>
        )}
      </div>
      {/* Fila 1: gráfico 2/3 + Company/About 1/3 (Dilucion Data layout) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
        <div className="lg:col-span-2 min-w-0 flex">
          <div className="flex-1">
            <CandlestickChart data={data?.candles} loading={loading} ticker={tickerUpper} profile={p} />
          </div>
        </div>
        <div className="lg:col-span-1 min-w-0 flex">
          <div className="flex-1">
            <CompanyAbout profile={p} />
          </div>
        </div>
      </div>

      {/* Fila 2: 3 KPI cards iguales */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <InfoCard rows={card1} loading={loading} />
        <InfoCard rows={card2} loading={loading} />
        <RiskPanel risk={risk} loading={loading} />
      </div>

      <div className="card card-inner">
        <div className="flex items-center justify-between border-b border-surface-border pb-3 mb-4">
          <h3 className="text-sm font-semibold text-white">Research Report</h3>
          <button type="button" className="text-xs text-gray-500 hover:text-white">Customize research</button>
        </div>
        <div className="text-sm text-gray-300 leading-relaxed space-y-3">
          {data?.research_summary
            ? data.research_summary.split(/\n(?=\*\*)/).map((section, i) => {
                const headerMatch = section.match(/^\*\*(.+?)\*\*/);
                if (headerMatch) {
                  const header = headerMatch[1];
                  const body = section.replace(/^\*\*.+?\*\*/, '').trim();
                  return (
                    <div key={i}>
                      <h4 className="text-sm font-semibold text-accent-teal mb-1">{header}</h4>
                      <p className="text-sm text-gray-300">{body}</p>
                    </div>
                  );
                }
                return <p key={i} className="text-sm text-gray-300">{section.trim()}</p>;
              })
            : 'AI-generated dilution research will appear here after scanning SEC filings and running RAG analysis.'}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <RecentArticles articles={data?.articles} loading={loading} />
        <RecentFilings filings={data?.filings} ticker={tickerUpper} loading={loading} />
      </div>

      <EarningsPanel earnings={data?.earnings} loading={loading} />
    </div>
  );
}
