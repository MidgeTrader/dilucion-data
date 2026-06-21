/** Full Dilution Tracker — Dilucion Data - Dilution Tracker */
import { useState, useEffect } from 'react';
import { fetchDilutionTracker } from '../../lib/mockData';

// ─── Helpers ──────────────────────────────────────────────────────────────

function fmtUSD(n) {
  if (n == null) return '—';
  if (n >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
  if (n >= 1e6) return `$${(n / 1e6).toFixed(2)}M`;
  if (n >= 1e3) return `$${(n / 1e3).toFixed(2)}K`;
  return `$${n.toLocaleString()}`;
}

function fmtNum(n) {
  if (n == null) return '—';
  if (n >= 1e9) return `${(n / 1e9).toFixed(2)}B`;
  if (n >= 1e6) return `${(n / 1e6).toFixed(2)}M`;
  if (n >= 1e3) return `${(n / 1e3).toFixed(1)}K`;
  return n.toLocaleString();
}

function fmtDate(d) {
  if (!d) return '—';
  try { return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }); }
  catch { return d; }
}

function Badge({ label, color = 'bg-gray-700 text-gray-300' }) {
  return <span className={`text-xs px-2 py-0.5 rounded ${color}`}>{label}</span>;
}

function SeverityBadge({ level }) {
  const m = { HIGH: 'bg-accent-red/20 text-accent-red', MEDIUM: 'bg-accent-yellow/20 text-accent-yellow', LOW: 'bg-accent-green/20 text-accent-green' };
  return <span className={`text-xs font-semibold px-2 py-0.5 rounded ${m[level] || m.MEDIUM}`}>{level}</span>;
}

function SectionTitle({ title, subtitle, right }) {
  return (
    <div className="flex items-center justify-between mb-4">
      <div>
        <h2 className="text-base font-semibold text-white">{title}</h2>
        {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
      </div>
      {right && <div className="shrink-0">{right}</div>}
    </div>
  );
}

function DataTable({ headers, rows, keyFn, emptyMsg = 'No data' }) {
  if (!rows || rows.length === 0) {
    return <p className="text-sm text-gray-500 italic">{emptyMsg}</p>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-gray-500 text-xs border-b border-surface-border">
            {headers.map((h, i) => (
              <th key={i} className={`text-left px-3 py-2 font-medium ${i > 0 ? 'whitespace-nowrap' : ''}`}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => {
            const cells = keyFn(row, i);
            return (
              <tr key={i} className="border-b border-surface-border/30 hover:bg-surface-hover/50">
                {cells.map((cell, j) => (
                  <td key={j} className={`px-3 py-2.5 ${j === 0 ? 'text-gray-300' : 'text-gray-400 font-mono'}`}>
                    {cell ?? '—'}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function Card({ children, className = '' }) {
  return <div className={`card ${className}`}>{children}</div>;
}

function LoadingSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="h-8 w-64 bg-surface-hover rounded" />
      {[1,2,3,4,5].map(i => <div key={i} className="h-40 bg-surface-hover rounded-card" />)}
    </div>
  );
}

// ─── Sections ──────────────────────────────────────────────────────────────

function CashPositionSection({ cp }) {
  if (!cp) return null;
  return (
    <Card>
      <SectionTitle title="Cash Position" subtitle="Based on latest 10-Q / 10-K filing" right={
        cp.going_concern ? <Badge label="⚠ Going Concern" color="bg-accent-red/20 text-accent-red" /> : null
      } />
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <p className="text-xs text-gray-500">Cash Estimated</p>
          <p className="text-lg font-semibold text-white">{fmtUSD(cp.cash_estimated)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Quarterly Burn</p>
          <p className="text-lg font-semibold text-white">{fmtUSD(cp.quarterly_burn)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Months of Cash</p>
          <p className={`text-lg font-semibold ${cp.months_of_cash != null && cp.months_of_cash < 6 ? 'text-accent-red' : 'text-white'}`}>
            {cp.months_of_cash != null ? `${cp.months_of_cash.toFixed(1)} months` : '—'}
          </p>
        </div>
      </div>
    </Card>
  );
}

function PendingOfferingSection({ po }) {
  if (!po || !po.type) return null;
  return (
    <Card>
      <SectionTitle title="Pending Offering" subtitle={po.type} />
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        {po.shares != null && (
          <div><p className="text-gray-500 text-xs">Shares</p><p className="text-white font-mono">{fmtNum(po.shares)}</p></div>
        )}
        {po.price != null && (
          <div><p className="text-gray-500 text-xs">Price</p><p className="text-white font-mono">${po.price.toFixed(2)}</p></div>
        )}
        {po.warrants != null && (
          <div><p className="text-gray-500 text-xs">Warrants</p><p className="text-white font-mono">{fmtNum(po.warrants)}</p></div>
        )}
        {po.date && (
          <div><p className="text-gray-500 text-xs">Date</p><p className="text-gray-300">{fmtDate(po.date)}</p></div>
        )}
      </div>
    </Card>
  );
}

function ShelfSection({ shelf, price }) {
  if (!shelf) return null;
  return (
    <Card>
      <SectionTitle title="Shelf Registration" subtitle={shelf.active ? 'Active S-3 / S-3/A' : 'No active shelf'} />
      {shelf.active ? (
        <div className="space-y-3">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
            <div><p className="text-gray-500 text-xs">Total Offering</p><p className="text-white font-mono">{fmtUSD(shelf.total_offering)}</p></div>
            <div><p className="text-gray-500 text-xs">Amt Sold Last 12M</p><p className="text-white font-mono">{fmtUSD(shelf.amt_sold_last_12m)}</p></div>
            <div><p className="text-gray-500 text-xs">Raisable Remaining</p><p className="text-accent-yellow font-mono">{fmtUSD(shelf.raisable_total)}</p></div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div><p className="text-gray-500 text-xs">Float</p><p className="text-white font-mono">{fmtNum(shelf.float_shares)}</p></div>
            <div><p className="text-gray-500 text-xs">60-Day High</p><p className="text-white font-mono">{shelf.sixty_day_high_price != null ? `$${shelf.sixty_day_high_price.toFixed(2)}` : '—'}</p></div>
            <div>
              <p className="text-gray-500 text-xs">Price to Exceed Baby Shelf</p>
              <p className="text-white font-mono">{shelf.price_to_exceed_baby_shelf != null ? `$${shelf.price_to_exceed_baby_shelf.toFixed(2)}` : '—'}</p>
            </div>
            <div><p className="text-gray-500 text-xs">Expiration</p><p className="text-gray-300">{fmtDate(shelf.expiration)}</p></div>
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div><p className="text-gray-500 text-xs">Float Value</p><p className="text-white font-mono">{fmtUSD(shelf.float_value)}</p></div>
            <div>
              <p className="text-gray-500 text-xs">Over Baby Shelf</p>
              <Badge label={shelf.over_baby_shelf ? 'Yes ✓' : 'No ✗'} color={shelf.over_baby_shelf ? 'bg-accent-green/20 text-accent-green' : 'bg-accent-red/20 text-accent-red'} />
            </div>
          </div>
        </div>
      ) : (
        <p className="text-sm text-gray-500">No shelf registration detected.</p>
      )}
    </Card>
  );
}

function ATMProgramsSection({ atms }) {
  if (!atms || atms.length === 0) return null;
  return (
    <Card>
      <SectionTitle title="ATM Programs" subtitle={`${atms.length} active program(s)`} />
      <DataTable
        headers={['Name', 'Remaining', 'Total Amt', 'Bank', 'Date']}
        rows={atms}
        keyFn={(a) => [a.name, fmtUSD(a.remaining), fmtUSD(a.total_amt), a.bank || '—', fmtDate(a.date)]}
        emptyMsg="No ATM programs"
      />
    </Card>
  );
}

function PendingEventsSection({ events }) {
  if (!events || events.length === 0) return null;
  const urgencyColor = { HIGH: 'bg-accent-red/20 text-accent-red', MEDIUM: 'bg-accent-yellow/20 text-accent-yellow', LOW: 'bg-accent-green/20 text-accent-green' };
  return (
    <Card>
      <SectionTitle title="Pending Dilution Events" subtitle="Active sources that could still dilute" />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
        {events.map((e, i) => (
          <div key={i} className="flex items-center gap-2 p-2 rounded-lg bg-surface-hover/30 border border-surface-border/30 text-xs">
            <span className={`shrink-0 font-semibold px-1.5 py-0.5 rounded ${urgencyColor[e.urgency] || urgencyColor.MEDIUM}`}>{e.urgency}</span>
            <span className="font-medium text-white truncate">{e.label}</span>
            <span className="text-gray-500 truncate hidden sm:inline">{e.detail}</span>
            <span className="text-gray-600 italic truncate hidden lg:inline">{e.trigger_condition}</span>
            {e.max_dilution_shares != null && <span className="shrink-0 font-mono text-accent-red">{e.max_dilution_shares >= 1e6 ? `${(e.max_dilution_shares / 1e6).toFixed(1)}M` : `${(e.max_dilution_shares / 1e3).toFixed(0)}K`}</span>}
          </div>
        ))}
      </div>
    </Card>
  );
}

function WarrantsSection({ warrants }) {
  if (!warrants || warrants.length === 0) return null;
  return (
    <Card>
      <SectionTitle title="Warrants" subtitle={`${warrants.length} issue(s) outstanding`} />
      <DataTable
        headers={['Issue', 'Remaining', 'Exercise Price', 'Owners', 'Protection']}
        rows={warrants}
        keyFn={(w) => [
          w.issue_label,
          fmtNum(w.remaining),
          w.exercise_price != null ? `$${w.exercise_price.toFixed(2)}` : '—',
          w.owners?.join(', ') || '—',
          <Badge key="p" label={w.protection || '—'} color={w.protection === 'Full Ratchet' ? 'bg-accent-red/20 text-accent-red' : 'bg-gray-600 text-gray-300'} />,
        ]}
        emptyMsg="No warrants detected"
      />
    </Card>
  );
}

function ConvertiblesSection({ convertibles }) {
  if (!convertibles || convertibles.length === 0) return null;
  return (
    <Card>
      <SectionTitle title="Convertibles" subtitle="Convertible notes and debentures" />
      <DataTable
        headers={['Issue', 'Total', 'Remaining', 'Conversion Price', 'Protection', 'Owner']}
        rows={convertibles}
        keyFn={(c) => [
          c.issue_label,
          fmtUSD(c.total),
          fmtUSD(c.remaining),
          c.conversion_price != null ? `$${c.conversion_price.toFixed(2)}` : '—',
          <Badge key="p" label={c.protection || '—'} color={c.protection === 'Full Ratchet' ? 'bg-accent-red/20 text-accent-red' : 'bg-gray-600 text-gray-300'} />,
          c.owner || '—',
        ]}
        emptyMsg="No convertibles detected"
      />
    </Card>
  );
}

function EquityLinesSection({ lines }) {
  if (!lines || lines.length === 0) return null;
  return (
    <Card>
      <SectionTitle title="Equity Lines" subtitle="Committed equity / SPA agreements" />
      {lines.map((el, i) => (
        <div key={i} className="space-y-2 text-sm">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div><p className="text-gray-500 text-xs">Total Amount</p><p className="text-white font-mono">{fmtUSD(el.total_amt)}</p></div>
            <div><p className="text-gray-500 text-xs">Shares</p><p className="text-white font-mono">{fmtNum(el.shares)}</p></div>
            <div><p className="text-gray-500 text-xs">ATM Remaining</p><p className="text-white font-mono">{fmtUSD(el.atm_remaining)}</p></div>
            <div><p className="text-gray-500 text-xs">Date</p><p className="text-gray-300">{fmtDate(el.date)}</p></div>
          </div>
          {el.pricing_mechanism && (
            <div><p className="text-gray-500 text-xs">Pricing</p><p className="text-gray-400 text-xs mt-1">{el.pricing_mechanism}</p></div>
          )}
          <div className="flex gap-4 text-xs text-gray-500">
            {el.max_daily_shares && <span>Max daily: {el.max_daily_shares} shares</span>}
            {el.max_daily_amount && <span>Max daily: {el.max_daily_amount}</span>}
          </div>
        </div>
      ))}
    </Card>
  );
}

function CompletedOfferingsSection({ offerings }) {
  if (!offerings || offerings.length === 0) return null;
  return (
    <Card>
      <SectionTitle title="Completed Offerings" subtitle="Chronological history" />
      <DataTable
        headers={['Date', 'Type', 'Amount', 'Shares', 'Price', 'Warrants', 'Bank']}
        rows={offerings}
        keyFn={(o) => [
          fmtDate(o.date),
          <Badge key="t" label={o.type} color="bg-accent-teal/20 text-accent-teal" />,
          fmtUSD(o.amount),
          fmtNum(o.shares),
          o.price != null ? `$${o.price.toFixed(2)}` : '—',
          fmtNum(o.warrants),
          o.bank || '—',
        ]}
        emptyMsg="No completed offerings"
      />
    </Card>
  );
}

function LockUpSection({ locks }) {
  if (!locks || locks.length === 0) return null;
  return (
    <Card>
      <SectionTitle title="Lock-Up Agreements" subtitle="Post-offering restrictions" />
      <DataTable
        headers={['Description', 'Duration', 'Date Filed', 'Filing Type']}
        rows={locks}
        keyFn={(l) => [l.description, l.duration_days ? `${l.duration_days} days` : '—', fmtDate(l.date_filed), l.filing_type || '—']}
        emptyMsg="No lock-up agreements"
      />
    </Card>
  );
}

function NasdaqComplianceSection({ items }) {
  if (!items || items.length === 0) return null;
  return (
    <Card>
      <SectionTitle title="NASDAQ Compliance" subtitle="Listing standards tracking" />
      <DataTable
        headers={['Date', 'Rule', 'Exchange', 'Status', 'Details']}
        rows={items}
        keyFn={(n) => [
          fmtDate(n.date),
          n.rule || '—',
          n.exchange || 'NASDAQ',
          <Badge key="s" label={n.status} color={n.status === 'RESOLVED' ? 'bg-accent-green/20 text-accent-green' : 'bg-accent-yellow/20 text-accent-yellow'} />,
          n.details || '—',
        ]}
        emptyMsg="No compliance issues"
      />
    </Card>
  );
}

function ReverseSplitsSection({ splits }) {
  if (!splits || splits.length === 0) return null;
  return (
    <Card>
      <SectionTitle title="Reverse Splits" subtitle="Historical" />
      <DataTable
        headers={['Date', 'Ratio']}
        rows={splits}
        keyFn={(s) => [fmtDate(s.date), s.ratio || '—']}
        emptyMsg="No reverse splits"
      />
    </Card>
  );
}

// ─── Main Component ────────────────────────────────────────────────────────

export default function TickerDilutionView({ data, loading, tickerUpper }) {
  const [tracker, setTracker] = useState(null);
  const [trackerLoading, setTrackerLoading] = useState(true);
  const [trackerError, setTrackerError] = useState(null);

  // Fetch dedicated dilution tracker endpoint
  useEffect(() => {
    if (!tickerUpper) return;
    setTrackerLoading(true);
    setTrackerError(null);

    fetchDilutionTracker(tickerUpper)
      .then(setTracker)
      .catch(e => {
        // Fallback: extract from main ticker data
        if (data?.dilution) {
          setTracker(data.dilution);
        } else {
          setTrackerError(String(e));
        }
      })
      .finally(() => setTrackerLoading(false));
  }, [tickerUpper]);

  const d = tracker || data?.dilution;
  const risk = data?.risk;
  const profile = data?.profile;
  const isLoad = loading || trackerLoading;

  if (isLoad && !d) return <LoadingSkeleton />;
  if (!d && trackerError) {
    return (
      <div className="space-y-4">
        <h1 className="text-xl font-bold text-white">Dilution Tracker</h1>
        <Card>
          <p className="text-accent-red text-sm">{trackerError}</p>
          <p className="text-gray-500 text-xs mt-2">Run <code className="font-mono">python main.py scan {tickerUpper}</code> in the backend first, or start the API server.</p>
        </Card>
      </div>
    );
  }

  // Merge tracker data with profile
  const price = d.price || profile?.price;
  const mktCap = d.market_cap || profile?.market_cap;

  return (
    <div className="space-y-4">
      {/* ── Header ── */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white">Dilution Tracker</h1>
          <p className="text-sm text-gray-500 mt-1">
            {tickerUpper}
            {d.company_name ? ` — ${d.company_name}` : ''}
          </p>
        </div>
        <div className="text-right shrink-0">
          <p className="text-xs text-gray-500">Est. Max Dilution</p>
          <p className="text-3xl font-bold text-white">{d.estimated_dilution_pct != null ? `${d.estimated_dilution_pct.toFixed(1)}%` : '—'}</p>
          <div className="mt-1">
            <SeverityBadge level={d.risk_level} />
          </div>
        </div>
      </div>

      {/* ── Quick Stats ── */}
      <div className="flex flex-wrap gap-3 text-xs text-gray-400">
        {price != null && <span><span className="text-gray-600">Price:</span> ${price.toFixed(2)}</span>}
        {mktCap != null && <span><span className="text-gray-600">Mkt Cap:</span> {fmtUSD(mktCap)}</span>}
        {d.country && <span><span className="text-gray-600">Country:</span> {d.country}</span>}
        {d.sector && <span><span className="text-gray-600">Sector:</span> {d.sector}</span>}
        {d.exchange && <span><span className="text-gray-600">Exchange:</span> {d.exchange}</span>}
      </div>

      {/* ── Sections ── */}
      <CashPositionSection cp={d.cash_position} />
      <PendingOfferingSection po={d.pending_offering} />
      <ShelfSection shelf={d.shelf} price={price} />
      <ATMProgramsSection atms={d.atms} />
      <PendingEventsSection events={d.pending_events} />
      <WarrantsSection warrants={d.warrants} />
      <ConvertiblesSection convertibles={d.convertibles} />
      <EquityLinesSection lines={d.equity_lines} />
      <CompletedOfferingsSection offerings={d.completed_offerings} />
      <LockUpSection locks={d.lock_up_agreements} />
      <NasdaqComplianceSection items={d.nasdaq_compliance} />
      <ReverseSplitsSection splits={d.reverse_splits} />
    </div>
  );
}
