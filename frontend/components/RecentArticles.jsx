function formatDate(d) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

export default function RecentArticles({ articles, loading }) {
  if (loading) {
    return (
      <div className="card card-inner animate-pulse">
        <div className="h-5 w-32 bg-surface-hover rounded mb-4" />
        {[...Array(3)].map((_, i) => <div key={i} className="h-12 bg-surface-hover rounded mb-2" />)}
      </div>
    );
  }

  const rows = articles || [];

  return (
    <div className="card overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-surface-border">
        <h3 className="text-sm font-semibold text-white">Recent Articles</h3>
        <button type="button" className="text-xs text-gray-500 hover:text-white">
          View All
        </button>
      </div>
      <div className="divide-y divide-surface-border/50">
        {rows.length === 0 ? (
          <p className="px-4 py-6 text-center text-gray-600 text-sm">No recent articles</p>
        ) : (
          rows.map((a, i) => (
            <a
              key={i}
              href={a.url || '#'}
              target="_blank"
              rel="noopener noreferrer"
              className="block px-4 py-3 hover:bg-surface-hover/50 transition-colors"
            >
              <p className="text-sm text-gray-200 leading-snug mb-1">{a.title}</p>
              <p className="text-xs text-gray-600">
                {a.source} · {formatDate(a.date)}
              </p>
            </a>
          ))
        )}
      </div>
    </div>
  );
}
