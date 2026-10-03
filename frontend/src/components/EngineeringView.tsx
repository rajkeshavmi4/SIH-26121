import { useState, useEffect } from 'react';
import { getEngineeringData, getTVDCorrelation, type EngineeringData } from '../api';

type Props = {
  wellId: string;
  scenarioId: string;
};

export default function EngineeringView({ wellId, scenarioId }: Props) {
  const [data, setData] = useState<EngineeringData | null>(null);
  const [tvdCorrelation, setTvdCorrelation] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      getEngineeringData(wellId).catch(() => null),
      getTVDCorrelation(scenarioId).catch(() => null)
    ]).then(([eng, tvd]) => {
      setData(eng);
      setTvdCorrelation(tvd);
      setLoading(false);
    });
  }, [wellId, scenarioId]);

  if (loading) return <div style={{ padding: 24, color: '#94a3b8' }}>Loading subsurface engineering parameters...</div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div className="card" style={{ padding: 20, background: '#0f172a', borderRadius: 8, border: '1px solid #1e293b' }}>
        <h3 style={{ margin: '0 0 16px 0', color: '#38bdf8' }}>TVD & Stratigraphic Formation Correlation</h3>
        {tvdCorrelation ? (
          <div>
            <div style={{ display: 'flex', gap: 24, marginBottom: 16, fontSize: 14 }}>
              <div><strong>Active Well Depth (MD):</strong> {tvdCorrelation.active_md_m} m</div>
              <div><strong>Computed TVD:</strong> {tvdCorrelation.active_tvd_m} m</div>
              <div><strong>Formation:</strong> <span style={{ color: '#f59e0b' }}>{tvdCorrelation.active_formation}</span></div>
            </div>

            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ background: '#1e293b', color: '#94a3b8', textAlign: 'left' }}>
                  <th style={{ padding: 8 }}>Offset Well</th>
                  <th style={{ padding: 8 }}>Incident</th>
                  <th style={{ padding: 8 }}>Severity</th>
                  <th style={{ padding: 8 }}>Top/Bottom TVD (m)</th>
                  <th style={{ padding: 8 }}>TVD Delta (m)</th>
                  <th style={{ padding: 8 }}>Formation Match</th>
                </tr>
              </thead>
              <tbody>
                {tvdCorrelation.correlated_incidents?.map((item: any, idx: number) => (
                  <tr key={idx} style={{ borderBottom: '1px solid #1e293b', color: '#e2e8f0' }}>
                    <td style={{ padding: 8 }}>{item.well_name}</td>
                    <td style={{ padding: 8 }}>{item.event_type}</td>
                    <td style={{ padding: 8 }}><span style={{ color: item.severity === 'HIGH' || item.severity === 'critical' ? '#ef4444' : '#f59e0b' }}>{item.severity}</span></td>
                    <td style={{ padding: 8 }}>{item.offset_top_tvd} - {item.offset_bottom_tvd}</td>
                    <td style={{ padding: 8 }}>{item.tvd_delta_m} m</td>
                    <td style={{ padding: 8 }}>{item.formation_match ? <span style={{ color: '#4ade80' }}>MATCH ({item.active_formation})</span> : <span style={{ color: '#94a3b8' }}>MISMATCH</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : <div>No TVD correlation data available.</div>}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        <div className="card" style={{ padding: 20, background: '#0f172a', borderRadius: 8, border: '1px solid #1e293b' }}>
          <h4 style={{ margin: '0 0 12px 0', color: '#38bdf8' }}>Casing & Cementing Specifications</h4>
          {data?.casings?.map((c, i) => (
            <div key={i} style={{ marginBottom: 12, padding: 12, background: '#1e293b', borderRadius: 6, fontSize: 13 }}>
              <div><strong>Casing OD:</strong> {c.outer_diameter_in} in | <strong>Grade:</strong> {c.grade} | <strong>Weight:</strong> {c.weight_ppf} ppf</div>
              <div><strong>Shoe TVD:</strong> {c.shoe_tvd_m} m | <strong>Burst:</strong> {c.burst_psi} psi | <strong>Collapse:</strong> {c.collapse_psi} psi</div>
            </div>
          ))}
          {data?.cementings?.map((cm, i) => (
            <div key={i} style={{ padding: 12, background: '#1e293b', borderRadius: 6, fontSize: 13 }}>
              <div><strong>Slurry Density:</strong> {cm.slurry_density_sg} SG | <strong>TOC - BOC:</strong> {cm.top_of_cement_m}m - {cm.bottom_of_cement_m}m</div>
              <div><strong>Compressive Strength:</strong> {cm.compressive_strength_psi} psi</div>
            </div>
          ))}
        </div>

        <div className="card" style={{ padding: 20, background: '#0f172a', borderRadius: 8, border: '1px solid #1e293b' }}>
          <h4 style={{ margin: '0 0 12px 0', color: '#38bdf8' }}>Mud & BHA Assembly Parameters</h4>
          {data?.muds?.map((m, i) => (
            <div key={i} style={{ marginBottom: 12, padding: 12, background: '#1e293b', borderRadius: 6, fontSize: 13 }}>
              <div><strong>Mud Type:</strong> {m.mud_type} | <strong>Weight:</strong> {m.mud_weight_sg} SG | <strong>ECD:</strong> {m.ecd_sg} SG</div>
              <div><strong>PV/YP:</strong> {m.pv_cp} cP / {m.yp_lb_100ft2} lb/100ft²</div>
            </div>
          ))}
          {data?.bhas?.map((b, i) => (
            <div key={i} style={{ padding: 12, background: '#1e293b', borderRadius: 6, fontSize: 13 }}>
              <div><strong>Bit Diameter:</strong> {b.bit_diameter_in} in ({b.bit_type}) | <strong>Tools:</strong> {b.mwd_lwd_tools}</div>
              <div><strong>Steering:</strong> {b.motor_rss_flag} | <strong>Max WOB:</strong> {b.max_wob_kda} kda</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
