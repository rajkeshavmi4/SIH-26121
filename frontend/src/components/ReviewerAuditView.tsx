import { useState, useEffect } from 'react';
import { getPendingReviews, approveReview, rejectReview, getAuditTrail, type ReviewItem, type AuditLog } from '../api';

export default function ReviewerAuditView() {
  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [notesMap, setNotesMap] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);

  const refreshData = () => {
    setLoading(true);
    Promise.all([
      getPendingReviews().catch(() => []),
      getAuditTrail().catch(() => [])
    ]).then(([revs, logs]) => {
      setReviews(revs);
      setAuditLogs(logs);
      setLoading(false);
    });
  };

  useEffect(() => {
    refreshData();
  }, []);

  const handleApprove = async (id: string) => {
    await approveReview(id, notesMap[id] || 'Approved by Reviewer');
    refreshData();
  };

  const handleReject = async (id: string) => {
    await rejectReview(id, notesMap[id] || 'Rejected by Reviewer');
    refreshData();
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div className="card" style={{ padding: 20, background: '#0f172a', borderRadius: 8, border: '1px solid #1e293b' }}>
        <h3 style={{ margin: '0 0 16px 0', color: '#38bdf8' }}>Reviewer Approval Workflow Queue</h3>
        {loading ? <div style={{ color: '#94a3b8' }}>Loading queue...</div> : reviews.length === 0 ? (
          <div style={{ color: '#4ade80', fontSize: 14 }}>No pending extraction or incident reviews in queue.</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {reviews.map(item => (
              <div key={item.id} style={{ padding: 16, background: '#1e293b', borderRadius: 6, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: '#f8fafc' }}>
                    [{item.entity_type}] ID: {item.entity_id}
                  </div>
                  <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 4 }}>
                    Payload: {item.payload_json}
                  </div>
                  <input
                    type="text"
                    placeholder="Add review notes..."
                    value={notesMap[item.id] || ''}
                    onChange={e => setNotesMap({ ...notesMap, [item.id]: e.target.value })}
                    style={{ marginTop: 8, padding: '4px 8px', background: '#0f172a', border: '1px solid #334155', color: '#fff', borderRadius: 4, width: 300, fontSize: 12 }}
                  />
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button onClick={() => handleApprove(item.id)} style={{ padding: '6px 14px', background: '#16a34a', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer', fontSize: 12, fontWeight: 600 }}>Approve</button>
                  <button onClick={() => handleReject(item.id)} style={{ padding: '6px 14px', background: '#dc2626', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer', fontSize: 12, fontWeight: 600 }}>Reject</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="card" style={{ padding: 20, background: '#0f172a', borderRadius: 8, border: '1px solid #1e293b' }}>
        <h3 style={{ margin: '0 0 16px 0', color: '#38bdf8' }}>Audit Trail Logs</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
          <thead>
            <tr style={{ background: '#1e293b', color: '#94a3b8', textAlign: 'left' }}>
              <th style={{ padding: 8 }}>Timestamp</th>
              <th style={{ padding: 8 }}>Actor</th>
              <th style={{ padding: 8 }}>Role</th>
              <th style={{ padding: 8 }}>Action</th>
              <th style={{ padding: 8 }}>Resource</th>
              <th style={{ padding: 8 }}>Details</th>
            </tr>
          </thead>
          <tbody>
            {auditLogs.map(log => (
              <tr key={log.id} style={{ borderBottom: '1px solid #1e293b', color: '#cbd5e1' }}>
                <td style={{ padding: 8 }}>{new Date(log.timestamp).toLocaleString()}</td>
                <td style={{ padding: 8, color: '#38bdf8' }}>{log.actor}</td>
                <td style={{ padding: 8 }}>{log.user_role}</td>
                <td style={{ padding: 8, fontWeight: 600 }}>{log.action}</td>
                <td style={{ padding: 8 }}>{log.resource_type}:{log.resource_id}</td>
                <td style={{ padding: 8, color: '#94a3b8' }}>{log.details || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
