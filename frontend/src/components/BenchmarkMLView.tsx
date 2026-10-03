import { useState } from 'react';
import { trainMLModel, predictHazard, runBenchmarkCourt, type BenchmarkMetrics, type ModelPredictOut } from '../api';

type Props = {
  scenarioId: string;
};

export default function BenchmarkMLView({ scenarioId }: Props) {
  const [metrics, setMetrics] = useState<BenchmarkMetrics | null>(null);
  const [prediction, setPrediction] = useState<ModelPredictOut | null>(null);
  const [loadingBenchmark, setLoadingBenchmark] = useState(false);
  const [loadingModel, setLoadingModel] = useState(false);

  const [inputData, setInputData] = useState({
    measured_depth_m: 1850.0,
    wob: 14.5,
    rpm: 115.0,
    torque: 22.0,
    rop_mhr: 12.0,
    ecd_sg: 1.34,
    spp_kpa: 21000.0,
    mse_mj_m3: 850.0
  });

  const handleRunBenchmark = async () => {
    setLoadingBenchmark(true);
    try {
      const res = await runBenchmarkCourt(scenarioId);
      setMetrics(res);
    } catch (err) {
      alert('Benchmark evaluation failed');
    }
    setLoadingBenchmark(false);
  };

  const handleTrainAndPredict = async () => {
    setLoadingModel(true);
    try {
      await trainMLModel();
      const res = await predictHazard(inputData);
      setPrediction(res);
    } catch (err) {
      alert('Model training/prediction failed');
    }
    setLoadingModel(false);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div className="card" style={{ padding: 20, background: '#0f172a', borderRadius: 8, border: '1px solid #1e293b' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h3 style={{ margin: 0, color: '#38bdf8' }}>Replay Court Benchmark Evaluation Suite</h3>
          <button onClick={handleRunBenchmark} disabled={loadingBenchmark} style={{ padding: '8px 16px', background: '#0284c7', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer', fontWeight: 600, fontSize: 13 }}>
            {loadingBenchmark ? 'Executing Replay Court...' : 'Run Benchmark Evaluation'}
          </button>
        </div>

        {metrics ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
            <div style={{ padding: 16, background: '#1e293b', borderRadius: 6, textAlign: 'center' }}>
              <div style={{ fontSize: 12, color: '#94a3b8' }}>Precision / Recall</div>
              <div style={{ fontSize: 22, fontWeight: 700, color: '#4ade80', marginTop: 4 }}>{metrics.precision} / {metrics.recall}</div>
            </div>
            <div style={{ padding: 16, background: '#1e293b', borderRadius: 6, textAlign: 'center' }}>
              <div style={{ fontSize: 12, color: '#94a3b8' }}>F1 Score</div>
              <div style={{ fontSize: 22, fontWeight: 700, color: '#38bdf8', marginTop: 4 }}>{metrics.f1_score}</div>
            </div>
            <div style={{ padding: 16, background: '#1e293b', borderRadius: 6, textAlign: 'center' }}>
              <div style={{ fontSize: 12, color: '#94a3b8' }}>Avg Lead Time</div>
              <div style={{ fontSize: 22, fontWeight: 700, color: '#f59e0b', marginTop: 4 }}>{metrics.lead_time_m} m ({metrics.lead_time_min} min)</div>
            </div>
            <div style={{ padding: 16, background: '#1e293b', borderRadius: 6, textAlign: 'center' }}>
              <div style={{ fontSize: 12, color: '#94a3b8' }}>Latency / Grade</div>
              <div style={{ fontSize: 22, fontWeight: 700, color: '#e2e8f0', marginTop: 4 }}>{metrics.latency_ms_per_record} ms ({metrics.grade})</div>
            </div>
          </div>
        ) : (
          <div style={{ color: '#94a3b8', fontSize: 13 }}>Click 'Run Benchmark Evaluation' to replay historical incidents through the Namowell engine and evaluate precision, recall, lead time, and latency metrics.</div>
        )}
      </div>

      <div className="card" style={{ padding: 20, background: '#0f172a', borderRadius: 8, border: '1px solid #1e293b' }}>
        <h3 style={{ margin: '0 0 16px 0', color: '#38bdf8' }}>Machine Learning Pipeline & Hazard Prediction</h3>
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
          <div>
            <h4 style={{ margin: '0 0 12px 0', color: '#cbd5e1' }}>Telemetry Inputs</h4>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, fontSize: 12 }}>
              {Object.entries(inputData).map(([key, val]) => (
                <div key={key}>
                  <label style={{ display: 'block', color: '#94a3b8', marginBottom: 2 }}>{key}</label>
                  <input
                    type="number"
                    value={val}
                    onChange={e => setInputData({ ...inputData, [key]: parseFloat(e.target.value) || 0 })}
                    style={{ width: '100%', padding: '6px', background: '#1e293b', border: '1px solid #334155', color: '#fff', borderRadius: 4 }}
                  />
                </div>
              ))}
            </div>
            <button onClick={handleTrainAndPredict} disabled={loadingModel} style={{ marginTop: 16, padding: '8px 16px', background: '#16a34a', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer', fontWeight: 600, fontSize: 13, width: '100%' }}>
              {loadingModel ? 'Training & Evaluating...' : 'Train Baseline & Predict Hazard'}
            </button>
          </div>

          <div>
            <h4 style={{ margin: '0 0 12px 0', color: '#cbd5e1' }}>Calibrated Prediction & Feature Explainability</h4>
            {prediction ? (
              <div style={{ padding: 16, background: '#1e293b', borderRadius: 6 }}>
                <div style={{ fontSize: 16, fontWeight: 700, color: prediction.predicted_hazard === 'NORMAL' ? '#4ade80' : '#ef4444' }}>
                  Predicted Hazard: {prediction.predicted_hazard}
                </div>
                <div style={{ fontSize: 13, color: '#cbd5e1', marginTop: 4 }}>
                  Calibrated Probability: <strong>{(prediction.calibrated_probability * 100).toFixed(1)}%</strong>
                </div>

                <div style={{ marginTop: 16 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: '#38bdf8', marginBottom: 6 }}>Top Feature Drivers (SHAP-style):</div>
                  {prediction.explainability.map((item, idx) => (
                    <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, padding: '4px 0', borderBottom: '1px solid #334155' }}>
                      <span>{item.feature} (Val: {item.value})</span>
                      <span style={{ color: item.contribution > 0 ? '#ef4444' : '#4ade80' }}>
                        {item.contribution > 0 ? `+${item.contribution}` : item.contribution}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div style={{ color: '#94a3b8', fontSize: 13 }}>Train model or adjust inputs to evaluate hazard probabilities and feature contribution drivers.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
