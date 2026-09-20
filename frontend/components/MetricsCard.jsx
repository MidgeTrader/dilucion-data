// Los umbrales se comparan contra el valor absoluto: ver TickerSidebar.jsx.
// Para positivos la salida es identica a la de antes.
function formatNumber(num) {
  if (num == null) return '—';
  const abs = Math.abs(num);
  const sign = num < 0 ? '-' : '';
  if (abs >= 1e9) return `${sign}${(abs / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `${sign}${(abs / 1e6).toFixed(2)}M`;
  if (abs >= 1e3) return `${sign}${(abs / 1e3).toFixed(1)}K`;
  return num.toLocaleString();
}

function MetricRow({ label, value, sub }) {
  return (
    <div className="flex justify-between items-start py-2 border-b border-surface-border last:border-0">
      <span className="text-sm text-gray-400">{label}</span>
      <div className="text-right">
        <span className="text-sm font-medium text-white">{value}</span>
        {sub && <p className="text-xs text-gray-500">{sub}</p>}
      </div>
    </div>
  );
}

export default function MetricsCard({ profile, loading, error }) {
  if (loading) {
    return (
      <div className="card animate-pulse space-y-3">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-4 bg-surface-hover rounded" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="card border-accent-red/30">
        <p className="text-accent-red text-sm">{error}</p>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="card">
        <p className="text-gray-500 text-sm">No metrics available.</p>
      </div>
    );
  }

  return (
    <div className="card">
      <h3 className="text-sm font-semibold text-gray-300 mb-3 uppercase tracking-wide">
        Sector Metrics
      </h3>
      <MetricRow label="Sector" value={profile.sector || '—'} />
      <MetricRow label="Country" value={profile.country || '—'} />
      <MetricRow label="Incorporated" value={profile.country_incorporation || '—'} />
      <MetricRow label="Float" value={formatNumber(profile.float_shares)} />
      <MetricRow label="Shares Outstanding" value={formatNumber(profile.shares_outstanding)} />
      <MetricRow
        label="Borrow Rate"
        value={profile.borrow_rate != null ? `${profile.borrow_rate.toFixed(2)}%` : '—'}
        sub={profile.short_percent_float != null ? `Short: ${profile.short_percent_float.toFixed(1)}% float` : null}
      />
    </div>
  );
}
