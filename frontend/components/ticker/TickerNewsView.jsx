function formatDate(d) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function sourceBadge(type) {
  const labels = {
    sec: 'SEC',
    massive: 'Massive',
    polygon: 'Massive',
    eodhd: 'EODHD',
    yfinance: 'Yahoo',
    finnhub: 'Finnhub',
    google: 'Google',
    benzinga: 'Benzinga',
  };
  return labels[type] || null;
}

export default function TickerNewsView({ data, loading, tickerUpper }) {
  const news = data?.news || data?.articles || [];

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-8 w-32 bg-surface-hover rounded" />
        {[...Array(5)].map((_, i) => <div key={i} className="h-16 bg-surface-hover rounded-card" />)}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold text-white">News</h1>
        <p className="text-sm text-gray-500 mt-1">
          Aggregated from SEC, Massive, EODHD, Yahoo, Finnhub, Google News, Benzinga.
        </p>
      </div>

      <div className="card divide-y divide-surface-border/50 overflow-hidden">
        {news.length === 0 ? (
          <p className="px-4 py-12 text-center text-gray-600 text-sm">No news articles found.</p>
        ) : (
          news.map((item, i) => (
            <a
              key={i}
              href={item.url || '#'}
              target="_blank"
              rel="noopener noreferrer"
              className="flex gap-4 px-4 py-4 hover:bg-surface-hover/50 transition-colors group"
            >
              <div className="shrink-0 w-16 text-center">
                <p className="text-xs text-gray-600">{formatDate(item.date).split(',')[0]}</p>
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-medium text-gray-200 group-hover:text-white leading-snug mb-1">
                  {item.title}
                </h3>
                <p className="text-xs text-gray-600 flex items-center gap-2">
                  {item.source}
                  {sourceBadge(item.source_type) && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-surface-muted text-gray-500">
                      {sourceBadge(item.source_type)}
                    </span>
                  )}
                </p>
              </div>
              <svg className="w-4 h-4 text-gray-700 group-hover:text-gray-400 shrink-0 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
            </a>
          ))
        )}
      </div>
    </div>
  );
}
