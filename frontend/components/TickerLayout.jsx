import Head from 'next/head';
import TopNav from './TopNav';
import TickerSidebar from './TickerSidebar';
import FloatingAskButton from './FloatingAskButton';
import RagChatModal from './RagChatModal';
import { DEMO_MODE } from '../lib/mockData';
import useTickerData from '../lib/useTickerData';
import { useState } from 'react';

export default function TickerLayout({ activeNav, title, children }) {
  const { tickerUpper, data, loading, error, profile } = useTickerData();
  const [chatOpen, setChatOpen] = useState(false);

  const pageTitle = title
    ? `${title} — ${tickerUpper || 'Ticker'}`
    : `${tickerUpper || 'Ticker'} — SEC Dilution Tracker`;

  return (
    <>
      <Head>
        <title>{pageTitle}</title>
      </Head>

      {DEMO_MODE && (
        <div className="bg-accent-yellow/10 border-b border-accent-yellow/20 px-4 py-1.5 text-center text-xs text-accent-yellow">
          Modo demo — inspirado en{' '}
          <a href="https://app.askedgar.io/ticker/SPHL" target="_blank" rel="noopener noreferrer" className="underline hover:text-white">
            AskEdgar
          </a>
        </div>
      )}

      <div className="flex flex-col h-screen overflow-hidden">
        <TopNav />

        <div className="flex flex-1 min-h-0">
          <TickerSidebar profile={profile} activeNav={activeNav} ticker={tickerUpper} />

          <main className="flex-1 overflow-y-auto bg-surface p-4">
            {error ? (
              <div className="flex items-center justify-center min-h-[60vh]">
                <div className="text-center max-w-md">
                  <p className="text-4xl mb-3">🔍</p>
                  <h2 className="text-lg font-semibold text-white mb-2">Ticker no encontrado</h2>
                  <p className="text-sm text-gray-500 leading-relaxed">
                    No pudimos cargar datos para <span className="font-mono text-accent-teal">{tickerUpper}</span>.
                    Puede que el ticker no exista o que todavía no se haya escaneado.
                  </p>
                  <p className="text-xs text-gray-600 mt-4">
                    Busca un ticker válido en el buscador o escanéalo desde el backend.
                  </p>
                </div>
              </div>
            ) : typeof children === 'function' ? (
              children({ data, loading, tickerUpper, profile })
            ) : (
              children
            )}
          </main>
        </div>
      </div>

      <FloatingAskButton ticker={tickerUpper} onClick={() => setChatOpen(true)} />
      <RagChatModal
        ticker={tickerUpper}
        isOpen={chatOpen}
        onClose={() => setChatOpen(false)}
        filingUrl={data?.filings?.[0]?.source_url}
      />
    </>
  );
}
