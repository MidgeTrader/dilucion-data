function formatDate(d) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

function formatUSD(n) {
  if (n == null) return null;
  if (n >= 1e9) return `$${(n / 1e9).toFixed(1)}B`;
  if (n >= 1e6) return `$${(n / 1e6).toFixed(1)}M`;
  return `$${n.toLocaleString()}`;
}

const DILUTION_COLORS = {
  HIGH: 'text-accent-red bg-accent-red/10',
  MEDIUM: 'text-accent-yellow bg-accent-yellow/10',
  LOW: 'text-accent-green bg-accent-green/10',
};

export default function FilingsTable({ filings, loading, error, ticker }) {
  if (loading) {
    return (
      <div className="space-y-2">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-14 bg-surface-hover rounded-card animate-pulse" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <p className="text-accent-red text-sm">{error}</p>
      </div>
    );
  }

  if (!filings || filings.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 text-sm">No SEC filings indexed for {ticker || 'this ticker'}.</p>
      </div>
    );
  }

  return (
    <div className="space-y-1.5">
      {filings.map((f) => {
        const hasDil = f.dilution_percentage != null && f.dilution_percentage > 0;
        const dilColor = f.dilution_percentage >= 20 ? 'HIGH' : f.dilution_percentage >= 10 ? 'MEDIUM' : 'LOW';
        const hasFlags = f.warrants_found || f.has_atm || f.has_full_ratchet || f.has_prefunded_warrants;
        return (
          <div
            key={f.accession_number}
            className="flex items-start gap-3 px-4 py-3 rounded-card hover:bg-surface-hover/50 transition-colors"
          >
            {/* Left: Form type badge + date */}
            <div className="flex flex-col items-center min-w-[60px] shrink-0">
              {f.source_url ? (
                <a
                  href={f.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-mono text-xs font-semibold text-accent-teal bg-accent-teal/10 px-2.5 py-1 rounded hover:bg-accent-teal/20 transition-colors"
                >
                  {f.form_type}
                </a>
              ) : (
                <span className="font-mono text-xs font-semibold text-accent-teal bg-accent-teal/10 px-2.5 py-1 rounded">
                  {f.form_type}
                </span>
              )}
              <span className="text-[11px] text-gray-600 mt-1 whitespace-nowrap">{formatDate(f.filed_date)}</span>
            </div>

            {/* Middle: Headline + flags + summary */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                {f.summary ? (
                  <span className="text-sm text-gray-200">{f.summary.slice(0, 120)}</span>
                ) : (
                  <span className="text-sm text-gray-500 italic">{f.form_type} filing</span>
                )}
              </div>
              {/* Flags row */}
              <div className="flex items-center gap-1.5 mt-1 flex-wrap">
                {f.shelf_amount_usd != null && f.shelf_amount_usd > 0 && (
                  <span className="text-[11px] text-gray-500 bg-surface-muted px-1.5 py-0.5 rounded">
                    {formatUSD(f.shelf_amount_usd)}
                  </span>
                )}
                {hasDil && (
                  <span className={`text-[11px] px-1.5 py-0.5 rounded ${DILUTION_COLORS[dilColor]}`}>
                    {f.dilution_percentage.toFixed(1)}% dil
                  </span>
                )}
                {f.warrants_found && <span className="text-[11px] px-1.5 py-0.5 rounded bg-accent-yellow/15 text-accent-yellow">Warrants</span>}
                {f.has_atm && <span className="text-[11px] px-1.5 py-0.5 rounded bg-blue-500/15 text-blue-400">ATM</span>}
                {f.has_full_ratchet && <span className="text-[11px] px-1.5 py-0.5 rounded bg-accent-red/15 text-accent-red">Full Ratchet</span>}
                {f.has_prefunded_warrants && <span className="text-[11px] px-1.5 py-0.5 rounded bg-purple-500/15 text-purple-400">Pre-Funded</span>}
                {!hasFlags && !f.shelf_amount_usd && !hasDil && (
                  <span className="text-[11px] text-gray-600">No dilution signals</span>
                )}
              </div>
            </div>

            {/* Right: View link */}
            {f.source_url && (
              <a
                href={f.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="shrink-0 text-xs text-gray-600 hover:text-white self-center px-2 py-1 rounded transition-colors"
                title="Open SEC filing"
              >
                ↗
              </a>
            )}
          </div>
        );
      })}
    </div>
  );
}
