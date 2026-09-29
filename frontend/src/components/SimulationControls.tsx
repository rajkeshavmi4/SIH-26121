import { useEffect, useRef } from 'react';
import type { Scenario } from '../api';
type Props = {
  scenario: Scenario | null | undefined;
  scenarioId: string;
  onStep: () => void;
  onStart: () => void;
  onPause: () => void;
  onReset: () => void;
  speed: number;
  onSpeedChange: (s: number) => void;
  isPending: boolean;
};
export default function SimulationControls({
  scenario,
  scenarioId,
  onStep,
  onStart,
  onPause,
  onReset,
  speed,
  onSpeedChange,
  isPending,
}: Props) {
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  useEffect(() => {
    if (scenario?.running) {
      const ms = Math.round(2000 / speed);
      intervalRef.current = setInterval(onStep, ms);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [scenario?.running, speed, onStep]);
  const current = scenario?.current_depth_m ?? 0;
  const start = scenario?.start_depth_m ?? 0;
  const end = scenario?.end_depth_m ?? 1;
  const progressPct = Math.min(100, ((current - start) / (end - start)) * 100);
  const stepM = scenario?.step_m ?? 100;
  return (
    <div className="sim-panel">
      <div>
        <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 9, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 4 }}>
          Active Depth
        </div>
        <div className="sim-depth">
          {current.toLocaleString()}
          <small> m MD</small>
        </div>
      </div>
      <div className="sim-progress-wrap">
        <div className="sim-progress-label">
          <span>{start.toLocaleString()} m</span>
          <span>{Math.round(progressPct)}%</span>
          <span>{end.toLocaleString()} m</span>
        </div>
        <div className="sim-progress-track">
          <div className="sim-progress-fill" style={{ width: `${progressPct}%` }} />
        </div>
        <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 9, color: 'var(--muted)', marginTop: 4 }}>
          SCENARIO: {scenarioId.toUpperCase()} · STEP {stepM} M
        </div>
      </div>
      <div className="sim-controls">
        <button
          className="btn primary"
          onClick={onStep}
          disabled={isPending}
        >
          +{stepM} m
        </button>
        {scenario?.running ? (
          <button className="btn danger" onClick={onPause} disabled={isPending}>
            Pause
          </button>
        ) : (
          <button className="btn" onClick={onStart} disabled={isPending}>
            Start Auto
          </button>
        )}
        <button className="btn" onClick={onReset} disabled={isPending}>
          Reset
        </button>
        <select
          className="select speed-select"
          value={speed}
          onChange={e => onSpeedChange(Number(e.target.value))}
          aria-label="Simulation speed"
        >
          <option value={1}>1x</option>
          <option value={2}>2x</option>
          <option value={5}>5x</option>
        </select>
        {scenario?.running && (
          <div className="sys-status">
            <span className="status-dot" />
            RUNNING
          </div>
        )}
      </div>
    </div>
  );
}
