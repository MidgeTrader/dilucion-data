import Link from 'next/link';
import Sidebar from './Sidebar';
export default function Layout({ children, activeNav }) {
  return (
    <div className="flex min-h-screen flex-col">
      <div className="flex flex-1 min-h-0">
        <Sidebar activeNav={activeNav} />
        <div className="flex-1 flex flex-col min-w-0">{children}</div>
      </div>
    </div>
  );
}
