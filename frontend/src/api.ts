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
  source_type: string;
  is_synthetic: boolean;
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
export type TelemetryRecord = {
  id: string;
  well_id: string;
  timestamp: string;
  depth_m: number;
  wob: number;
  rpm: number;
  torque: number;
  spp: number;
  ecd: number;
  rop: number;
};
export type TelemetryTrend = {
  wob: 'up' | 'down' | 'stable';
  rpm: 'up' | 'down' | 'stable';
  torque: 'up' | 'down' | 'stable';
  spp: 'up' | 'down' | 'stable';
  ecd: 'up' | 'down' | 'stable';
  rop: 'up' | 'down' | 'stable';
};
export type Anomaly = {
  parameter: string;
  value: number;
  threshold: number;
  severity: string;
  timestamp: string;
};
export type WellListResponse = {
  items: Well[];
  total: number;
  page: number;
  page_size: number;
};
export type OffsetListResponse = {
  offsets: Well[];
  radius_km: number;
  target_depth_m: number;
};
export type RiskEvaluateRequest = {
  well_id: string;
  current_depth_m: number;
  lookahead_m?: number;
  formation?: string;
};
export type AlertResponse = Alert;
export type UploadResult = {
  filename: string;
  characters: number;
  candidates: Record<string, string | number>[];
};
const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, init);
  if (!res.ok) throw new Error((await res.text()) || 'API request failed');
  return res.json();
}
export const getScenarios = () => request<Scenario[]>('/api/scenarios');
export const getDashboard = (id: string, radiusKm = 50) =>
  request<Dashboard>(`/api/dashboard?scenario_id=${id}&radius_km=${radiusKm}`);
export const getIncidents = (params: string) =>
  request<Incident[]>(`/api/incidents${params}`);
export const getCorrelation = (id: string) =>
  request<CorrelationResult>(`/api/correlation?scenario_id=${id}`);
export const mutateSimulation = (action: string, id: string) =>
  request<Scenario>(`/api/simulation/${action}?scenario_id=${id}`, { method: 'POST' });
export async function uploadReport(file: File): Promise<UploadResult> {
  const form = new FormData();
  form.append('file', file);
  return request<UploadResult>('/api/documents/upload', { method: 'POST', body: form });
}
export const searchRecords = (q: string) =>
  request<{ results: Incident[] }>(`/api/search?q=${encodeURIComponent(q)}`);
export const getTelemetry = (wellId: string, limit = 20) =>
  request<TelemetryRecord[]>(`/api/telemetry/${wellId}?limit=${limit}`);
export const getTelemetryTrends = (wellId: string) =>
  request<TelemetryTrend>(`/api/telemetry/${wellId}/trends`);
export const getTelemetryAnomalies = (wellId: string) =>
  request<Anomaly[]>(`/api/telemetry/${wellId}/anomalies`);
export const getWells = (params?: { page?: number; page_size?: number; status?: string }) => {
  const qs = new URLSearchParams();
  if (params?.page != null) qs.set('page', String(params.page));
  if (params?.page_size != null) qs.set('page_size', String(params.page_size));
  if (params?.status) qs.set('status', params.status);
  return request<WellListResponse>(`/api/wells${qs.toString() ? `?${qs}` : ''}`);
};
export const getWellOffsets = (
  wellId: string,
  params: { radius_km: number; target_depth_m: string }
) => {
  const qs = new URLSearchParams({
    radius_km: String(params.radius_km),
    target_depth_m: params.target_depth_m,
  });
  return request<OffsetListResponse>(`/api/wells/${wellId}/offsets?${qs}`);
};
export const getWellCorrelation = (
  wellId: string,
  params: { current_depth_m: number; lookahead_m?: number }
) => {
  const qs = new URLSearchParams({ current_depth_m: String(params.current_depth_m) });
  if (params.lookahead_m != null) qs.set('lookahead_m', String(params.lookahead_m));
  return request<CorrelationResult>(`/api/wells/${wellId}/correlation?${qs}`);
};
export const evaluateRisk = (req: RiskEvaluateRequest) =>
  request<AlertResponse[]>('/api/risk/evaluate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
export const getAlerts = (wellId?: string, status?: string) => {
  const qs = new URLSearchParams();
  if (wellId) qs.set('well_id', wellId);
  if (status) qs.set('status', status);
  return request<AlertResponse[]>(`/api/alerts${qs.toString() ? `?${qs}` : ''}`);
};
