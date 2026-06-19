import TickerLayout from '../../../components/TickerLayout';
import TickerFilingsView from '../../../components/ticker/TickerFilingsView';

export default function TickerFilingsPage() {
  return (
    <TickerLayout activeNav="filings" title="Filings">
      {({ data, loading, tickerUpper }) => (
        <TickerFilingsView data={data} loading={loading} tickerUpper={tickerUpper} />
      )}
    </TickerLayout>
  );
}
