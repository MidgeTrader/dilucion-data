const LEVELS = {
  Low: { bars: 2, color: 'bg-accent-green', text: 'text-accent-green' },
  Med: { bars: 4, color: 'bg-accent-yellow', text: 'text-accent-yellow' },
  High: { bars: 6, color: 'bg-accent-red', text: 'text-accent-red' },
};

const TOOLTIPS = {
  'Ofr Ability': 'Assesses the company\'s capacity to raise capital through registered offerings based on shelf registration status and available capacity.\n\nLow — No active shelf or limited available capacity.\nMedium — Active shelf with moderate capacity remaining.\nHigh — Large shelf registration actively available for offerings.',
  'Ofr Freq.': 'Measures how frequently the company conducts capital market offerings.\n\nLow — Rare or no recent offerings detected.\nMedium — Occasional offerings in prior periods.\nHigh — Frequent or continuous offerings indicating persistent capital needs.',
  'Dilution': 'Estimates the potential dilution to existing shareholders based on shelf registrations, ATM programs, and warrant overhang.\n\nLow — Less than 10% potential dilution.\nMedium — 10–20% potential dilution.\nHigh — More than 20% potential dilution, significant risk to shareholders.',
  'Cash Need': 'Evaluates the company\'s operating cash flow and runway, estimating how long they can sustain operations without raising additional capital.\n\nLow — Positive operating cash flow or more than 24 months of runway.\nMedium — 6–24 months of runway before needing additional funds.\nHigh — Less than 6 months of runway, indicating an urgent need for capital.',
  'Overall Offering Risk': 'Composite risk assessment considering offering ability, frequency, dilution, and cash need to provide a holistic view of the company\'s offering-related risk profile.\n\nLow — All or most sub-risks rated Low.\nMedium — Mix of Low and Medium, no High ratings.\nHigh — One or more sub-risks rated High.',
  'Warrant Exercise Risk': 'Evaluates the risk of warrant exercises diluting existing shareholders, considering warrant count, exercise price relative to market price, and expiration timeline.\n\nLow — No warrants outstanding or deeply out-of-the-money.\nMedium — Warrants outstanding with moderate exercise risk.\nHigh — Significant warrant overhang with near-term exercise potential.',
};

const LEVEL_COLORS = {
  Low: 'text-accent-green',
  Medium: 'text-accent-yellow',
  Med: 'text-accent-yellow',
  High: 'text-accent-red',
};

function colorizeTip(text) {
  // Split on Low/Med/Medium/High word boundaries, keeping the separators
  const parts = text.split(/\b(Low|Med(?:ium)?|High)\b/g);
  return parts.map((part, i) => {
    const color = LEVEL_COLORS[part];
    return color ? (
      <span key={i} className={`font-semibold ${color}`}>{part}</span>
    ) : (
      part
    );
  });
}

function MiniBars({ level }) {
  const cfg = LEVELS[level] || LEVELS.Med;
  return (
    <div className="flex items-end gap-px h-3.5 mr-2">
      {[1, 2, 3, 4, 5, 6].map((i) => (
        <div
          key={i}
          className={`w-[3px] rounded-sm ${i <= cfg.bars ? cfg.color : 'bg-surface-border'}`}
          style={{ height: `${3 + i * 1.5}px` }}
        />
      ))}
    </div>
  );
}

function RiskRow({ label, level }) {
  const cfg = LEVELS[level] || LEVELS.Med;
  const tip = TOOLTIPS[label] || '';
  return (
    <div className="kpi-row group relative cursor-help">
      <span className="kpi-label min-w-0 truncate pr-2 border-b border-dotted border-transparent hover:border-gray-600">
        {label}
      </span>
      <div className="flex items-center shrink-0">
        <MiniBars level={level} />
        <span className={`text-xs font-semibold w-7 text-right ${cfg.text}`}>{level}</span>
      </div>
      {tip && (
        <div className="absolute right-full top-1/2 -translate-y-1/2 mr-2 z-50 w-72 p-3 rounded-lg bg-surface-card border border-surface-border shadow-2xl text-xs text-gray-300 leading-relaxed opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 pointer-events-none whitespace-pre-line">
          {colorizeTip(tip)}
        </div>
      )}
    </div>
  );
}

export default function RiskPanel({ risk, loading }) {
  const items = [
    { label: 'Ofr Ability', level: risk?.offering_ability || 'Med' },
    { label: 'Ofr Freq.', level: risk?.offering_frequency || 'Med' },
    { label: 'Dilution', level: risk?.dilution || 'Med' },
    { label: 'Cash Need', level: risk?.cash_need || 'Low' },
    { label: 'Overall Offering Risk', level: risk?.overall_offering_risk || 'Med' },
    { label: 'Warrant Exercise Risk', level: risk?.warrant_exercise || 'Low' },
  ];

  if (loading) {
    return (
      <div className="card kpi-card animate-pulse h-full">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="kpi-row">
            <div className="h-3 w-24 bg-surface-hover rounded" />
            <div className="h-3 w-16 bg-surface-hover rounded" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="card kpi-card h-full">
      {items.map((item) => (
        <RiskRow key={item.label} label={item.label} level={item.level} />
      ))}
    </div>
  );
}
