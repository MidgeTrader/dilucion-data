const SEVERITY = {
  high: { dot: 'bg-accent-red', badge: 'bg-accent-red/20 text-accent-red', label: 'High' },
  medium: { dot: 'bg-accent-yellow', badge: 'bg-accent-yellow/20 text-accent-yellow', label: 'Med' },
  low: { dot: 'bg-accent-green', badge: 'bg-accent-green/20 text-accent-green', label: 'Low' },
};

function formatDate(d) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

export default function TickerInsightsView({ data, loading, tickerUpper }) {
  const insights = data?.insights || [];

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-8 w-48 bg-surface-hover rounded" />
        {[...Array(4)].map((_, i) => <div key={i} className="h-28 bg-surface-hover rounded-card" />)}
      </div>
    );
  }

  const bySeverity = {
    high: insights.filter((i) => i.severity === 'high').length,
    medium: insights.filter((i) => i.severity === 'medium').length,
    low: insights.filter((i) => i.severity === 'low').length,
  };

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold text-white">Insights</h1>
        <p className="text-sm text-gray-500 mt-1">
          AI-generated analysis of dilution risk, warrants, and cash runway for {tickerUpper}.
        </p>
      </div>

      <div className="flex gap-3">
        {Object.entries(bySeverity).map(([sev, count]) => {
          const cfg = SEVERITY[sev];
          return (
            <div key={sev} className="card card-inner flex items-center gap-3 flex-1 min-w-0">
              <div className={`w-2 h-2 rounded-full ${cfg.dot}`} />
              <div>
                <p className="text-lg font-bold text-white">{count}</p>
                <p className="text-xs text-gray-500">{cfg.label} priority</p>
              </div>
            </div>
          );
        })}
      </div>

      <div className="space-y-3">
        {insights.map((insight) => {
          const cfg = SEVERITY[insight.severity] || SEVERITY.medium;
          return (
            <article key={insight.id} className="card card-inner hover:border-gray-700 transition-colors">
              <div className="flex items-start justify-between gap-3 mb-2">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded ${cfg.badge}`}>
                    {cfg.label}
                  </span>
                  <span className="text-xs text-gray-600 bg-surface-muted px-2 py-0.5 rounded">
                    {insight.category}
                  </span>
                  {insight.source_form && (
                    <span className="font-mono text-xs text-accent-teal">{insight.source_form}</span>
                  )}
                </div>
                <time className="text-xs text-gray-600 shrink-0">{formatDate(insight.date)}</time>
              </div>
              <h3 className="text-sm font-semibold text-white mb-2">{insight.title}</h3>
              <p className="text-sm text-gray-400 leading-relaxed">{insight.body}</p>
            </article>
          );
        })}
      </div>

      {insights.length === 0 && (
        <div className="card card-inner text-center py-12">
          <p className="text-gray-500 text-sm">No insights yet. Run a scan to generate AI analysis.</p>
          <code className="text-xs text-accent-teal font-mono mt-2 block">python main.py scan {tickerUpper}</code>
        </div>
      )}
    </div>
  );
}
