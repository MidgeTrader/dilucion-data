import {
  ComposedChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-surface-card border border-surface-border rounded-lg p-3 text-xs shadow-xl">
      <p className="text-gray-400 mb-1">{d.date}</p>
      <p>O: <span className="text-white">{d.open?.toFixed(2)}</span></p>
      <p>H: <span className="text-accent-green">{d.high?.toFixed(2)}</span></p>
      <p>L: <span className="text-accent-red">{d.low?.toFixed(2)}</span></p>
      <p>C: <span className="text-white font-semibold">{d.close?.toFixed(2)}</span></p>
      {d.volume != null && <p className="text-gray-500 mt-1">Vol: {(d.volume / 1e6).toFixed(2)}M</p>}
    </div>
  );
}

export default function CandlestickChart({ data, loading, error, ticker }) {
  if (loading) {
    return (
      <div className="card h-72 flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="card h-72 flex items-center justify-center">
        <p className="text-accent-red text-sm">{error}</p>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="card h-72 flex items-center justify-center">
        <p className="text-gray-500 text-sm">No price data available for {ticker}.</p>
      </div>
    );
  }

  const chartData = data.map((d) => ({
    ...d,
    range: [d.low, d.high],
    body: Math.abs(d.close - d.open),
    color: d.close >= d.open ? '#22c55e' : '#ef4444',
  }));

  return (
    <div className="card">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">
          Price Chart — {ticker}
        </h3>
        <span className="text-xs text-gray-500">{data.length} days</span>
      </div>
      <ResponsiveContainer width="100%" height={280}>
        <ComposedChart data={chartData} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
          <XAxis
            dataKey="date"
            tick={{ fill: '#6b7280', fontSize: 10 }}
            tickFormatter={(v) => v.slice(5)}
            interval="preserveStartEnd"
          />
          <YAxis
            domain={['auto', 'auto']}
            tick={{ fill: '#6b7280', fontSize: 10 }}
            width={55}
            tickFormatter={(v) => `$${v}`}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="close" fill="#3b82f6" opacity={0.7} radius={[2, 2, 0, 0]} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
