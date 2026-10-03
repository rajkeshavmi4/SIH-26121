import { useCallback, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { getDashboard, getScenarios, mutateSimulation } from './api';
import Header from './components/Header';
import Dashboard from './components/Dashboard';
import IncidentExplorer from './components/IncidentExplorer';
import EngineeringView from './components/EngineeringView';
import ReviewerAuditView from './components/ReviewerAuditView';
import BenchmarkMLView from './components/BenchmarkMLView';
import ReportIntake from './components/ReportIntake';
import './styles.css';

type Tab = 'dashboard' | 'incidents' | 'engineering' | 'reviews' | 'benchmark' | 'intake';

export default function App() {
  const [scenarioId, setScenarioId] = useState('scenario-1');
  const [tab, setTab] = useState<Tab>('dashboard');
  const [speed, setSpeed] = useState(1);
  const [radiusKm, setRadiusKm] = useState(50);
  const client = useQueryClient();

  const scenarios = useQuery({
    queryKey: ['scenarios'],
    queryFn: getScenarios,
  });

  const dashboard = useQuery({
    queryKey: ['dashboard', scenarioId, radiusKm],
    queryFn: () => getDashboard(scenarioId, radiusKm),
    refetchInterval: 6000,
  });

  const simulation = useMutation({
    mutationFn: (action: string) => mutateSimulation(action, scenarioId),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ['dashboard', scenarioId] });
      client.invalidateQueries({ queryKey: ['correlation', scenarioId] });
    },
  });

  const handleStep = useCallback(() => simulation.mutate('step'), [simulation]);
  const handleStart = useCallback(() => simulation.mutate('start'), [simulation]);
  const handlePause = useCallback(() => simulation.mutate('pause'), [simulation]);
  const handleReset = useCallback(() => simulation.mutate('reset'), [simulation]);

  const data = dashboard.data;

  return (
    <div className="app">
      <Header
        scenarios={scenarios.data ?? []}
        scenarioId={scenarioId}
        onScenario={id => { setScenarioId(id); }}
        activeTab={tab}
        onTab={t => setTab(t as Tab)}
      />
      <div className="shell" style={{ marginTop: 20 }}>
        {dashboard.isError && (
          <div className="error-msg" style={{ marginTop: 16 }}>
            Cannot reach Namowell AI backend. Start FastAPI server on port 8000.
          </div>
        )}
        {tab === 'dashboard' && (
          <Dashboard
            data={data}
            scenarioId={scenarioId}
            isLoading={dashboard.isLoading}
            onStep={handleStep}
            onStart={handleStart}
            onPause={handlePause}
            onReset={handleReset}
            speed={speed}
            onSpeedChange={setSpeed}
            isPending={simulation.isPending}
            radiusKm={radiusKm}
            onRadiusChange={setRadiusKm}
          />
        )}
        {tab === 'incidents' && <IncidentExplorer />}
        {tab === 'engineering' && (
          <EngineeringView wellId={data?.active_well.id || 'demo-well-01'} scenarioId={scenarioId} />
        )}
        {tab === 'reviews' && <ReviewerAuditView />}
        {tab === 'benchmark' && <BenchmarkMLView scenarioId={scenarioId} />}
        {tab === 'intake' && <ReportIntake />}
        <footer style={{ marginTop: 32, padding: '16px 0', borderTop: '1px solid #1e293b', fontSize: 12, color: '#64748b', textAlign: 'center' }}>
          NAMOWELL AI Subsurface Decision Support System Synthetic Demo
        </footer>
      </div>
    </div>
  );
}
