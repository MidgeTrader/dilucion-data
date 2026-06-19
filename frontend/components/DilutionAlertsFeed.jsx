function riskBadge(level) {
  const map = {
    Low: 'bg-accent-green/20 text-accent-green',
    Med: 'bg-accent-yellow/20 text-accent-yellow',
    High: 'bg-accent-red/20 text-accent-red',
  };
  return map[level] || 'bg-gray-700 text-gray-400';
}

function formatDate(d) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

export default function DilutionAlertsFeed({ alerts, loading, error }) {
  if (loading) {
    return (
      <div className="card animate-pulse space-y-3">
        {[...Array(5)].map((_, i) => <div key={i} className="h-12 bg-surface-hover rounded" />)}
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

  if (!alerts?.length) {
    return (
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-300 mb-2 uppercase tracking-wide">Alerts Feed</h3>
        <p className="text-gray-500 text-sm">No dilution alerts yet. Run <code className="font-mono text-xs">python main.py scan TICKER</code></p>
      </div>
    );
  }

  return (
    <div className="card p-0 overflow-hidden">
      <div className="px-4 py-3 border-b border-surface-border">
        <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">
          Dilution Alerts Feed
        </h3>
      </div>
      <ul className="divide-y divide-surface-border/50 max-h-96 overflow-y-auto">
        {alerts.map((a) => (
          <li key={a.accession_number} className="px-4 py-3 hover:bg-surface-hover transition-colors">
            <div className="flex justify-between items-start gap-2">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-white">{a.ticker || a.cik}</span>
                  <span className="text-xs font-mono text-accent">{a.form_type}</span>
                  {a.has_atm && <span className="text-xs px-1.5 py-0.5 rounded bg-accent-yellow/20 text-accent-yellow">ATM</span>}
                  {a.has_full_ratchet && <span className="text-xs px-1.5 py-0.5 rounded bg-accent-red/20 text-accent-red">FR</span>}
                </div>
                <p className="text-xs text-gray-500 mt-1">{formatDate(a.filed_date)}</p>
              </div>
              <div className="text-right shrink-0">
                {a.dilution_percentage != null && (
                  <p className="text-sm font-semibold text-white">{a.dilution_percentage.toFixed(1)}%</p>
                )}
                {a.risk_level && (
                  <span className={`text-xs px-2 py-0.5 rounded ${riskBadge(a.risk_level)}`}>{a.risk_level}</span>
                )}
              </div>
            </div>
            {a.source_url && (
              <a href={a.source_url} target="_blank" rel="noopener noreferrer" className="text-xs text-accent hover:underline mt-1 inline-block">
                View filing →
              </a>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
