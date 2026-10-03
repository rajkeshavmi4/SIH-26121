from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

class Provenance(BaseModel):
    source_type: str
    is_synthetic: bool
    demo_label: str = "Namowell synthetic demo"

class WellOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    latitude: float
    longitude: float
    total_depth_m: float
    formation: str
    trajectory: Optional[str] = None
    status: str
    provenance: Provenance
    distance_km: Optional[float] = None
    relevance_score: Optional[float] = None
    score_factors: Dict[str, float] = Field(default_factory=dict)
    missing_fields: List[str] = Field(default_factory=list)

class IncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    well_id: str
    well_name: Optional[str] = None
    event_type: str
    top_depth_m: float
    bottom_depth_m: float
    formation: str
    severity: str
    mitigation: str
    source_document: str
    source_page: int
    bounding_box: Optional[str] = None
    snippet: Optional[str] = None
    confidence: float = 1.0
    source_type: str
    is_synthetic: bool
    approval_status: str = "APPROVED"

class CasingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    well_id: str
    outer_diameter_in: float
    inner_diameter_in: float
    shoe_tvd_m: float
    shoe_md_m: float
    weight_ppf: float
    grade: str
    collapse_psi: float
    burst_psi: float

class CementingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    well_id: str
    slurry_density_sg: float
    top_of_cement_m: float
    bottom_of_cement_m: float
    compressive_strength_psi: float
    displacement_bbl: float

class MudOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    well_id: str
    depth_m: float
    mud_type: str
    mud_weight_sg: float
    pv_cp: float
    yp_lb_100ft2: float
    gel_10s_lb: float
    gel_10m_lb: float
    ecd_sg: float
    ph: float
    filtrate_ml: float

class BHAOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    well_id: str
    top_depth_m: float
    bottom_depth_m: float
    bit_diameter_in: float
    bit_type: str
    mwd_lwd_tools: str
    motor_rss_flag: str
    max_wob_kda: float
    collar_od_in: float

class TrajectoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    well_id: str
    measured_depth_m: float
    inclination_deg: float
    azimuth_deg: float
    true_vertical_depth_m: float
    dogleg_severity_deg100ft: float
    northing_m: float
    easting_m: float

class FormationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    well_id: str
    formation_name: str
    top_tvd_m: float
    bottom_tvd_m: float
    top_md_m: float
    bottom_md_m: float
    lithology: str
    pore_pressure_sg: float
    frac_gradient_sg: float
    permeability_md: float
    porosity_pct: float
    ucs_psi: float

class AlertRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    dedup_key: str
    scenario_id: str
    well_id: str
    incident_id: str
    event_type: str
    status: str
    escalation_level: str
    distance_m: float
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class AlertOut(BaseModel):
    incident: IncidentOut
    status: str
    distance_to_interval_m: float
    relevance_factors: List[str]
    data_completeness: List[str]
    warning: str = "Historical hazard proximity only; not a validated failure probability."

class ScenarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    active_well_id: str
    current_depth_m: float
    start_depth_m: float
    end_depth_m: float
    step_m: float
    running: bool
    active_well_name: Optional[str] = None

class DashboardOut(BaseModel):
    scenario: ScenarioOut
    active_well: WellOut
    offsets: List[WellOut]
    alerts: List[AlertOut]
    incident_count: int

class CorrelationBand(BaseModel):
    formation: str
    top_depth_m: float
    bottom_depth_m: float
    top_tvd_m: Optional[float] = None
    bottom_tvd_m: Optional[float] = None
    color: str

class CorrelationOut(BaseModel):
    scenario: ScenarioOut
    formations: List[CorrelationBand]
    incidents: List[IncidentOut]
    alerts: List[AlertOut]

class UploadOut(BaseModel):
    filename: str
    characters: int
    candidates: List[Dict[str, Any]]
    source_type: str = "uploaded"

class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    actor: str
    user_role: str
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: datetime

class ReviewItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    entity_type: str
    entity_id: str
    status: str
    reviewer_id: Optional[str] = None
    reviewer_notes: Optional[str] = None
    payload_json: str
    created_at: datetime

class ReviewActionInput(BaseModel):
    reviewer_id: str = "reviewer_1"
    notes: Optional[str] = None

class AlertAcknowledgeInput(BaseModel):
    user_id: str = "engineer_1"
    notes: Optional[str] = None

class ModelTrainInput(BaseModel):
    model_name: str = "hazard_classifier"
    epochs: int = 10
    features: List[str] = Field(default_factory=lambda: ["wob", "rpm", "torque", "rop_mhr", "ecd_sg", "spp_kpa", "mse_mj_m3"])

class ModelPredictInput(BaseModel):
    measured_depth_m: float
    wob: float
    rpm: float
    torque: float
    rop_mhr: float
    ecd_sg: float
    spp_kpa: float
    mse_mj_m3: float

class ModelPredictOut(BaseModel):
    predicted_hazard: str
    calibrated_probability: float
    hazard_probabilities: Dict[str, float]
    explainability: List[Dict[str, Any]]

class ReplayCourtInput(BaseModel):
    scenario_id: str = "scenario-1"
    step_size_m: float = 10.0
    lookahead_m: float = 300.0

class BenchmarkMetricOut(BaseModel):
    scenario_id: str
    total_steps: int
    precision: float
    recall: float
    f1_score: float
    lead_time_m: float
    lead_time_min: float
    latency_ms_per_record: float
    total_samples: int
    true_positives: int
    false_positives: int
    false_negatives: int
    grade: str

class APIResponse(BaseModel):
    success: bool = True
    data: Any
    meta: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
