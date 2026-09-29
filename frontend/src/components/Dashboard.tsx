import type { Dashboard as DashboardData } from '../api';
import WellMap from './WellMap';
import AlertPanel from './AlertPanel';
import DepthCorrelation from './DepthCorrelation';
import OffsetTable from './OffsetTable';
import SimulationControls from './SimulationControls';
type Props = {
  data: DashboardData | undefined;
  scenarioId: string;
  isLoading: boolean;
  onStep: () => void;
  onStart: () => void;
  onPause: () => void;
  onReset: () => void;
  speed: number;
  onSpeedChange: (s: number) => void;
  isPending: boolean;
  radiusKm?: number;
  onRadiusChange?: (r: number) => void;
};
function MetricCard({
  label,
  value,
  unit,
  sub,
  accent,
}: {
  label: string;
  value: string | number;
  unit?: string;
  sub?: string;
  accent?: 'orange' | 'red' | 'mint';
}) {
  const color =
    accent === 'orange' ? 'var(--orange)' : accent === 'red' ? 'var(--red)' : 'var(--mint)';
  const cardClass =
    accent === 'orange' ? 'metric-card alert-card-metric' : accent === 'red' ? 'metric-card red-card' : 'metric-card';
  return (
    <div className={cardClass}>
      <div className="metric-label">{label}</div>
      <div className="metric-value" style={{ color }}>
        {value}
        {unit && <small> {unit}</small>}
      </div>
      {sub && <div className="metric-sub">{sub}</div>}
    </div>
  );
}
export default function Dashboard({
  data,
  scenarioId,
  isLoading,
  onStep,
  onStart,
  onPause,
  onReset,
  speed,
  onSpeedChange,
  isPending,
  radiusKm = 50,
  onRadiusChange,
}: Props) {
  if (isLoading) {
    return <div className="empty" style={{ marginTop: 40 }}>Loading NWIS scenario...</div>;
  }
  const inZoneCount = data?.alerts.filter(a => a.status === 'in_zone').length ?? 0;
  const upcomingCount = data?.alerts.filter(a => a.status === 'upcoming').length ?? 0;
  const totalAlerts = (data?.alerts.length ?? 0);
  const completeness = data
    ? Math.round(
        (data.offsets.filter(w => w.missing_fields.length === 0).length / Math.max(data.offsets.length, 1)) * 100
      )
    : 0;
  const alertAccent =
    inZoneCount > 0 ? 'red' : totalAlerts > 0 ? 'orange' : 'mint';
  return (
    <div style={{ marginTop: 16 }}>
      <SimulationControls
        scenario={data?.scenario}
        scenarioId={scenarioId}
        onStep={onStep}
        onStart={onStart}
        onPause={onPause}
        onReset={onReset}
        speed={speed}
        onSpeedChange={onSpeedChange}
        isPending={isPending}
      />
      {data && (
        <>
          <div className="metrics-row">
            <MetricCard
              label="Current Depth"
              value={data.scenario.current_depth_m.toLocaleString()}
              unit="m MD"
              sub={data.active_well.name}
            />
            <MetricCard
              label="Active Alerts"
              value={totalAlerts}
              unit="alerts"
              sub={`${inZoneCount} in zone · ${upcomingCount} upcoming`}
              accent={alertAccent}
            />
            <MetricCard
              label="Offset Wells"
              value={data.offsets.length}
              unit="wells"
              sub="ranked by relevance score"
            />
            <MetricCard
              label="Data Completeness"
              value={completeness}
              unit="%"
              sub={`${data.offsets.filter(w => w.missing_fields.length === 0).length} / ${data.offsets.length} complete records`}
              accent={completeness < 60 ? 'orange' : 'mint'}
            />
          </div>
          <div className="grid-main" style={{ marginBottom: 12 }}>
            <WellMap active={data.active_well} offsets={data.offsets} radiusKm={radiusKm} onRadiusChange={onRadiusChange} />
            <AlertPanel alerts={data.alerts} />
          </div>
          <div style={{ marginBottom: 12 }}>
            <DepthCorrelation scenarioId={scenarioId} />
          </div>
          <OffsetTable offsets={data.offsets} />
        </>
      )}
    </div>
  );
}
