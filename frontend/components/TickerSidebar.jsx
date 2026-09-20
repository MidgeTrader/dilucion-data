import Link from 'next/link';
import TickerAvatar from './TickerAvatar';
import { fpiRow } from '../lib/fpi';

const NAV = [
  { id: 'overview', label: 'Overview', segment: '' },
  { id: 'filings', label: 'Filings', segment: '/filings' },
  { id: 'insights', label: 'Insights', segment: '/insights' },
  { id: 'dilution', label: 'Dilution', segment: '/dilution' },
  { id: 'news', label: 'News', segment: '/news' },
  { id: 'transcripts', label: 'Transcripts', segment: '/transcripts' },
];

// Los umbrales se comparan contra el valor absoluto: con `n >= 1e6` un
// negativo no pasaba ningun if y caia al final, pintandose en crudo.
// Para positivos la salida es identica a la de antes.
function fmtNum(n) {
  if (n == null) return '—';
  const abs = Math.abs(n);
  const sign = n < 0 ? '-' : '';
  if (abs >= 1e9) return `${sign}${(abs / 1e9).toFixed(2)} B`;
  if (abs >= 1e6) return `${sign}${(abs / 1e6).toFixed(2)} M`;
  if (abs >= 1e3) return `${sign}${(abs / 1e3).toFixed(2)} K`;
  return n.toLocaleString();
}

export default function TickerSidebar({ profile, activeNav = 'overview', ticker: tickerProp }) {
  const ticker = tickerProp || profile?.ticker || '—';

  const quickStats = [
    { label: 'Price', value: profile?.price != null ? profile.price.toFixed(2) : '—' },
    { label: 'Market Cap', value: fmtNum(profile?.market_cap) },
    { label: 'Float', value: fmtNum(profile?.float_shares) },
    { label: 'Country', value: profile?.country || '—' },
    { label: 'Incorporated', value: profile?.country_incorporation || '—' },
    { label: 'FPI', ...fpiRow(profile?.is_fpi) },
    { label: 'Sector', value: profile?.sector || '—' },
    { label: 'Exchange', value: profile?.exchange || '—' },
  ];

  return (
    <aside className="w-[220px] shrink-0 border-r border-surface-border bg-surface flex flex-col h-full overflow-y-auto">
      <div className="p-4 border-b border-surface-border">
        <Link href="/" className="text-xs text-gray-500 hover:text-white flex items-center gap-1 mb-4">
          ← Back
        </Link>
        <div className="flex items-start gap-3 mb-2">
          <TickerAvatar ticker={ticker} />
          <div className="min-w-0">
            <h2 className="text-sm font-semibold text-white leading-snug">
              {profile?.company_name || 'Loading...'}
            </h2>
            <div className="flex items-center gap-2 text-xs text-gray-500 mt-1">
              <span className="font-mono text-accent-teal font-semibold">{ticker}</span>
              {profile?.website && (
                <a href={`https://${profile.website}`} target="_blank" rel="noopener noreferrer" className="hover:text-white truncate">
                  website
                </a>
              )}
            </div>
          </div>
        </div>
        {profile?.employees != null && (
          <p className="text-xs text-gray-600 ml-[52px]">{profile.employees} employees</p>
        )}
      </div>

      <div className="px-4 py-3 border-b border-surface-border space-y-0">
        {quickStats.map((s) => (
          <div key={s.label} className="flex justify-between py-1.5 text-xs">
            <span className="text-gray-500 shrink-0 mr-2">{s.label}</span>
            <span
              className={`font-medium text-right truncate max-w-[130px] text-[10px] leading-4 ${s.highlight || 'text-gray-200'}`}
              title={s.title || undefined}
            >
              {s.value}
            </span>
          </div>
        ))}
      </div>

      <nav className="flex-1 p-2 space-y-0.5">
        {NAV.map((item) => {
          const active = activeNav === item.id;
          const href = ticker && ticker !== '—'
            ? `/ticker/${ticker}${item.segment}`
            : '#';
          return (
            <Link
              key={item.id}
              href={href}
              className={`nav-link ${active ? 'nav-link-active' : ''}`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-surface-border mt-auto">
        <p className="text-xs text-gray-600 mb-2">Search in Documents</p>
        <input
          type="text"
          placeholder="Any keyword or phrase"
          className="input-search text-xs py-2"
        />
      </div>
    </aside>
  );
}
