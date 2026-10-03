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
  { id: 'engineering', label: 'Subsurface & TVD' },
  { id: 'reviews', label: 'Reviewer & Audit' },
  { id: 'benchmark', label: 'ML & Replay Court' },
  { id: 'intake', label: 'Report OCR Intake' }
];

export default function Header({ scenarios, scenarioId, onScenario, activeTab, onTab }: Props) {
  return (
    <header style={{ position: 'sticky', top: 0, zIndex: 100, background: 'rgba(10,20,16,0.97)', backdropFilter: 'blur(8px)', borderBottom: '1px solid var(--line)' }}>
      <div className="shell" style={{ padding: '0 28px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', height: 60 }}>
          <div className="brand" style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{ fontSize: 20, fontWeight: 700, color: '#38bdf8', tracking: '0.05em' }}>NAMOWELL AI</span>
            <span style={{ fontSize: 11, background: '#1e293b', color: '#94a3b8', padding: '2px 8px', borderRadius: 4 }}>Subsurface Intelligence</span>
          </div>
          <div className="top-actions" style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            <div className="sys-status" style={{ fontSize: 11, color: '#4ade80' }}>
              ONLINE DEMO
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
        <nav style={{ display: 'flex', gap: 4, paddingBottom: '4px' }}>
          {TABS.map(t => (
            <button
              key={t.id}
              className={`tab${activeTab === t.id ? ' active' : ''}`}
              onClick={() => onTab(t.id)}
              style={{ padding: '6px 14px', fontSize: 13, background: activeTab === t.id ? '#1e293b' : 'transparent', color: activeTab === t.id ? '#38bdf8' : '#94a3b8', border: '1px solid', borderColor: activeTab === t.id ? '#38bdf8' : 'transparent', borderRadius: 4, cursor: 'pointer' }}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </div>
    </header>
  );
}
