import dynamic from 'next/dynamic';

const TV = dynamic(() => import('./TradingViewWidget'), { ssr: false });

export default function CandlestickChart({ data, loading, ticker, profile }) {
  if (loading) {
    return (
      <div className="card min-h-[360px] flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-teal-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!ticker) {
    return (
      <div className="card min-h-[360px] flex items-center justify-center text-gray-500 text-sm">No ticker</div>
    );
  }

  const p = profile?.price;
  const c = profile?.change_percent;

  return (
    <div className="card flex flex-col h-full min-h-[360px]">
      {/* KPI en vivo más destacado, similar a las InfoCards de abajo */}
      <div className="flex items-center justify-between px-5 pt-4 pb-2 border-b border-surface-border">
        <div className="flex items-baseline gap-2">
          <span className="text-xs font-semibold text-gray-500 uppercase tracking-widest">{ticker}</span>
          <span className="text-xs text-gray-600">· Live</span>
        </div>
        {p != null && (
          <div className="flex items-baseline gap-3">
            <span className="text-3xl font-bold text-white tabular-nums">${Number(p).toFixed(2)}</span>
            {c != null && (
              <span className={`text-base font-semibold ${c >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {c >= 0 ? '+' : ''}{Number(c).toFixed(2)}%
              </span>
            )}
          </div>
        )}
      </div>
      <div className="flex-1 min-h-[300px]">
        <TV ticker={ticker} />
      </div>
    </div>
  );
}
