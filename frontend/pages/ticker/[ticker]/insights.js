import TickerLayout from '../../../components/TickerLayout';
import TickerInsightsView from '../../../components/ticker/TickerInsightsView';

export default function TickerInsightsPage() {
  return (
    <TickerLayout activeNav="insights" title="Insights">
      {({ data, loading, tickerUpper }) => (
        <TickerInsightsView data={data} loading={loading} tickerUpper={tickerUpper} />
      )}
    </TickerLayout>
  );
}
