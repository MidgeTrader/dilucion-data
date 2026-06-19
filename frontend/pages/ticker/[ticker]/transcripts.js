import TickerLayout from '../../../components/TickerLayout';
import TickerTranscriptsView from '../../../components/ticker/TickerTranscriptsView';

export default function TickerTranscriptsPage() {
  return (
    <TickerLayout activeNav="transcripts" title="Transcripts">
      {({ data, loading, tickerUpper }) => (
        <TickerTranscriptsView data={data} loading={loading} tickerUpper={tickerUpper} />
      )}
    </TickerLayout>
  );
}
