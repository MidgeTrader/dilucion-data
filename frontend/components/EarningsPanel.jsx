function formatDate(d) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

export default function EarningsPanel({ earnings, loading }) {
  if (loading) {
    return (
      <div className="card card-inner animate-pulse">
        <div className="h-5 w-24 bg-surface-hover rounded mb-4" />
        <div className="h-16 bg-surface-hover rounded" />
      </div>
    );
  }

  const next = earnings?.next;
  const last = earnings?.last;

  return (
    <div className="card card-inner">
      <h3 className="text-sm font-semibold text-white mb-4">Earnings</h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="bg-surface-muted rounded-lg p-3 border border-surface-border/50">
          <p className="text-xs text-gray-500 mb-1">Next Report</p>
          <p className="text-sm text-white font-medium">{next ? formatDate(next.date) : '—'}</p>
          {next?.estimate && (
            <p className="text-xs text-gray-500 mt-1">Est. EPS {next.estimate}</p>
          )}
        </div>
        <div className="bg-surface-muted rounded-lg p-3 border border-surface-border/50">
          <p className="text-xs text-gray-500 mb-1">Last Report</p>
          <p className="text-sm text-white font-medium">{last ? formatDate(last.date) : '—'}</p>
          {last?.eps != null && (
            <p className="text-xs text-gray-500 mt-1">
              EPS {last.eps}
              {last.surprise != null && (
                <span className={last.surprise >= 0 ? ' text-accent-green' : ' text-accent-red'}>
                  {' '}({last.surprise >= 0 ? '+' : ''}{last.surprise}%)
                </span>
              )}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
