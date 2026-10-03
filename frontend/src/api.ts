export type Scenario = {
  id: string;
  name: string;
  active_well_id: string;
  active_well_name?: string;
  current_depth_m: number;
  start_depth_m: number;
  end_depth_m: number;
  step_m: number;
  running: boolean;
};

export type Well = {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  total_depth_m: number;
  formation: string;
  trajectory?: string;
  status: string;
  provenance: { source_type: string; is_synthetic: boolean; demo_label: string };
  distance_km?: number;
  relevance_score?: number;
  score_factors: Record<string, number>;
  missing_fields: string[];
};

export type Incident = {
  id: string;
  well_id: string;
  well_name?: string;
  event_type: string;
  top_depth_m: number;
  bottom_depth_m: number;
  formation: string;
  severity: string;
  mitigation: string;
  source_document: string;
  source_page: number;
  bounding_box?: string;
  snippet?: string;
  confidence?: number;
  source_type: string;
  is_synthetic: boolean;
  approval_status?: string;
  description?: string;
};

export type Alert = {
  incident: Incident;
  status: string;
  distance_to_interval_m: number;
  relevance_factors: string[];
  data_completeness: string[];
  warning: string;
};

export type AlertRecord = {
  id: string;
  dedup_key: string;
  scenario_id: string;
  well_id: string;
  incident_id: string;
  event_type: string;
  status: string;
  escalation_level: string;
  distance_m: number;
  acknowledged_by?: string;
  acknowledged_at?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
};

export type Dashboard = {
  scenario: Scenario;
  active_well: Well;
  offsets: Well[];
  alerts: Alert[];
  incident_count: number;
};

export type Formation = {
  formation: string;
  top_depth_m: number;
  bottom_depth_m: number;
  color: string;
};

export type CorrelationResult = {
  scenario: Scenario;
  formations: Formation[];
  incidents: Incident[];
  alerts: Alert[];
};

export type EngineeringData = {
  well_id: string;
  casings: Array<{ id: number; outer_diameter_in: number; shoe_tvd_m: number; weight_ppf: number; grade: string; collapse_psi: number; burst_psi: number }>;
  cementings: Array<{ id: number; slurry_density_sg: number; top_of_cement_m: number; bottom_of_cement_m: number; compressive_strength_psi: number }>;
  muds: Array<{ id: number; depth_m: number; mud_type: string; mud_weight_sg: number; pv_cp: number; yp_lb_100ft2: number; ecd_sg: number }>;
  bhas: Array<{ id: number; top_depth_m: number; bottom_depth_m: number; bit_diameter_in: number; bit_type: string; mwd_lwd_tools: string; motor_rss_flag: string }>;
  trajectories: Array<{ id: number; measured_depth_m: number; inclination_deg: number; azimuth_deg: number; true_vertical_depth_m: number; dogleg_severity_deg100ft: number }>;
  formations: Array<{ id: number; formation_name: string; top_tvd_m: number; bottom_tvd_m: number; lithology: string; pore_pressure_sg: number; frac_gradient_sg: number }>;
};

export type ReviewItem = {
  id: string;
  entity_type: string;
  entity_id: string;
  status: string;
  reviewer_id?: string;
  reviewer_notes?: string;
  payload_json: string;
  created_at: string;
};

export type AuditLog = {
  id: number;
  actor: string;
  user_role: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  details?: string;
  ip_address?: string;
  timestamp: string;
};

export type BenchmarkMetrics = {
  scenario_id: string;
  total_steps: number;
  precision: number;
  recall: number;
  f1_score: number;
  lead_time_m: number;
  lead_time_min: number;
  latency_ms_per_record: number;
  total_samples: number;
  true_positives: number;
  false_positives: number;
  false_negatives: number;
  grade: string;
};

export type ModelPredictOut = {
  predicted_hazard: string;
  calibrated_probability: number;
  hazard_probabilities: Record<string, number>;
  explainability: Array<{ feature: string; value: number; baseline: number; contribution: number }>;
};

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, init);
  if (!res.ok) throw new Error((await res.text()) || 'API request failed');
  return res.json();
}

export const getScenarios = () => request<Scenario[]>('/api/scenarios');
export const getDashboard = (id: string, radiusKm = 50) => request<Dashboard>(`/api/dashboard?scenario_id=${id}&radius_km=${radiusKm}`);
export const getIncidents = (params: string) => request<Incident[]>(`/api/incidents${params}`);
export const getCorrelation = (id: string) => request<CorrelationResult>(`/api/correlation?scenario_id=${id}`);
export const mutateSimulation = (action: string, id: string) => request<Scenario>(`/api/simulation/${action}?scenario_id=${id}`, { method: 'POST' });

export const getEngineeringData = (wellId: string) => request<EngineeringData>(`/api/v1/engineering/${wellId}`);
export const getTVDCorrelation = (scenarioId = 'scenario-1') => request<any>(`/api/v1/correlation/tvd-aware?scenario_id=${scenarioId}`);
export const getAlertRecords = (scenarioId = 'scenario-1') => request<AlertRecord[]>(`/api/v1/alerts?scenario_id=${scenarioId}`);
export const acknowledgeAlert = (alertId: string, notes?: string) => request<AlertRecord>(`/api/v1/alerts/${alertId}/acknowledge`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ user_id: 'engineer_1', notes }) });

export const getPendingReviews = () => request<ReviewItem[]>('/api/v1/reviews/pending');
export const approveReview = (reviewId: string, notes?: string) => request<ReviewItem>(`/api/v1/reviews/${reviewId}/approve`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ reviewer_id: 'reviewer_1', notes }) });
export const rejectReview = (reviewId: string, notes?: string) => request<ReviewItem>(`/api/v1/reviews/${reviewId}/reject`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ reviewer_id: 'reviewer_1', notes }) });

export const getAuditTrail = () => request<AuditLog[]>('/api/v1/audit-trail');
export const processOCR = (filename: string, content: string) => request<any>(`/api/v1/documents/ocr-process?filename=${encodeURIComponent(filename)}&content=${encodeURIComponent(content)}`, { method: 'POST' });
export const trainMLModel = () => request<any>('/api/v1/models/train', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}) });
export const predictHazard = (data: any) => request<ModelPredictOut>('/api/v1/models/predict', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
export const runBenchmarkCourt = (scenarioId = 'scenario-1') => request<BenchmarkMetrics>('/api/v1/benchmark/run', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ scenario_id: scenarioId }) });
