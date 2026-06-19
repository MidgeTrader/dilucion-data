export default function TickerAvatar({ ticker, size = 'md' }) {
  const letters = (ticker || '?').slice(0, 2).toUpperCase();
  const sizes = {
    sm: 'w-8 h-8 text-xs',
    md: 'w-10 h-10 text-sm',
    lg: 'w-12 h-12 text-base',
  };

  return (
    <div
      className={`${sizes[size] || sizes.md} rounded-full bg-surface-hover border border-surface-border flex items-center justify-center font-mono font-bold text-accent-teal shrink-0`}
    >
      {letters}
    </div>
  );
}
