import { useRef, useEffect } from 'react';

export default function TradingViewWidget({ ticker }) {
  const containerRef = useRef(null);
  const widgetRef = useRef(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el || !ticker) return;

    const initWidget = (h) => {
      if (!containerRef.current) return;
      if (widgetRef.current) {
        try { widgetRef.current.resize(h); } catch {}
        return;
      }
      widgetRef.current = new TradingView.widget({
        container_id: 'tv_chart',
        symbol: ticker,
        interval: 'D',
        timezone: 'America/New_York',
        theme: 'dark',
        style: '1',
        locale: 'en',
        toolbar_bg: '#0f1119',
        enable_publishing: false,
        allow_symbol_change: false,
        hide_side_toolbar: true,
        hide_top_toolbar: true,
        withdateranges: true,
        show_volume: true,
        studies: [],
        width: '100%',
        height: h,
        backgroundColor: '#0f1119',
        gridColor: '#1e2235',
        disabled_features: [
          'header_symbol_search', 'symbol_search_hot_key',
          'header_undo_redo', 'header_screenshot', 'header_compare',
          'volume_force_overlay', 'use_localstorage_for_settings',
        ],
        enabled_features: [],
      });
    };

    const loadWidget = () => {
      const h = Math.max(el.clientHeight || 400, 300);
      initWidget(h);
    };

    // ResizeObserver to keep widget height in sync with container
    const ro = new ResizeObserver(() => {
      const h = Math.max(el.clientHeight || 400, 300);
      if (widgetRef.current) {
        try { widgetRef.current.resize(h); } catch {}
      }
    });
    ro.observe(el);

    if (!document.querySelector('script[src*="tv.js"]')) {
      const script = document.createElement('script');
      script.src = 'https://s3.tradingview.com/tv.js';
      script.async = true;
      script.onload = loadWidget;
      document.body.appendChild(script);
    } else if (window.TradingView) {
      loadWidget();
    }

    return () => {
      ro.disconnect();
      if (widgetRef.current) {
        try { widgetRef.current.remove(); } catch {}
        widgetRef.current = null;
      }
    };
  }, [ticker]);

  return <div id="tv_chart" ref={containerRef} style={{ width: '100%', height: '100%', minHeight: 300 }} />;
}
