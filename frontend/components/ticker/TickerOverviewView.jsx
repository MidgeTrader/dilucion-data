import { useState } from 'react';
import dynamic from 'next/dynamic';
import CompanyAbout from '../CompanyAbout';
import InfoCard from '../InfoCard';
import { fpiRow } from '../../lib/fpi';
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

// Los umbrales se comparan contra el valor absoluto: un EV negativo (empresa
// con mas caja que market cap) caia al final y salia en crudo. Para positivos
// la salida es identica a la de antes.
function fmtM(n) {
  if (n == null) return '—';
  const abs = Math.abs(n);
  const sign = n < 0 ? '-' : '';
  if (abs >= 1e6) return `${sign}${(abs / 1e6).toFixed(2)} M`;
  if (abs >= 1e3) return `${sign}${(abs / 1e3).toFixed(2)} K`;
  return String(n);
}

// Igual que fmtM pero para recuentos de acciones. Sin la unidad, un "1.47 M"
// al lado de un market cap en dólares se lee como dinero.
function fmtAcc(n) {
  const texto = fmtM(n);
  return texto === '—' ? texto : `${texto} /shr`;
}

// Clasificación del float por tamaño, con cortes de small caps: por debajo de
// 10 M el precio se mueve con poco dinero y el riesgo de squeeze es real; por
// encima de 50 M el float deja de ser la historia. Se mide sobre las acciones
// libres (float_shares) y no sobre el capital emitido, que es lo que opera.
const FLOAT_LOW_MAX = 10e6;
const FLOAT_MEDIUM_MAX = 50e6;

function floatTier(shares) {
  // Cero o negativo es un dato roto, no un float diminuto.
  if (shares == null || shares <= 0) return { value: '—' };
  const esLow = shares < FLOAT_LOW_MAX;
  const esMedium = shares < FLOAT_MEDIUM_MAX;
  return {
    value: esLow ? 'Low' : esMedium ? 'Medium' : 'Large',
    highlight: esLow ? 'text-accent-red' : esMedium ? 'text-accent-yellow' : '',
    title: `${shares.toLocaleString('es-ES')} acciones en float · ` +
      'Low < 10 M · Medium 10-50 M · Large > 50 M',
  };
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
      // Jurisdicciones de registro habituales en small caps extranjeras:
      // casi todas las chinas cotizadas en Nasdaq son sociedades de Caiman.
      'KY': '🇰🇾', 'Cayman Islands': '🇰🇾',
      'VG': '🇻🇬', 'British Virgin Islands': '🇻🇬',
      'BM': '🇧🇲', 'Bermuda': '🇧🇲',
      'MH': '🇲🇭', 'Marshall Islands': '🇲🇭',
    };
    const flag = flags[c] || flags[p?.country] || '';
    return flag ? `${flag} ${c}` : c;
  };

  const card1 = p ? [
    { label: 'Sector', value: p.sector },
    { label: 'Industry', value: p.industry },
    { label: 'Country', value: countryFlag(p.country) },
    { label: 'Incorporated', value: countryFlag(p.country_incorporation) },
    { label: 'FPI', ...fpiRow(p.is_fpi) },
    { label: 'Exchange', value: p.exchange },
    { label: 'Vol Avg.', value: fmtM(p.avg_volume) },
    { label: 'Inst Own', value: p.institutional_ownership != null ? `${p.institutional_ownership.toFixed(3)}%` : 'N/A' },
  ] : [];

  const floatOs = p?.float_shares != null && p?.shares_outstanding != null
    ? `${fmtAcc(p.float_shares)} / ${fmtAcc(p.shares_outstanding)}`
    : '—';

  // Capital emitido que NO está en el float: insiders, restringidas y bloqueadas.
  // Es la oferta que puede entrar al mercado de golpe cuando se libere
  // (fin de lock-up o ventana de la Rule 144), así que interesa tenerla a mano.
  const noFloatShares =
    p?.float_shares != null && p?.shares_outstanding != null && p.shares_outstanding >= p.float_shares
      ? p.shares_outstanding - p.float_shares
      : null;

  // Pista de caja: caja disponible / quema. Por debajo de 6 meses la proxima
  // ampliacion es inminente, y para esta estrategia eso no es un riesgo — es el
  // evento que se opera, de ahi el rojo.
  const cashRunway = (prof) => {
    const meses = prof?.months_of_cash;
    if (meses == null) {
      // Ojo: null aqui tiene DOS causas y no significan lo mismo. Si hay fecha
      // de balance, la caja se leyo y el flujo de operaciones es positivo: no
      // hay runway finito que agotar. Si no la hay, EDGAR no devolvio ni caja
      // ni flujo, asi que no consta. Afirmar "flujo positivo" en el segundo
      // caso seria inventarse el dato — que es el error que se venia
      // cometiendo: un "—" por falta de dato se leia como "no quema".
      return prof?.cash_balance_date
        ? {
            label: 'Time to Burn',
            value: '—',
            title: `Flujo de operaciones positivo: no hay quema que agotar (caja al ${prof.cash_balance_date})`,
          }
        : {
            label: 'Time to Burn',
            value: 's/d',
            title: 'Sin dato: EDGAR no devuelve caja ni flujo de operaciones para este emisor',
          };
    }
    const partes = [];
    if (prof?.cash_burn_annual) partes.push(`Quema ${fmtM(Math.abs(prof.cash_burn_annual))}/año`);
    if (prof?.cash_balance_date) partes.push(`Balance al ${prof.cash_balance_date}`);
    return {
      label: 'Time to Burn',
      value: `${meses.toFixed(1)} m`,
      highlight: meses < 6 ? 'text-accent-red' : meses < 12 ? 'text-accent-yellow' : '',
      title: partes.length ? partes.join(' · ') : undefined,
    };
  };

  const card2 = p ? [
    { label: 'Float & OS', value: floatOs },
    { label: 'Float', ...floatTier(p.float_shares) },
    { label: 'No-float (no disponibles)', value: fmtAcc(noFloatShares), title: 'Capital emitido fuera del float: insiders, restringidas y bloqueadas. Puede entrar en el mercado al liberarse (lock-up, Rule 144)' },
    { label: 'Cash/Shr', value: p.cash_per_share != null ? `$${p.cash_per_share.toFixed(2)}` : '—' },
    { label: 'Market Cap & EV', value: `${fmtM(p.market_cap)} / ${fmtM(p.enterprise_value)}` },
    cashRunway(p),
    { label: 'Short Interest', value: p.short_percent_float != null ? `${p.short_percent_float}%` : '—' },
    { label: 'Borrow Rate', value: p.borrow_rate != null ? `${p.borrow_rate.toFixed(2)}%` : '—', highlight: p.borrow_rate > 100 ? 'text-accent-red' : '' },
    { label: 'Days to Cover', value: p.days_to_cover ?? '—' },
  ] : [];

  const [scanning, setScanning] = useState(false);
  const [scanMsg, setScanMsg] = useState(null);

  const handleScan = async () => {
    setScanning(true);
    setScanMsg(null);
    try {
      const backend = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
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
