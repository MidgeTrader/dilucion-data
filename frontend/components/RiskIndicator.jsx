const LEVEL_CONFIG = {
  Low: { color: 'bg-accent-green', width: 'w-1/4', text: 'text-accent-green' },
  Med: { color: 'bg-accent-yellow', width: 'w-2/4', text: 'text-accent-yellow' },
  High: { color: 'bg-accent-red', width: 'w-full', text: 'text-accent-red' },
};

export default function RiskIndicator({ label, level = 'Med', description }) {
  const config = LEVEL_CONFIG[level] || LEVEL_CONFIG.Med;

  return (
    <div className="space-y-1.5">
      <div className="flex justify-between items-center">
        <span className="text-sm text-gray-300">{label}</span>
        <span className={`text-xs font-semibold ${config.text}`}>{level}</span>
      </div>
      <div className="h-2 bg-surface rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${config.color} ${config.width}`}
        />
      </div>
      {description && (
        <p className="text-xs text-gray-500">{description}</p>
      )}
    </div>
  );
}
