import { useQuery } from '@tanstack/react-query';
import { getTelemetry, getTelemetryAnomalies } from '../api';
import type { TelemetryRecord, Anomaly } from '../api';
type Props = {
  wellId: string;
};
const PARAMS: { key: keyof TelemetryRecord; label: string; unit: string; warnHigh?: number; warnLow?: number }[] = [
  { key: 'wob', label: 'WOB', unit: 'kN', warnHigh: 250 },
  { key: 'rpm', label: 'RPM', unit: 'rpm', warnHigh: 180, warnLow: 40 },
  { key: 'torque', label: 'Torque', unit: 'kNm', warnHigh: 30 },
  { key: 'spp', label: 'SPP', unit: 'bar', warnHigh: 350 },
  { key: 'ecd', label: 'ECD', unit: 'sg', warnHigh: 2.1, warnLow: 1.0 },
  { key: 'rop', label: 'ROP', unit: 'm/h' },
];
function trend(history: number[]): 'up' | 'down' | 'stable' {
  if (history.length < 3) return 'stable';
  const last = history.slice(-3);
  const delta = last[2] - last[0];
  const threshold = Math.abs(last[0]) * 0.05;
  if (delta > threshold) return 'up';
  if (delta < -threshold) return 'down';
  return 'stable';
}
function TrendArrow({ direction }: { direction: 'up' | 'down' | 'stable' }) {
  if (direction === 'up') return <span className="trend-arrow trend-up">↑</span>;
  if (direction === 'down') return <span className="trend-arrow trend-down">↓</span>;
  return <span className="trend-arrow trend-stable">→</span>;
}
function GaugeCard({
  label,
  unit,
  values,
  anomaly,
}: {
  label: string;
  unit: string;
  values: number[];
  anomaly: boolean;
}) {
  const current = values[values.length - 1] ?? 0;
  const t = trend(values);
  const max = Math.max(...values, 0.001);
  const min = Math.min(...values);
  const range = max - min || 1;
  return (
    <div className={`gauge-card${anomaly ? ' anomaly' : ''}`}>
      <div className="gauge-label">
        {label}
        <TrendArrow direction={t} />
      </div>
      <div className="gauge-value">
        {typeof current === 'number' ? current.toFixed(1) : '-'}
        <span className="gauge-unit"> {unit}</span>
      </div>
      <div className="sparkline">
        {values.slice(-12).map((v, i) => {
          const h = Math.max(4, ((v - min) / range) * 24);
          return <div key={i} className="spark-bar" style={{ height: h }} />;
        })}
      </div>
      {anomaly && (
        <div style={{ marginTop: 6, fontFamily: "'DM Mono', monospace", fontSize: 9, color: 'var(--red)', textTransform: 'uppercase', letterSpacing: '0.07em' }}>
          WARNING THRESHOLD
        </div>
      )}
    </div>
  );
}
function buildMockTelemetry(): TelemetryRecord[] {
  const records: TelemetryRecord[] = [];
  for (let i = 0; i < 20; i++) {
    records.push({
      id: `mock-${i}`,
      well_id: 'mock',
      timestamp: new Date(Date.now() - (20 - i) * 5000).toISOString(),
      depth_m: 2000 + i * 10,
      wob: 150 + Math.sin(i * 0.5) * 30 + Math.random() * 10,
      rpm: 90 + Math.cos(i * 0.4) * 15 + Math.random() * 5,
      torque: 18 + Math.sin(i * 0.3) * 4 + Math.random() * 2,
      spp: 280 + Math.cos(i * 0.6) * 20 + Math.random() * 8,
      ecd: 1.45 + Math.sin(i * 0.2) * 0.05 + Math.random() * 0.02,
      rop: 12 + Math.cos(i * 0.7) * 3 + Math.random() * 1,
    });
  }
  return records;
}
export default function TelemetryPanel({ wellId }: Props) {
  const { data: records } = useQuery({
    queryKey: ['telemetry', wellId],
    queryFn: () => getTelemetry(wellId, 20),
    retry: false,
    refetchInterval: 5000,
  });
  const { data: anomalies } = useQuery({
    queryKey: ['telemetry-anomalies', wellId],
    queryFn: () => getTelemetryAnomalies(wellId),
    retry: false,
    refetchInterval: 5000,
  });
  const rows = (records && records.length > 0) ? records : buildMockTelemetry();
  const anomalySet = new Set<string>(((anomalies ?? []) as Anomaly[]).map(a => a.parameter));
  function valuesFor(key: keyof TelemetryRecord): number[] {
    return rows.map(r => {
      const v = r[key];
      return typeof v === 'number' ? v : 0;
    });
  }
  return (
    <div className="panel full">
      <div className="panel-head">
        <div>
          <h3>Live Telemetry</h3>
          <p className="sub">Real-time drilling parameters · 5 s refresh</p>
        </div>
        {!records && (
          <span className="badge yellow">SIMULATED DATA</span>
        )}
      </div>
      <div className="telemetry-grid">
        {PARAMS.map(p => {
          const vals = valuesFor(p.key);
          const current = vals[vals.length - 1] ?? 0;
          const isAnomaly =
            anomalySet.has(p.key) ||
            (p.warnHigh != null && current > p.warnHigh) ||
            (p.warnLow != null && current < p.warnLow);
          return (
            <GaugeCard
              key={p.key}
              label={p.label}
              unit={p.unit}
              values={vals}
              anomaly={isAnomaly}
            />
          );
        })}
      </div>
    </div>
  );
}
