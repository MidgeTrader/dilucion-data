import TickerLayout from '../../../components/TickerLayout';
import TickerDilutionView from '../../../components/ticker/TickerDilutionView';

export default function TickerDilutionPage() {
  return (
    <TickerLayout activeNav="dilution" title="Dilution">
      {({ data, loading, tickerUpper }) => (
        <TickerDilutionView data={data} loading={loading} tickerUpper={tickerUpper} />
      )}
    </TickerLayout>
  );
}
