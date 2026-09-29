import { useQuery } from '@tanstack/react-query';
import { getCorrelation } from '../api';
import type { Formation, Incident, Alert } from '../api';
type Props = {
  scenarioId: string;
};
const TICK_INTERVAL = 500;
function formatDepth(d: number): string {
  return d >= 1000 ? `${(d / 1000).toFixed(1)}k` : String(d);
}
function DepthAxis({ maxDepth, height }: { maxDepth: number; height: number }) {
  const ticks: number[] = [];
  for (let d = 0; d <= maxDepth; d += TICK_INTERVAL) {
    ticks.push(d);
  }
  return (
    <div className="depth-axis" style={{ height }}>
      {ticks.map(d => {
        const pct = (d / maxDepth) * 100;
        return (
          <div key={d} className="depth-tick" style={{ top: `${pct}%` }}>
            <span className="depth-tick-label" style={{ right: 8, position: 'absolute', transform: 'translateY(-50%)' }}>
              {formatDepth(d)}
            </span>
            <div className="depth-tick-line" />
          </div>
        );
      })}
    </div>
  );
}
function FormationBand({ band, maxDepth }: { band: Formation; maxDepth: number }) {
  const topPct = (band.top_depth_m / maxDepth) * 100;
  const heightPct = ((band.bottom_depth_m - band.top_depth_m) / maxDepth) * 100;
  return (
    <>
      <div
        className="formation-band"
        style={{
          top: `${topPct}%`,
          height: `${heightPct}%`,
          background: band.color,
        }}
      />
      <div
        className="formation-label"
        style={{ top: `${topPct + heightPct / 2}%`, transform: 'translateY(-50%)' }}
      >
        {band.formation}
      </div>
    </>
  );
}
function IncidentMarker({ incident, maxDepth }: { incident: Incident; maxDepth: number }) {
  const topPct = (incident.top_depth_m / maxDepth) * 100;
  const heightPct = Math.max(0.4, ((incident.bottom_depth_m - incident.top_depth_m) / maxDepth) * 100);
  const sevClass = `severity-${incident.severity}`;
  const labelColor =
    incident.severity === 'critical' || incident.severity === 'high'
      ? 'var(--red)'
      : incident.severity === 'medium'
      ? 'var(--yellow)'
      : 'var(--muted)';
  return (
    <>
      <div
        className={`incident-marker ${sevClass}`}
        style={{ top: `${topPct}%`, height: `${heightPct}%` }}
        title={`${incident.event_type} · ${incident.formation} · ${incident.top_depth_m}-${incident.bottom_depth_m} m`}
      />
      <div
        className="incident-right-label"
        style={{ top: `${topPct}%`, color: labelColor }}
      >
        {incident.event_type.replace(/_/g, ' ')}
      </div>
    </>
  );
}
export default function DepthCorrelation({ scenarioId }: Props) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['correlation', scenarioId],
    queryFn: () => getCorrelation(scenarioId),
    refetchInterval: 4000,
  });
  if (isLoading) {
    return (
      <div className="panel full">
        <div className="empty">Loading depth correlation...</div>
      </div>
    );
  }
  if (isError || !data) {
    return (
      <div className="panel full">
        <div className="empty" style={{ color: 'var(--red)' }}>Failed to load correlation data</div>
      </div>
    );
  }
  const maxDepth = data.scenario.end_depth_m;
  const currentDepth = data.scenario.current_depth_m;
  const lookahead = 300;
  const CHART_HEIGHT = 420;
  const currentPct = (currentDepth / maxDepth) * 100;
  const lookaheadPct = (lookahead / maxDepth) * 100;
  const ticks: number[] = [];
  for (let d = 0; d <= maxDepth; d += TICK_INTERVAL) {
    ticks.push(d);
  }
  const alertZoneIncidents = (data.alerts as Alert[]).filter(a =>
    a.status === 'in_zone' || a.status === 'upcoming'
  );
  return (
    <div className="panel full">
      <div className="panel-head">
        <div>
          <h3>Depth Correlation</h3>
          <p className="sub">
            Formation bands and historical incident intervals · measured depth in metres
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span className="badge mint">ACTIVE {currentDepth.toLocaleString()} m</span>
          <span className="badge upcoming">LOOKAHEAD {lookahead} m</span>
        </div>
      </div>
      <div className="depth-chart-wrap" style={{ height: CHART_HEIGHT }}>
        <DepthAxis maxDepth={maxDepth} height={CHART_HEIGHT} />
        <div className="depth-chart-inner" style={{ height: CHART_HEIGHT }}>
          {ticks.map(d => (
            <div
              key={d}
              className="depth-grid-line"
              style={{ top: `${(d / maxDepth) * 100}%` }}
            />
          ))}
          {data.formations.map(band => (
            <FormationBand key={band.formation} band={band} maxDepth={maxDepth} />
          ))}
          {data.incidents.slice(0, 12).map(inc => (
            <IncidentMarker key={inc.id} incident={inc} maxDepth={maxDepth} />
          ))}
          {alertZoneIncidents.map(alert => {
            const inc = alert.incident;
            const topPct = (inc.top_depth_m / maxDepth) * 100;
            const heightPct = Math.max(0.3, ((inc.bottom_depth_m - inc.top_depth_m) / maxDepth) * 100);
            return (
              <div
                key={`alert-zone-${inc.id}`}
                style={{
                  position: 'absolute',
                  left: 0,
                  right: 0,
                  top: `${topPct}%`,
                  height: `${heightPct}%`,
                  background: 'rgba(240,117,102,0.08)',
                  border: '1px solid rgba(240,117,102,0.3)',
                  zIndex: 6,
                  pointerEvents: 'none',
                }}
              />
            );
          })}
          <div
            className="lookahead-zone"
            style={{
              top: `${currentPct}%`,
              height: `${lookaheadPct}%`,
            }}
          >
            <span className="lookahead-label">LOOKAHEAD +{lookahead} m</span>
          </div>
          <div
            className="current-depth-line"
            style={{ top: `${currentPct}%` }}
          >
            <span className="current-depth-label">
              ACTIVE {currentDepth.toLocaleString()} m
            </span>
          </div>
        </div>
        <div style={{ width: 90, flexShrink: 0, position: 'relative', paddingLeft: 6 }}>
          {data.incidents.slice(0, 12).map(inc => {
            const topPct = (inc.top_depth_m / maxDepth) * 100;
            const labelColor =
              inc.severity === 'critical' || inc.severity === 'high'
                ? 'var(--red)'
                : inc.severity === 'medium'
                ? 'var(--yellow)'
                : 'var(--muted)';
            return (
              <div
                key={`rlabel-${inc.id}`}
                style={{
                  position: 'absolute',
                  top: `${topPct}%`,
                  transform: 'translateY(-50%)',
                  fontFamily: "'DM Mono', monospace",
                  fontSize: 9,
                  color: labelColor,
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  maxWidth: 85,
                  lineHeight: 1.3,
                }}
              >
                {inc.event_type.replace(/_/g, ' ')}
              </div>
            );
          })}
        </div>
      </div>
      <div style={{ display: 'flex', gap: 16, marginTop: 10, flexWrap: 'wrap' }}>
        {data.formations.map(band => (
          <div key={band.formation} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <div style={{ width: 10, height: 10, background: band.color, borderRadius: 2, opacity: 0.7 }} />
            <span style={{ fontSize: 10, color: 'var(--muted)', fontFamily: "'DM Mono', monospace" }}>
              {band.formation}
            </span>
          </div>
        ))}
        <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
          <div style={{ width: 10, height: 10, background: 'var(--red)', borderRadius: 2, opacity: 0.7 }} />
          <span style={{ fontSize: 10, color: 'var(--muted)', fontFamily: "'DM Mono', monospace" }}>
            Incident
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
          <div style={{ width: 20, height: 2, background: 'var(--mint)' }} />
          <span style={{ fontSize: 10, color: 'var(--muted)', fontFamily: "'DM Mono', monospace" }}>
            Active depth
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
          <div style={{ width: 20, height: 10, background: 'rgba(240,163,91,0.15)', border: '1px dashed rgba(240,163,91,0.4)' }} />
          <span style={{ fontSize: 10, color: 'var(--muted)', fontFamily: "'DM Mono', monospace" }}>
            Look-ahead zone
          </span>
        </div>
      </div>
    </div>
  );
}
