import { useState, useRef, useEffect } from 'react';
import { DEMO_MODE } from '../lib/mockData';

const DEMO_ANSWERS = {
  dilution: `**Auditoría de dilución (demo) — ${'{ticker}'}\n\n• Shelf S-3 registrado: $25,000,000\n• Dilución estimada vs float: **32.5%** 🔴\n• ATM activo: Sí — sales agent registrado\n• Warrants: 1,200,000 autorizados @ $4.50 exercise\n• Pre-funded warrants detectados\n\n⚠️ Riesgo HIGH — capacidad de dilución significativa vs float de 4.2M shares.`,
  warrants: `**Warrant Scanner (demo):**\n\n1. Volumen autorizado: 1,200,000 warrants\n2. Exercise price: $4.50\n3. Anti-dilución: No Full Ratchet detectado\n4. Pre-funded: Sí — 400,000 unidades\n5. Expiración: 5 años desde issuance`,
  default: `Respuesta demo para {ticker}. En producción, DeepSeek analizará el filing SEC real con citas textuales.`,
};

const PROMPT_OPTIONS = [
  { value: 'dilution', label: 'Full Dilution Audit' },
  { value: 'warrants', label: 'Warrant Scanner' },
  { value: 'convertible', label: 'Convertible / Toxic Debt' },
  { value: 'atm', label: 'ATM Offering Audit' },
  { value: 'shelf', label: 'Shelf Registration' },
];

export default function RagChatModal({ ticker, isOpen, onClose, filingUrl }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [promptType, setPromptType] = useState('dilution');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      setMessages([]);
      setError(null);
    }
  }, [isOpen, ticker]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (question) => {
    if (!question.trim() || loading) return;
    setLoading(true);
    setError(null);
    const userMsg = { role: 'user', content: question };
    setMessages((prev) => [...prev, userMsg]);

    try {
      if (DEMO_MODE) {
        await new Promise((r) => setTimeout(r, 800));
        const key = promptType in DEMO_ANSWERS ? promptType : 'default';
        const answer = DEMO_ANSWERS[key].replace(/\{ticker\}/g, ticker || 'TICKER');
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: answer,
            citations: [{ content: 'Demo excerpt: "Aggregate offering price of up to $25,000,000..."' }],
          },
        ]);
        return;
      }
      const res = await fetch('/api/rag', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question,
          ticker,
          url: filingUrl || undefined,
          prompt_type: promptType,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'RAG request failed');
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.answer,
          citations: data.citations || [],
        },
      ]);
    } catch (err) {
      setError(err.message);
      setMessages((prev) => [
        ...prev,
        { role: 'error', content: err.message },
      ]);
    } finally {
      setLoading(false);
      setInput('');
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(input);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-2xl bg-surface-card border border-surface-border rounded-2xl shadow-2xl flex flex-col max-h-[85vh]">
        <div className="flex items-center justify-between px-5 py-4 border-b border-surface-border">
          <div>
            <h2 className="font-semibold text-white">Ask about {ticker}</h2>
            <p className="text-xs text-gray-500">DeepSeek RAG · SEC Filings</p>
          </div>
          <button onClick={onClose} className="btn-ghost text-xl leading-none">&times;</button>
        </div>

        <div className="px-5 py-3 border-b border-surface-border">
          <select
            value={promptType}
            onChange={(e) => setPromptType(e.target.value)}
            className="input-dark text-sm"
          >
            {PROMPT_OPTIONS.map((p) => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </select>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4 min-h-[300px]">
          {messages.length === 0 && (
            <div className="text-center text-gray-500 text-sm py-8">
              <p className="mb-2">Ask about warrants, dilution, ATM offerings...</p>
              <button
                onClick={() => sendMessage(PROMPT_OPTIONS.find(p => p.value === promptType)?.label || 'Analyze dilution risk')}
                className="btn-primary text-sm"
              >
                Run {PROMPT_OPTIONS.find(p => p.value === promptType)?.label}
              </button>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-[85%] rounded-xl px-4 py-3 text-sm ${
                  msg.role === 'user'
                    ? 'bg-accent text-white'
                    : msg.role === 'error'
                    ? 'bg-accent-red/10 text-accent-red border border-accent-red/30'
                    : 'bg-surface-hover text-gray-200'
                }`}
              >
                <p className="whitespace-pre-wrap">{msg.content}</p>
                {msg.citations?.length > 0 && (
                  <details className="mt-2">
                    <summary className="text-xs text-gray-400 cursor-pointer">
                      {msg.citations.length} citation(s)
                    </summary>
                    {msg.citations.map((c, j) => (
                      <p key={j} className="text-xs text-gray-500 mt-1 font-mono border-l-2 border-surface-border pl-2">
                        {c.content?.slice(0, 200)}...
                      </p>
                    ))}
                  </details>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex items-center gap-2 text-gray-400 text-sm">
              <div className="w-4 h-4 border-2 border-accent border-t-transparent rounded-full animate-spin" />
              Analyzing filing...
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {error && (
          <p className="px-5 text-accent-red text-xs">{error}</p>
        )}

        <form onSubmit={handleSubmit} className="px-5 py-4 border-t border-surface-border flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about this ticker..."
            className="input-dark flex-1"
            disabled={loading}
          />
          <button type="submit" disabled={loading || !input.trim()} className="btn-primary">
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
