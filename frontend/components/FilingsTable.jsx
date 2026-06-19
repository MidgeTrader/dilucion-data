function formatDate(d) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

function formatUSD(n) {
  if (n == null) return '—';
  if (n >= 1e9) return `$${(n / 1e9).toFixed(1)}B`;
  if (n >= 1e6) return `$${(n / 1e6).toFixed(1)}M`;
  return `$${n.toLocaleString()}`;
}

export default function FilingsTable({ filings, loading, error }) {
  if (loading) {
    return (
      <div className="card">
        <div className="animate-pulse space-y-3">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-10 bg-surface-hover rounded" />
          ))}
        </div>
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
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-300 mb-2 uppercase tracking-wide">SEC Filings</h3>
        <p className="text-gray-500 text-sm">
          No filings indexed yet. Run a scan via CLI:{' '}
          <code className="text-accent font-mono text-xs">python main.py scan &lt;URL&gt;</code>
        </p>
      </div>
    );
  }

  return (
    <div className="card overflow-hidden p-0">
      <div className="px-4 py-3 border-b border-surface-border">
        <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">
          SEC Filings ({filings.length})
        </h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-500 text-xs uppercase border-b border-surface-border">
              <th className="text-left px-4 py-2.5 font-medium">Form</th>
              <th className="text-left px-4 py-2.5 font-medium">Filed</th>
              <th className="text-left px-4 py-2.5 font-medium">Shelf $</th>
              <th className="text-left px-4 py-2.5 font-medium">Dilution</th>
              <th className="text-left px-4 py-2.5 font-medium">Flags</th>
              <th className="text-left px-4 py-2.5 font-medium">AI Summary</th>
            </tr>
          </thead>
          <tbody>
            {filings.map((f) => (
              <tr key={f.accession_number} className="border-b border-surface-border/50 hover:bg-surface-hover transition-colors">
                <td className="px-4 py-3">
                  <span className="font-mono text-accent text-xs">{f.form_type}</span>
                </td>
                <td className="px-4 py-3 text-gray-400">{formatDate(f.filed_date)}</td>
                <td className="px-4 py-3 text-gray-300">{formatUSD(f.shelf_amount_usd)}</td>
                <td className="px-4 py-3">
                  {f.dilution_percentage != null ? (
                    <span className={`font-semibold ${
                      f.dilution_percentage >= 30 ? 'text-accent-red' :
                      f.dilution_percentage >= 10 ? 'text-accent-yellow' : 'text-accent-green'
                    }`}>
                      {f.dilution_percentage.toFixed(1)}%
                    </span>
                  ) : '—'}
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-1 flex-wrap">
                    {f.warrants_found && <span className="text-xs px-1.5 py-0.5 rounded bg-accent-yellow/20 text-accent-yellow">W</span>}
                    {f.has_atm && <span className="text-xs px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400">ATM</span>}
                    {f.has_full_ratchet && <span className="text-xs px-1.5 py-0.5 rounded bg-accent-red/20 text-accent-red">FR</span>}
                    {f.has_prefunded_warrants && <span className="text-xs px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-400">PF</span>}
                    {!f.warrants_found && !f.has_atm && !f.has_full_ratchet && !f.has_prefunded_warrants && (
                      <span className="text-gray-600 text-xs">—</span>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3 text-gray-400 max-w-xs truncate">
                  {f.summary ? (
                    f.source_url ? (
                      <a href={f.source_url} target="_blank" rel="noopener noreferrer" className="hover:text-accent transition-colors" title={f.summary}>
                        {f.summary.slice(0, 80)}...
                      </a>
                    ) : f.summary.slice(0, 80)
                  ) : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
