import Link from 'next/link';
import Sidebar from './Sidebar';
import { DEMO_MODE } from '../lib/mockData';

export default function Layout({ children, activeNav }) {
  return (
    <div className="flex min-h-screen flex-col">
      {DEMO_MODE && (
        <div className="bg-accent-yellow/15 border-b border-accent-yellow/30 px-4 py-2 text-center text-xs text-accent-yellow">
          Modo demo — datos ficticios para preview visual.{' '}
          <Link href="/ticker/SPHL" className="underline hover:text-white">Ver SPHL →</Link>
        </div>
      )}
      <div className="flex flex-1 min-h-0">
        <Sidebar activeNav={activeNav} />
        <div className="flex-1 flex flex-col min-w-0">{children}</div>
      </div>
    </div>
  );
}
