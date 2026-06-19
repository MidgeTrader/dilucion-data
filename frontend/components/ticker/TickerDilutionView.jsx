import RiskPanel from '../RiskPanel';

function fmtUSD(n) {
  if (n == null) return '—';
  if (n >= 1e9) return `$${(n / 1e9).toFixed(1)}B`;
  if (n >= 1e6) return `$${(n / 1e6).toFixed(1)}M`;
  return `$${n.toLocaleString()}`;
}

function fmtNum(n) {
  if (n == null) return '—';
  if (n >= 1e6) return `${(n / 1e6).toFixed(2)}M`;
  if (n >= 1e3) return `${(n / 1e3).toFixed(0)}K`;
  return n.toLocaleString();
}

function ProgressBar({ value, max, color = 'bg-accent-teal' }) {
  const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0;
  return (
    <div className="h-1.5 bg-surface-muted rounded-full overflow-hidden">
      <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
    </div>
  );
}

function SeverityBadge({ level }) {
  const styles = {
    HIGH: 'bg-accent-red/20 text-accent-red',
    MEDIUM: 'bg-accent-yellow/20 text-accent-yellow',
    LOW: 'bg-accent-green/20 text-accent-green',
  };
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded ${styles[level] || styles.MEDIUM}`}>
      {level}
    </span>
  );
}

export default function TickerDilutionView({ data, loading, tickerUpper }) {
  const d = data?.dilution;
  const risk = data?.risk;

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-8 w-48 bg-surface-hover rounded" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => <div key={i} className="h-40 bg-surface-hover rounded-card" />)}
        </div>
      </div>
    );
  }

  if (!d) return null;

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white">Dilution</h1>
          <p className="text-sm text-gray-500 mt-1">
            Shelf capacity, ATM usage, warrant overhang and dilution timeline for {tickerUpper}.
          </p>
        </div>
        <div className="text-right shrink-0">
          <p className="text-3xl font-bold text-white">{d.estimated_dilution_pct?.toFixed(1)}%</p>
          <p className="text-xs text-gray-500">Est. max dilution</p>
          <div className="mt-1"><SeverityBadge level={d.risk_level} /></div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card card-inner">
          <h3 className="text-sm font-semibold text-white mb-3">Shelf Registration</h3>
          {d.shelf?.active ? (
            <>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-500">Capacity</span>
                <span className="text-white font-medium">{fmtUSD(d.shelf.capacity_usd)}</span>
              </div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-500">Remaining</span>
                <span className="text-white font-medium">{fmtUSD(d.shelf.remaining_usd)}</span>
              </div>
              <ProgressBar value={d.shelf.capacity_usd - d.shelf.remaining_usd} max={d.shelf.capacity_usd} color="bg-accent-yellow" />
              <p className="text-xs text-gray-600 mt-2">Expires {d.shelf.expiration}</p>
            </>
          ) : (
            <p className="text-sm text-gray-500">No active shelf</p>
          )}
        </div>

        <div className="card card-inner">
          <h3 className="text-sm font-semibold text-white mb-3">ATM Program</h3>
          {d.atm?.active ? (
            <>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-500">Capacity</span>
                <span className="text-white font-medium">{fmtUSD(d.atm.capacity_usd)}</span>
              </div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-500">Used</span>
                <span className="text-white font-medium">{fmtUSD(d.atm.used_usd)}</span>
              </div>
              <ProgressBar value={d.atm.used_usd} max={d.atm.capacity_usd} color="bg-accent-red" />
              <p className="text-xs text-gray-600 mt-2">Agent: {d.atm.agent}</p>
            </>
          ) : (
            <p className="text-sm text-gray-500">No active ATM</p>
          )}
        </div>

        <div className="card card-inner">
          <h3 className="text-sm font-semibold text-white mb-3">Share Structure</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Float</span>
              <span className="text-white">{fmtNum(d.share_structure?.float)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Outstanding</span>
              <span className="text-white">{fmtNum(d.share_structure?.outstanding)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Fully Diluted</span>
              <span className="text-accent-yellow font-medium">{fmtNum(d.share_structure?.fully_diluted)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Cash Runway</span>
              <span className="text-white">~{d.share_structure?.cash_months} months</span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-4">
        <div className="card overflow-hidden">
          <div className="px-4 py-3 border-b border-surface-border">
            <h3 className="text-sm font-semibold text-white">Warrant Overhang</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-500 text-xs border-b border-surface-border">
                  <th className="text-left px-4 py-2 font-medium">Type</th>
                  <th className="text-left px-4 py-2 font-medium">Count</th>
                  <th className="text-left px-4 py-2 font-medium">Exercise</th>
                  <th className="text-left px-4 py-2 font-medium">Expiration</th>
                  <th className="text-left px-4 py-2 font-medium">ITM</th>
                </tr>
              </thead>
              <tbody>
                {(d.warrants || []).map((w, i) => (
                  <tr key={i} className="border-b border-surface-border/50 hover:bg-surface-hover/50">
                    <td className="px-4 py-2.5 text-gray-300">{w.type}</td>
                    <td className="px-4 py-2.5 font-mono text-gray-400">{fmtNum(w.count)}</td>
                    <td className="px-4 py-2.5 font-mono text-accent-teal">${w.exercise_price?.toFixed(2)}</td>
                    <td className="px-4 py-2.5 text-gray-500">{w.expiration}</td>
                    <td className="px-4 py-2.5">
                      {w.in_the_money ? (
                        <span className="text-xs text-accent-green">Yes</span>
                      ) : (
                        <span className="text-xs text-gray-600">No</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <RiskPanel risk={risk} loading={false} />
      </div>

      <div className="card card-inner">
        <h3 className="text-sm font-semibold text-white mb-4">Dilution Timeline</h3>
        <div className="space-y-0">
          {(d.events || []).map((ev, i) => (
            <div key={i} className="flex gap-4 py-3 border-b border-surface-border/50 last:border-0">
              <div className="shrink-0 w-20 text-xs text-gray-500 pt-0.5">{ev.date}</div>
              <div className="shrink-0">
                <span className="font-mono text-xs text-accent-teal bg-accent-teal/10 px-2 py-0.5 rounded">{ev.type}</span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-300">{ev.description}</p>
              </div>
              {ev.impact_pct != null && (
                <div className="shrink-0 text-sm font-semibold text-accent-red">+{ev.impact_pct}%</div>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {d.flags?.warrants_found && <span className="text-xs px-2 py-1 rounded bg-accent-yellow/20 text-accent-yellow">Warrants</span>}
        {d.flags?.has_atm && <span className="text-xs px-2 py-1 rounded bg-blue-500/20 text-blue-400">ATM Active</span>}
        {d.flags?.has_full_ratchet && <span className="text-xs px-2 py-1 rounded bg-accent-red/20 text-accent-red">Full Ratchet</span>}
        {d.flags?.has_prefunded_warrants && <span className="text-xs px-2 py-1 rounded bg-purple-500/20 text-purple-400">Prefunded Warrants</span>}
      </div>
    </div>
  );
}
