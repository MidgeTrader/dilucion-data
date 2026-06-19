import TickerLayout from '../../../components/TickerLayout';
import TickerNewsView from '../../../components/ticker/TickerNewsView';

export default function TickerNewsPage() {
  return (
    <TickerLayout activeNav="news" title="News">
      {({ data, loading, tickerUpper }) => (
        <TickerNewsView data={data} loading={loading} tickerUpper={tickerUpper} />
      )}
    </TickerLayout>
  );
}
