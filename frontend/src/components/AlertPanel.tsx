import { useState } from 'react';
import type { Alert } from '../api';
type Props = {
  alerts: Alert[];
};
const STATUS_CLASS: Record<string, string> = {
  in_zone: 'in-zone',
  upcoming: 'upcoming',
  passed: 'passed',
};
const STATUS_LABEL: Record<string, string> = {
  in_zone: 'IN ZONE',
  upcoming: 'UPCOMING',
  passed: 'PASSED',
};
function AlertItem({ alert }: { alert: Alert }) {
  const [expanded, setExpanded] = useState(false);
  const statusClass = STATUS_CLASS[alert.status] ?? 'upcoming';
  const inc = alert.incident;
  return (
    <div
      className={`alert-item ${statusClass}`}
      onClick={() => setExpanded(e => !e)}
    >
      <div className="alert-top">
        <div className="alert-event-type" style={{ color: statusClass === 'in-zone' ? 'var(--red)' : statusClass === 'passed' ? 'var(--muted)' : 'var(--orange)' }}>
          {inc.event_type.replace(/_/g, ' ')}
        </div>
        <span className={`badge ${statusClass}`}>{STATUS_LABEL[alert.status] ?? alert.status}</span>
      </div>
      <div className="alert-meta">
        {alert.distance_to_interval_m === 0
          ? 'Active depth is inside'
          : `${Math.round(alert.distance_to_interval_m)} m ahead of`}{' '}
        <strong style={{ color: 'var(--text)' }}>{inc.formation}</strong> interval{' '}
        {inc.top_depth_m}-{inc.bottom_depth_m} m
      </div>
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center', marginTop: 4 }}>
        <div className="alert-source">
          {inc.source_document} / p.{inc.source_page}
        </div>
        <span className={`badge ${inc.severity === 'critical' || inc.severity === 'high' ? 'high' : inc.severity === 'low' ? 'low' : ''}`}>
          {inc.severity}
        </span>
        {inc.is_synthetic && <span className="badge yellow">SYNTHETIC</span>}
      </div>
      {expanded && (
        <div className="alert-expanded">
          <p className="alert-mitigation">{inc.mitigation}</p>
          {alert.relevance_factors.length > 0 && (
            <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 6 }}>
              <strong style={{ color: 'var(--text)', display: 'block', marginBottom: 3 }}>Relevance factors:</strong>
              {alert.relevance_factors.map((f, i) => (
                <span key={i} style={{ display: 'block' }}>{f}</span>
              ))}
            </div>
          )}
          {alert.warning && (
            <div style={{ marginTop: 8, fontSize: 11, color: 'var(--yellow)', fontFamily: "'DM Mono', monospace" }}>
              {alert.warning}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
export default function AlertPanel({ alerts }: Props) {
  const inZone = alerts.filter(a => a.status === 'in_zone');
  const upcoming = alerts.filter(a => a.status === 'upcoming');
  const passed = alerts.filter(a => a.status === 'passed');
  const ordered = [...inZone, ...upcoming, ...passed];
  return (
    <div className="panel" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="panel-head">
        <div>
          <h3>Historical Hazard Alerts</h3>
          <p className="sub">Proximity-based · look-ahead 300 m</p>
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          {inZone.length > 0 && <span className="badge in-zone">{inZone.length} IN ZONE</span>}
          {upcoming.length > 0 && <span className="badge upcoming">{upcoming.length} UPCOMING</span>}
        </div>
      </div>
      <div className="alert-list" style={{ flex: 1, overflowY: 'auto' }}>
        {ordered.length === 0 ? (
          <div className="empty">No historical incidents within look-ahead window</div>
        ) : (
          ordered.map(a => <AlertItem key={a.incident.id} alert={a} />)
        )}
      </div>
    </div>
  );
}
