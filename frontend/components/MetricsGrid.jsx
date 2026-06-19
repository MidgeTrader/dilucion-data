import MetricsCard from './MetricsCard';

export default function MetricsGrid({ profile, loading, error }) {
  return <MetricsCard profile={profile} loading={loading} error={error} />;
}
