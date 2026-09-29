import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getIncidents, searchRecords } from '../api';
import type { Incident } from '../api';
const FORMATIONS = ['Barail', 'Tikak Parbat', 'Girujan', 'Lakshmi', 'Tipam', 'Narpuh', 'Sylhet', 'Jaintia'];
const EVENT_TYPES = ['lost_circulation', 'stuck_pipe', 'well_control', 'blowout', 'wellbore_instability', 'mud_losses', 'formation_damage'];
const SEV_CLASS: Record<string, string> = {
  critical: 'high',
  high: 'high',
  medium: 'yellow',
  low: 'low',
};
function IncidentRow({ incident }: { incident: Incident }) {
  const [open, setOpen] = useState(false);
  const sevClass = SEV_CLASS[incident.severity] ?? '';
  return (
    <>
      <tr className="expandable" onClick={() => setOpen(o => !o)}>
        <td>
          <strong style={{ fontSize: 12, textTransform: 'capitalize' }}>
            {incident.event_type.replace(/_/g, ' ')}
          </strong>
          <br />
          <span className="provenance">{incident.well_name || incident.well_id}</span>
        </td>
        <td className="mono" style={{ fontSize: 11 }}>
          {incident.top_depth_m}-{incident.bottom_depth_m} m
        </td>
        <td style={{ fontSize: 12 }}>{incident.formation}</td>
        <td>
          <span className={`badge ${sevClass}`}>{incident.severity}</span>
        </td>
        <td style={{ fontSize: 11, color: 'var(--muted)' }}>
          {incident.source_document}
          <br />
          <span className="provenance">p.{incident.source_page}</span>
        </td>
        <td>
          <span className={`badge ${incident.is_synthetic ? 'yellow' : 'mint'}`}>
            {incident.is_synthetic ? 'SYNTHETIC' : 'REAL'}
          </span>
        </td>
      </tr>
      {open && (
        <tr className="expanded">
          <td colSpan={6}>
            <div className="incident-detail">
              {incident.mitigation && (
                <p>
                  <strong>Mitigation:</strong> {incident.mitigation}
                </p>
              )}
              {incident.description && (
                <p>
                  <strong>Description:</strong> {incident.description}
                </p>
              )}
              <p>
                <strong>Source type:</strong>{' '}
                <span className="mono">{incident.source_type}</span>
                {' '}·{' '}
                <strong>Extraction:</strong>{' '}
                <span className="badge mint">VERIFIED</span>
              </p>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}
export default function IncidentExplorer() {
  const [severity, setSeverity] = useState('');
  const [formation, setFormation] = useState('');
  const [eventType, setEventType] = useState('');
  const [query, setQuery] = useState('');
  const params = new URLSearchParams();
  if (severity) params.set('severity', severity);
  if (formation) params.set('formation', formation);
  if (eventType) params.set('event_type', eventType);
  const incidentsQuery = useQuery({
    queryKey: ['incidents', severity, formation, eventType],
    queryFn: () => getIncidents(params.toString() ? `?${params}` : ''),
  });
  const searchQuery = useQuery({
    queryKey: ['search', query],
    queryFn: () => searchRecords(query),
    enabled: query.length > 1,
  });
  const rows: Incident[] =
    query.length > 1 ? (searchQuery.data?.results ?? []) : (incidentsQuery.data ?? []);
  const uniqueWells = new Set(rows.map(r => r.well_id)).size;
  const uniqueFormations = new Set(rows.map(r => r.formation)).size;
  return (
    <div className="panel full">
      <div className="explorer-header">
        <div>
          <h3>Historical Incident Explorer</h3>
          <p className="sub">Structured records and local report text search</p>
        </div>
        <div className="explorer-counts">
          <div className="count-chip">
            <strong>{rows.length}</strong> incidents
          </div>
          <div className="count-chip">
            <strong>{uniqueWells}</strong> wells
          </div>
          <div className="count-chip">
            <strong>{uniqueFormations}</strong> formations
          </div>
        </div>
      </div>
      <div className="filters">
        <input
          className="search"
          placeholder="Search event, formation, report text..."
          value={query}
          onChange={e => setQuery(e.target.value)}
        />
        <select className="select" value={eventType} onChange={e => setEventType(e.target.value)}>
          <option value="">All event types</option>
          {EVENT_TYPES.map(t => (
            <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>
          ))}
        </select>
        <select className="select" value={formation} onChange={e => setFormation(e.target.value)}>
          <option value="">All formations</option>
          {FORMATIONS.map(f => <option key={f}>{f}</option>)}
        </select>
        <select className="select" value={severity} onChange={e => setSeverity(e.target.value)}>
          <option value="">All severity</option>
          <option>critical</option>
          <option>high</option>
          <option>medium</option>
          <option>low</option>
        </select>
      </div>
      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Event / Well</th>
              <th>Interval</th>
              <th>Formation</th>
              <th>Severity</th>
              <th>Source</th>
              <th>Type</th>
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, 15).map(inc => (
              <IncidentRow key={inc.id} incident={inc} />
            ))}
          </tbody>
        </table>
        {rows.length === 0 && (
          <div className="empty">No incidents match the current filters</div>
        )}
      </div>
    </div>
  );
}
