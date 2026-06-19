import Sidebar from './Sidebar';

export default function Layout({ children, activeNav }) {
  return (
    <div className="flex min-h-screen">
      <Sidebar activeNav={activeNav} />
      <div className="flex-1 flex flex-col min-w-0">{children}</div>
    </div>
  );
}
