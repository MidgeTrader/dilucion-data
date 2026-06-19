import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { fetchTicker } from './mockData';
import { setLastTicker } from './lastTicker';

export default function useTickerData() {
  const router = useRouter();
  const tickerUpper = router.isReady && router.query.ticker
    ? String(router.query.ticker).toUpperCase()
    : undefined;

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!router.isReady) return;

    if (!tickerUpper) {
      setLoading(false);
      return;
    }

    setLastTicker(tickerUpper);

    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchTicker(tickerUpper)
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((e) => {
        if (!cancelled) setError(e.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [tickerUpper, router.isReady]);

  return { tickerUpper, data, loading, error, profile: data?.profile };
}
