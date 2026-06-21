import Link from 'next/link';
import { useRouter } from 'next/router';

const NAV = [
  { href: '/', id: 'overview', label: 'Overview', icon: '◈' },
  { href: '/filings', id: 'filings', label: 'Filings', icon: '📄' },
  { href: '/screener', id: 'screener', label: 'Screener', icon: '📊' },
  { href: '/halts', id: 'halts', label: 'Halts', icon: '⏸' },
  { href: '/monitor', id: 'monitor', label: 'Monitor', icon: '📡' },
  { href: '/#dilution', id: 'dilution', label: 'Dilution', icon: '🔥' },
];

export default function Sidebar({ activeNav = 'overview' }) {
  const router = useRouter();

  return (
    <aside className="w-56 shrink-0 border-r border-surface-border bg-surface-card flex flex-col">
      <div className="px-4 py-5 border-b border-surface-border">
        <h1 className="font-bold text-white text-lg">SEC Dilution</h1>
        <p className="text-xs text-gray-500">Tracker + RAG</p>
      </div>
      <nav className="flex-1 p-3 space-y-0.5">
        {NAV.map((item) => {
          const active = activeNav === item.id || router.pathname === item.href;
          return (
            <Link
              key={item.id}
              href={item.href}
              className={`nav-item ${active ? 'nav-item-active' : ''}`}
            >
              <span>{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="p-3 border-t border-surface-border text-xs text-gray-600">
        DeepSeek + ChromaDB
      </div>
    </aside>
  );
}
