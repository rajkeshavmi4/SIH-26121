import { useState } from 'react';
import type { Well } from '../api';
type Props = {
  offsets: Well[];
};
type SortKey = 'score' | 'distance';
export default function OffsetTable({ offsets }: Props) {
  const [expanded, setExpanded] = useState<string | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>('score');
  const [sortAsc, setSortAsc] = useState(false);
  const sorted = [...offsets].sort((a, b) => {
    const aVal = sortKey === 'score' ? (a.relevance_score ?? 0) : (a.distance_km ?? 0);
    const bVal = sortKey === 'score' ? (b.relevance_score ?? 0) : (b.distance_km ?? 0);
    return sortAsc ? aVal - bVal : bVal - aVal;
  });
  function handleSort(key: SortKey) {
    if (sortKey === key) {
      setSortAsc(a => !a);
    } else {
      setSortKey(key);
      setSortAsc(false);
    }
  }
  function sortIndicator(key: SortKey) {
    if (sortKey !== key) return ' ↕';
    return sortAsc ? ' ↑' : ' ↓';
  }
  const totalFactors = (factors: Record<string, number>) => {
    const vals = Object.values(factors);
    return vals.reduce((s, v) => s + v, 0);
  };
  return (
    <div className="panel full">
      <div className="panel-head">
        <div>
          <h3>Ranked Offset Wells</h3>
          <p className="sub">Explainable relevance score · missing fields disclosed</p>
        </div>
        <span className="provenance">SYNTHETIC / DEMO</span>
      </div>
      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Well</th>
              <th
                className={`sortable${sortKey === 'score' ? ' sorted' : ''}`}
                onClick={() => handleSort('score')}
              >
                Score{sortIndicator('score')}
              </th>
              <th
                className={`sortable${sortKey === 'distance' ? ' sorted' : ''}`}
                onClick={() => handleSort('distance')}
              >
                Distance{sortIndicator('distance')}
              </th>
              <th>Formation</th>
              <th>TD</th>
              <th>Completeness</th>
              <th>Formation Match</th>
            </tr>
          </thead>
          <tbody>
            {sorted.slice(0, 12).map(well => {
              const isOpen = expanded === well.id;
              const completeness = well.missing_fields.length === 0 ? 1 : Math.max(0.2, 1 - well.missing_fields.length * 0.15);
              const pct = Math.round(completeness * 100);
              return (
                <>
                  <tr
                    key={well.id}
                    className="expandable"
                    onClick={() => setExpanded(isOpen ? null : well.id)}
                    style={{ borderLeft: isOpen ? '2px solid var(--mint)' : undefined }}
                  >
                    <td>
                      <strong style={{ fontSize: 13 }}>{well.name.replace('NWIS Demo ', '')}</strong>
                      <br />
                      <span className="provenance">{well.id}</span>
                    </td>
                    <td>
                      <span className="score-val">{well.relevance_score ?? '-'}</span>
                    </td>
                    <td className="mono" style={{ fontSize: 12 }}>
                      {well.distance_km != null ? `${well.distance_km} km` : '-'}
                    </td>
                    <td style={{ fontSize: 12 }}>{well.formation}</td>
                    <td className="mono" style={{ fontSize: 12 }}>
                      {well.total_depth_m.toLocaleString()} m
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <div className="completeness-bar-wrap">
                          <div
                            className="completeness-bar-fill"
                            style={{
                              width: `${pct}%`,
                              background: pct > 80 ? 'var(--mint)' : pct > 50 ? 'var(--yellow)' : 'var(--red)',
                            }}
                          />
                        </div>
                        <span className="mono" style={{ fontSize: 10, color: 'var(--muted)' }}>
                          {pct}%
                        </span>
                      </div>
                    </td>
                    <td>
                      {well.missing_fields.length === 0 ? (
                        <span style={{ color: 'var(--mint)', fontSize: 13 }}>✓</span>
                      ) : (
                        <span style={{ color: 'var(--red)', fontSize: 13 }}>✗</span>
                      )}
                    </td>
                  </tr>
                  {isOpen && (
                    <tr key={`${well.id}-detail`} className="expanded">
                      <td colSpan={7}>
                        <div style={{ padding: '8px 4px' }}>
                          <div style={{ fontSize: 10, color: 'var(--muted)', fontFamily: "'DM Mono', monospace", textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>
                            Score Factor Breakdown
                          </div>
                          <div className="factor-bars">
                            {Object.entries(well.score_factors).map(([key, val]) => {
                              const max = totalFactors(well.score_factors);
                              const fillPct = max > 0 ? (val / max) * 100 : 0;
                              return (
                                <div className="factor-row" key={key}>
                                  <div className="factor-name">{key.replace(/_/g, ' ')}</div>
                                  <div className="factor-bar-wrap">
                                    <div className="factor-bar-fill" style={{ width: `${fillPct}%` }} />
                                  </div>
                                  <div className="factor-value">{val}</div>
                                </div>
                              );
                            })}
                          </div>
                          {well.missing_fields.length > 0 && (
                            <div style={{ marginTop: 8 }}>
                              <span style={{ fontSize: 10, color: 'var(--red)', fontFamily: "'DM Mono', monospace" }}>
                                MISSING: {well.missing_fields.join(', ')}
                              </span>
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
