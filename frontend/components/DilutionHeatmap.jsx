function dilutionColor(pct) {
  if (pct == null) return 'bg-gray-700';
  if (pct >= 30) return 'bg-accent-red';
  if (pct >= 15) return 'bg-accent-yellow';
  return 'bg-accent-green';
}

export default function DilutionHeatmap({ data, loading, error }) {
  if (loading) {
    return (
      <div className="card">
        <div className="animate-pulse space-y-2">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="h-8 bg-surface-hover rounded" />
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

  if (!data || data.length === 0) {
    return (
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-300 mb-2 uppercase tracking-wide">
          Dilution Heatmap
        </h3>
        <p className="text-gray-500 text-sm">No dilution data yet. Scan SEC filings to populate.</p>
      </div>
    );
  }

  const maxDilution = Math.max(...data.map((d) => d.dilution_percentage || 0), 1);

  return (
    <div className="card">
      <h3 className="text-sm font-semibold text-gray-300 mb-4 uppercase tracking-wide">
        Dilution Heatmap — Top Risks
      </h3>
      <div className="space-y-2">
        {data.map((item, i) => {
          const pct = item.dilution_percentage || 0;
          const width = maxDilution > 0 ? `${Math.max((pct / maxDilution) * 100, 4)}%` : '4%';
          return (
            <div key={item.accession_number || i} className="group">
              <div className="flex justify-between items-center mb-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-600 w-4">{i + 1}</span>
                  <span className="font-mono text-sm font-semibold text-white">
                    {item.ticker || item.cik}
                  </span>
                  <span className="text-xs text-gray-500">{item.form_type}</span>
                  {item.warrants_found && (
                    <span className="text-xs bg-accent-yellow/20 text-accent-yellow px-1.5 py-0.5 rounded">W</span>
                  )}
                </div>
                <span className="text-xs font-semibold text-gray-300">
                  {pct > 0 ? `${pct.toFixed(1)}%` : 'N/A'}
                </span>
              </div>
              <div className="h-6 bg-surface rounded overflow-hidden">
                <div
                  className={`h-full rounded transition-all duration-700 ${dilutionColor(pct)} opacity-80 group-hover:opacity-100`}
                  style={{ width }}
                />
              </div>
            </div>
          );
        })}
      </div>
      <div className="flex gap-4 mt-4 text-xs text-gray-500">
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-accent-green inline-block" /> Low</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-accent-yellow inline-block" /> Med</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-accent-red inline-block" /> High</span>
      </div>
    </div>
  );
}
