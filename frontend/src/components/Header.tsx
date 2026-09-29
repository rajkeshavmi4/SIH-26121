import type { Scenario } from '../api';

type Props = {
  scenarios: Scenario[];
  scenarioId: string;
  onScenario: (id: string) => void;
  activeTab: string;
  onTab: (tab: string) => void;
};

const TABS = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'incidents', label: 'Incident Explorer' },
  { id: 'telemetry', label: 'Telemetry' },
  { id: 'intake', label: 'Report Intake' },
];

export default function Header({ scenarios, scenarioId, onScenario, activeTab, onTab }: Props) {
  return (
    <header style={{ position: 'sticky', top: 0, zIndex: 100, background: 'rgba(10,20,16,0.97)', backdropFilter: 'blur(8px)', borderBottom: '1px solid var(--line)' }}>
      <div className="shell" style={{ padding: '0 28px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', height: 60 }}>
          <div className="brand" style={{ display: 'flex', alignItems: 'center' }}>
            <img src="/logo.png" alt="WellSage AI" style={{ height: 46, width: 'auto', objectFit: 'contain' }} />
          </div>
          <div className="top-actions">
            <div className="sys-status">
              <span className="status-dot" />
              LOCAL DEMO
            </div>
            <select
              className="select"
              value={scenarioId}
              onChange={e => onScenario(e.target.value)}
              aria-label="Active scenario"
              style={{ fontSize: 12 }}
            >
              {scenarios.map(s => (
                <option value={s.id} key={s.id}>{s.name}</option>
              ))}
            </select>
          </div>
        </div>
        <nav style={{ display: 'flex', gap: 2, paddingBottom: '0', borderBottom: 'none' }}>
          {TABS.map(t => (
            <button
              key={t.id}
              className={`tab${activeTab === t.id ? ' active' : ''}`}
              onClick={() => onTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </div>
    </header>
  );
}
