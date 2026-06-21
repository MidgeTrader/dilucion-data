import Link from 'next/link';
import { useRouter } from 'next/router';
import { useState, useEffect } from 'react';
import SearchBar from './SearchBar';
import { getLastTicker } from '../lib/lastTicker';

const PLATFORM = [
  { label: 'Home', href: '/' },
  { label: 'Screener', href: '/screener' },
];

export default function TopNav() {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  const onTicker = router.pathname?.startsWith('/ticker/') ?? false;

  useEffect(() => { setMounted(true); }, []);

  return (
    <header className="h-14 border-b border-surface-border bg-surface flex items-center px-4 gap-6 shrink-0">
      <div className="flex items-center gap-4 shrink-0">
        <Link href="/" className="flex items-center gap-1.5">
          <span className="w-7 h-7 rounded-md bg-accent-teal flex items-center justify-center text-xs font-bold text-black">DD</span>
          <span className="text-sm font-semibold text-white tracking-tight hidden sm:inline">Dilucion Data</span>
        </Link>
        <nav className="hidden sm:flex items-center gap-1">
          {PLATFORM.map((item) => (
            <Link
              key={item.label}
              href={item.href || '#'}
              className={`text-sm px-2.5 py-1 rounded-md transition-colors ${
                router.pathname === item.href
                  ? 'text-white bg-surface-hover'
                  : 'text-gray-500 hover:text-white hover:bg-surface-hover/50'
              }`}
            >
              {item.label}
            </Link>
          ))}
          {!onTicker && mounted && (
            <Link href={`/ticker/${getLastTicker()}`}
              className="text-sm px-2.5 py-1 rounded-md text-accent-teal hover:text-white hover:bg-surface-hover/50 transition-colors">
              Datos
            </Link>
          )}
        </nav>
      </div>

      <div className="flex-1 max-w-xl mx-auto">
        <SearchBar placeholder="Search ticker or company..." />
      </div>

      <div className="flex items-center gap-2 shrink-0">
        <div className="w-8 h-8 rounded-full bg-accent-teal/20 text-accent-teal flex items-center justify-center text-sm font-semibold">
          R
        </div>
      </div>
    </header>
  );
}
