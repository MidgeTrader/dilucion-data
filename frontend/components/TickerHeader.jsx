export default function TickerHeader({ ticker, profile, onAsk, loading }) {
  if (loading) {
    return (
      <div className="animate-pulse h-16 bg-surface-card rounded-xl mb-4" />
    );
  }

  const price = profile?.price != null ? `$${profile.price.toFixed(2)}` : '—';
  const change = profile?.change_percent;
  const changeStr = change != null ? `${change >= 0 ? '+' : ''}${change.toFixed(2)}%` : null;
  const changeColor = (change || 0) >= 0 ? 'text-accent-green' : 'text-accent-red';

  return (
    <div className="flex items-start justify-between mb-5">
      <div>
        <div className="flex items-center gap-3 flex-wrap">
          <h1 className="text-3xl font-bold font-mono text-white">{ticker}</h1>
          <span className="text-2xl font-semibold">{price}</span>
          {changeStr && <span className={`text-sm font-medium ${changeColor}`}>{changeStr}</span>}
        </div>
        <p className="text-gray-400 text-sm mt-1">{profile?.company_name || '—'}</p>
      </div>
      {onAsk && (
        <button onClick={onAsk} className="btn-primary flex items-center gap-2 shrink-0">
          🤖 Ask about {ticker}
        </button>
      )}
    </div>
  );
}
