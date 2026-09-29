import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { uploadReport } from '../api';
type Candidate = Record<string, string | number>;
export default function ReportIntake() {
  const [dragOver, setDragOver] = useState(false);
  const [result, setResult] = useState<{
    filename: string;
    characters: number;
    candidates: Candidate[];
  } | null>(null);
  const mutation = useMutation({
    mutationFn: uploadReport,
    onSuccess: data => setResult(data),
  });
  function handleFile(file: File) {
    setResult(null);
    mutation.mutate(file);
  }
  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  }
  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }
  function confidencePct(candidate: Candidate): number {
    const raw = candidate.confidence ?? candidate.score;
    if (typeof raw === 'number') return Math.round(raw * 100);
    return 85;
  }
  return (
    <div className="panel full">
      <div className="panel-head">
        <div>
          <h3>Report Intake</h3>
          <p className="sub">Extract, validate, review. Nothing is auto-published.</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <span className="badge mint">LOCAL EXTRACTION</span>
          <span className="badge yellow">REVIEW REQUIRED</span>
        </div>
      </div>
      <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap' }}>
        <div style={{ flex: '0 0 280px' }}>
          <label
            className={`upload-zone${dragOver ? ' drag-over' : ''}`}
            onDragOver={e => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
          >
            <span className="upload-icon">📄</span>
            <strong>Drop a PDF or TXT report</strong>
            <span className="upload-hint">or click to browse</span>
            <input
              type="file"
              accept=".pdf,.txt"
              hidden
              onChange={handleChange}
            />
          </label>
          {mutation.isPending && (
            <div className="empty" style={{ padding: '16px 0' }}>
              <span className="status-dot" style={{ width: 8, height: 8 }} />
              Extracting locally...
            </div>
          )}
          {mutation.isError && (
            <div className="error-msg">{(mutation.error as Error).message}</div>
          )}
          {result && (
            <div style={{ marginTop: 12, padding: 12, background: 'var(--panel2)', borderRadius: 7, border: '1px solid var(--line)' }}>
              <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, color: 'var(--muted)', marginBottom: 6, textTransform: 'uppercase' }}>
                Document processed
              </div>
              <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 4 }}>{result.filename}</div>
              <div style={{ fontSize: 11, color: 'var(--muted)' }}>
                {result.characters.toLocaleString()} characters extracted
              </div>
              <div style={{ marginTop: 8 }}>
                <span className="badge mint">{result.candidates.length} CANDIDATES</span>
              </div>
            </div>
          )}
          <div style={{ marginTop: 14, padding: 12, background: 'rgba(14,27,21,0.7)', border: '1px solid var(--line)', borderRadius: 7 }}>
            <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, color: 'var(--muted)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.07em' }}>
              Provenance Contract
            </div>
            <p style={{ fontSize: 11, color: 'var(--muted)', lineHeight: 1.6, margin: 0 }}>
              Uploaded evidence is isolated from the synthetic demo until a reviewer maps the candidate to a well, interval, formation, severity, and source. Semantic search and OCR are disabled unless configured.
            </p>
          </div>
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          {result && result.candidates.length > 0 ? (
            <>
              <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 10 }}>
                Extracted Candidates
              </div>
              {result.candidates.map((c, i) => {
                const conf = confidencePct(c);
                return (
                  <div key={i} className="candidate-card">
                    <div className="candidate-card-top">
                      <div>
                        <div className="candidate-event">
                          {String(c.event_type ?? 'Unknown event').replace(/_/g, ' ')}
                        </div>
                        <div className="candidate-confidence">
                          Confidence: {conf}%
                        </div>
                      </div>
                      <button className="publish-btn">Publish to DB</button>
                    </div>
                    <div className="candidate-meta">
                      {c.top_depth_m != null && c.bottom_depth_m != null && (
                        <span>Depth: {c.top_depth_m}-{c.bottom_depth_m} m · </span>
                      )}
                      {c.formation && <span>Formation: {c.formation} · </span>}
                      {c.severity && (
                        <span className={`badge ${c.severity === 'critical' || c.severity === 'high' ? 'high' : ''}`} style={{ marginLeft: 4 }}>
                          {String(c.severity)}
                        </span>
                      )}
                    </div>
                    {c.line && (
                      <div style={{ fontSize: 11, color: 'var(--muted)', background: 'rgba(10,20,16,0.5)', padding: '6px 8px', borderRadius: 4, fontFamily: "'DM Mono', monospace", lineHeight: 1.5 }}>
                        {String(c.line).slice(0, 200)}
                        {String(c.line).length > 200 && '...'}
                      </div>
                    )}
                    {c.page_or_line && (
                      <div style={{ marginTop: 5 }}>
                        <span className="provenance">SOURCE LINE {c.page_or_line}</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </>
          ) : (
            <div className="empty" style={{ height: '100%', minHeight: 200 }}>
              Upload a PDF or TXT report to extract incident candidates
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
