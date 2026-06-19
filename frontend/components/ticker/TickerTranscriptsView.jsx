import { useState } from 'react';

function formatDate(d) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

export default function TickerTranscriptsView({ data, loading, tickerUpper }) {
  const transcripts = data?.transcripts || [];
  const [expanded, setExpanded] = useState(null);

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-8 w-40 bg-surface-hover rounded" />
        {[...Array(3)].map((_, i) => <div key={i} className="h-24 bg-surface-hover rounded-card" />)}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold text-white">Transcripts</h1>
        <p className="text-sm text-gray-500 mt-1">Earnings call transcripts for {tickerUpper}.</p>
      </div>

      <div className="space-y-3">
        {transcripts.length === 0 ? (
          <div className="card card-inner text-center py-12">
            <p className="text-gray-500 text-sm">No transcripts available.</p>
          </div>
        ) : (
          transcripts.map((t) => {
            const isOpen = expanded === t.id;
            return (
              <div key={t.id} className="card overflow-hidden">
                <button
                  type="button"
                  onClick={() => setExpanded(isOpen ? null : t.id)}
                  className="w-full flex items-center justify-between px-4 py-4 hover:bg-surface-hover/50 transition-colors text-left"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-lg bg-surface-muted border border-surface-border flex items-center justify-center">
                      <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                      </svg>
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-white">{t.title}</h3>
                      <p className="text-xs text-gray-500 mt-0.5">
                        {t.quarter} · {formatDate(t.date)} · {t.duration}
                      </p>
                    </div>
                  </div>
                  <svg
                    className={`w-5 h-5 text-gray-500 transition-transform ${isOpen ? 'rotate-180' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {isOpen && (
                  <div className="px-4 pb-4 border-t border-surface-border/50">
                    <p className="text-xs text-gray-500 uppercase tracking-wide mt-3 mb-2">Key Highlights</p>
                    <ul className="space-y-1.5">
                      {(t.highlights || []).map((h, i) => (
                        <li key={i} className="text-sm text-gray-400 flex items-start gap-2">
                          <span className="text-accent-teal mt-1">•</span>
                          {h}
                        </li>
                      ))}
                    </ul>
                    <p className="text-xs text-gray-600 mt-4 italic">
                      Full transcript available after connecting Aiera or SEC audio sources.
                    </p>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
