import { useState } from 'react';

export default function CompanyAbout({ profile }) {
  const [tab, setTab] = useState('company');

  if (!profile) {
    return <div className="card h-full min-h-[320px] animate-pulse bg-surface-muted" />;
  }

  const description = profile.description || 'No company description available.';

  return (
    <div className="card h-full flex flex-col min-h-[360px]">
      <div className="flex items-center gap-1 p-3 border-b border-surface-border">
        <button
          type="button"
          onClick={() => setTab('company')}
          className={`tab-btn ${tab === 'company' ? 'tab-btn-active' : 'tab-btn-inactive'}`}
        >
          Company
        </button>
        <button
          type="button"
          onClick={() => setTab('about')}
          className={`tab-btn ${tab === 'about' ? 'tab-btn-active' : 'tab-btn-inactive'}`}
        >
          About
        </button>
      </div>
      <div className="flex-1 p-4 overflow-y-auto">
        <p className="text-sm text-gray-400 leading-relaxed whitespace-pre-line">
          {tab === 'company' ? description : profile.about || description}
        </p>
      </div>
      <div className="p-3 border-t border-surface-border">
        <button type="button" className="text-xs text-gray-500 hover:text-white border border-surface-border rounded-md px-3 py-1.5">
          Description
        </button>
      </div>
    </div>
  );
}
