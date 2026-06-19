export default function InfoCard({ title, rows = [], loading, compact = false }) {
  if (loading) {
    return (
      <div className="card kpi-card animate-pulse">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="kpi-row">
            <div className="h-3 w-20 bg-surface-hover rounded" />
            <div className="h-3 w-14 bg-surface-hover rounded" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="card kpi-card h-full">
      {title && (
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider px-4 pt-3 pb-1">{title}</h3>
      )}
      <div className={compact ? '' : ''}>
        {rows.map((row) => (
          <div key={row.label} className="kpi-row">
            <span className="kpi-label flex items-center gap-1.5 min-w-0">
              {row.icon && <span className="shrink-0">{row.icon}</span>}
              <span className="truncate">{row.label}</span>
            </span>
            <span className={`kpi-value ${row.highlight || ''}`}>{row.value ?? '—'}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
