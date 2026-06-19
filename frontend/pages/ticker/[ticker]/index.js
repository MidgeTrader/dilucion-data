import TickerLayout from '../../../components/TickerLayout';
import TickerOverviewView from '../../../components/ticker/TickerOverviewView';

export default function TickerOverviewPage() {
  return (
    <TickerLayout activeNav="overview">
      {({ data, loading, tickerUpper }) => (
        <TickerOverviewView data={data} loading={loading} tickerUpper={tickerUpper} />
      )}
    </TickerLayout>
  );
}
