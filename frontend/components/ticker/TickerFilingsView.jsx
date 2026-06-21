import { useState, useMemo } from 'react';

// ── AskEdgar-style filing groups ──

const GROUPS = [
  { key: 'Financials',    forms: ['10-K', '10-Q', '10-K/A', '10-Q/A', '20-F', '20-F/A', '40-F'] },
  { key: 'News',          forms: ['8-K', '8-K/A', '6-K'] },
  { key: 'Prospectus',    forms: ['S-3', 'S-3/A', '424B2', '424B3', '424B4', '424B5', 'F-1', 'F-3', 'F-3/A', 'POS AM'] },
  { key: 'Registrations', forms: ['S-1', 'S-1/A', 'S-8', 'DRS', '8-A12B', 'D'] },
  { key: 'Proxies',       forms: ['DEF 14A', 'DEFA14A', 'PRE 14A', 'PREM14A'] },
  { key: 'Ownerships',    forms: ['3', '4', '5', '13G', '13G/A', '13D', '13D/A', 'SCHEDULE 13G', 'SCHEDULE 13G/A'] },
  { key: 'Other',         forms: [] },
];

const FILTER_ORDER = ['All', 'Chronological', ...GROUPS.map((g) => g.key)];

function getGroup(formType) {
  if (!formType) return 'Other';
  for (const g of GROUPS) {
    if (g.forms.some((f) => formType.startsWith(f))) return g.key;
  }
  return 'Other';
}

function isNew(d) {
  if (!d) return false;
  const diff = Date.now() - new Date(d).getTime();
  return diff < 7 * 24 * 60 * 60 * 1000; // last 7 days
}

function formatDate(d) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

// ── Row component for a single filing ──

function FilingRow({ f }) {
  return (
    <tr className="border-b border-surface-border/50 hover:bg-surface-hover/50 transition-colors">
      <td className="px-4 py-2.5 whitespace-nowrap">
        <div className="flex items-center gap-2">
          {f.source_url ? (
            <a
              href={f.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="font-mono text-xs font-semibold text-accent-teal hover:text-white transition-colors"
            >
              {f.form_type}
            </a>
          ) : (
            <span className="font-mono text-xs font-semibold text-accent-teal">{f.form_type}</span>
          )}
          {isNew(f.filed_date) && (
            <span className="text-[10px] font-semibold text-accent-green bg-accent-green/15 px-1.5 py-0.5 rounded">
              NEW
            </span>
          )}
        </div>
      </td>
      <td className="px-4 py-2.5 text-sm text-gray-200 max-w-lg">
        {f.source_url ? (
          <a
            href={f.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-white transition-colors"
          >
            {f.summary || f.title || `${f.form_type} filing`}
          </a>
        ) : (
          f.summary || f.title || `${f.form_type} filing`
        )}
      </td>
      <td className="px-4 py-2.5 text-sm text-gray-500 whitespace-nowrap text-right">
        {formatDate(f.filed_date)}
      </td>
    </tr>
  );
}

// ── Section component for one group ──

function FilingGroupSection({ groupKey, filings, id }) {
  if (!filings || filings.length === 0) return null;

  return (
    <div id={id} className="card overflow-hidden scroll-mt-20">
      <div className="flex items-center gap-2 px-4 py-2.5 border-b border-surface-border bg-surface-muted/30">
        <h3 className="text-xs font-bold text-white uppercase tracking-wider">{groupKey}</h3>
        <span className="text-[11px] text-gray-500">({filings.length})</span>
      </div>
      <div className="overflow-y-auto max-h-[320px]">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-500 text-xs border-b border-surface-border">
              <th className="text-left px-4 py-2 font-medium w-[100px]">TYPE</th>
              <th className="text-left px-4 py-2 font-medium">HEADLINE</th>
              <th className="text-right px-4 py-2 font-medium whitespace-nowrap w-[120px]">FILED AT</th>
            </tr>
          </thead>
          <tbody>
            {filings.map((f) => (
              <FilingRow key={f.accession_number} f={f} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Main view ──

export default function TickerFilingsView({ data, loading, tickerUpper }) {
  const [filter, setFilter] = useState('All');
  const [search, setSearch] = useState('');

  const filings = data?.filings || [];

  // Group filings by category
  const grouped = useMemo(() => {
    let list = [...filings];

    // Apply search
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(
        (f) =>
          f.form_type?.toLowerCase().includes(q) ||
          f.title?.toLowerCase().includes(q) ||
          f.summary?.toLowerCase().includes(q)
      );
    }

    // Build groups
    const groups = {};
    for (const g of GROUPS) groups[g.key] = [];

    for (const f of list) {
      const groupKey = getGroup(f.form_type);
      if (!groups[groupKey]) groups[groupKey] = [];
      groups[groupKey].push(f);
    }

    // Sort each group by date desc
    for (const key of Object.keys(groups)) {
      groups[key].sort((a, b) => new Date(b.filed_date) - new Date(a.filed_date));
    }

    return groups;
  }, [filings, search]);

  // All filings (chronological, for All view)
  const allChronological = useMemo(() => {
    if (filter !== 'Chronological' && filter !== 'All') return [];
    return [...filings]
      .sort((a, b) => new Date(b.filed_date) - new Date(a.filed_date));
  }, [filings, filter]);

  // Filter by search for "All" and "Chronological" modes
  const allFiltered = useMemo(() => {
    if (!search.trim()) return allChronological;
    const q = search.toLowerCase();
    return allChronological.filter(
      (f) =>
        f.form_type?.toLowerCase().includes(q) ||
        f.title?.toLowerCase().includes(q) ||
        f.summary?.toLowerCase().includes(q)
    );
  }, [allChronological, search]);

  // Figure out which group sections to show
  const shownGroups = useMemo(() => {
    if (filter === 'All') {
      return GROUPS.filter((g) => (grouped[g.key] || []).length > 0).map((g) => g.key);
    }
    if (filter === 'Chronological' || !filter) return [];
    return [filter];
  }, [filter, grouped]);

  // Counts for filter tabs
  const counts = useMemo(() => {
    const c = { All: filings.length, Chronological: filings.length };
    for (const g of GROUPS) {
      c[g.key] = (grouped[g.key] || []).length;
    }
    return c;
  }, [filings, grouped]);

  // Loading state
  if (loading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-6 w-20 bg-surface-hover rounded" />
        <div className="h-8 w-full bg-surface-hover rounded" />
        {[...Array(3)].map((_, i) => (
          <div key={i}>
            <div className="h-4 w-24 bg-surface-hover rounded mb-2" />
            <div className="h-32 bg-surface-hover rounded-card" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold text-white">Filings</h1>
        <p className="text-sm text-gray-500 mt-1">
          SEC filings indexed for {tickerUpper} with dilution flags and AI summaries.
        </p>
      </div>

      {/* Search + Filter tabs */}
      <div className="flex flex-col gap-3">
        <input
          type="text"
          placeholder="Search in Documents"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input-search text-sm"
        />
        <div className="flex flex-wrap gap-1">
          {FILTER_ORDER.map((tab) => (
            <button
              key={tab}
              type="button"
              onClick={() => setFilter(tab)}
              className={`text-xs px-3 py-1.5 rounded-md border transition-colors ${
                filter === tab
                  ? 'bg-surface-hover border-surface-border text-white font-medium'
                  : 'border-transparent text-gray-500 hover:text-white hover:bg-surface-hover/50'
              }`}
            >
              {tab}
              {counts[tab] > 0 && (
                <span className="ml-1 text-gray-600">({counts[tab]})</span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Content: Chronological (flat list) or grouped sections */}
      {filter === 'Chronological' ? (
        <div className="card overflow-hidden p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-500 text-xs border-b border-surface-border">
                <th className="text-left px-4 py-2.5 font-medium w-[120px]">TYPE</th>
                <th className="text-left px-4 py-2.5 font-medium">HEADLINE</th>
                <th className="text-right px-4 py-2.5 font-medium whitespace-nowrap w-[140px]">FILED AT</th>
              </tr>
            </thead>
            <tbody>
              {allFiltered.length === 0 ? (
                <tr>
                  <td colSpan={3} className="px-4 py-8 text-center text-gray-600 text-sm">
                    No filings match your search.
                  </td>
                </tr>
              ) : (
                allFiltered.map((f) => (
                  <FilingRow key={f.accession_number} f={f} />
                ))
              )}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
          {shownGroups.length === 0 ? (
            <p className="text-center py-8 text-sm text-gray-500">
              {search ? 'No filings match your search.' : `No filings found for this category.`}
            </p>
          ) : (
            shownGroups.map((groupKey) => (
              <FilingGroupSection
                key={groupKey}
                id={`group-${groupKey}`}
                groupKey={groupKey}
                filings={grouped[groupKey]}
              />
            ))
          )}
        </div>
      )}
    </div>
  );
}
