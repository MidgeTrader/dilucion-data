import Link from 'next/link';

function formatDate(d) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

export default function RecentFilings({ filings, ticker, loading }) {
  if (loading) {
    return (
      <div className="card card-inner animate-pulse">
        <div className="h-5 w-32 bg-surface-hover rounded mb-4" />
        {[...Array(3)].map((_, i) => <div key={i} className="h-10 bg-surface-hover rounded mb-2" />)}
      </div>
    );
  }

  const rows = (filings || []).slice(0, 5);

  return (
    <div className="card overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-surface-border">
        <h3 className="text-sm font-semibold text-white">Recent Filings</h3>
        <Link href={`/ticker/${ticker || 'SPHL'}/filings`} className="text-xs text-gray-500 hover:text-white">
          View All
        </Link>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-500 text-xs border-b border-surface-border">
              <th className="text-left px-4 py-2 font-medium">Type</th>
              <th className="text-left px-4 py-2 font-medium">Title</th>
              <th className="text-left px-4 py-2 font-medium whitespace-nowrap">Date Released</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={3} className="px-4 py-6 text-center text-gray-600 text-sm">
                  No filings indexed for {ticker}
                </td>
              </tr>
            ) : (
              rows.map((f) => (
                <tr key={f.accession_number} className="border-b border-surface-border/50 hover:bg-surface-hover/50">
                  <td className="px-4 py-2.5">
                    {f.source_url ? (
                      <a href={f.source_url} target="_blank" rel="noopener noreferrer" className="font-mono text-xs text-accent-teal hover:text-white transition-colors">
                        {f.form_type}
                      </a>
                    ) : (
                      <span className="font-mono text-xs text-accent-teal">{f.form_type}</span>
                    )}
                  </td>
                  <td className="px-4 py-2.5 text-gray-300 text-sm max-w-md truncate">
                    {f.source_url ? (
                      <a href={f.source_url} target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">
                        {f.summary || f.form_type + ' Filing — ' + formatDate(f.filed_date)}
                      </a>
                    ) : (
                      f.summary || f.form_type + ' Filing — ' + formatDate(f.filed_date)
                    )}
                  </td>
                  <td className="px-4 py-2.5 text-gray-500 text-sm whitespace-nowrap">{formatDate(f.filed_date)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
