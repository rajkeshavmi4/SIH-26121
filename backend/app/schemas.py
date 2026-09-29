from pydantic import BaseModel, ConfigDict, Field
class Provenance(BaseModel):
    source_type: str
    is_synthetic: bool
    demo_label: str = "NWIS synthetic demo"
class WellOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    latitude: float
    longitude: float
    total_depth_m: float
    formation: str
    trajectory: str | None
    status: str
    provenance: Provenance
    distance_km: float | None = None
    relevance_score: float | None = None
    score_factors: dict[str, float] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
class IncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    well_id: str
    well_name: str | None = None
    event_type: str
    top_depth_m: float
    bottom_depth_m: float
    formation: str
    severity: str
    mitigation: str
    source_document: str
    source_page: int
    source_type: str
    is_synthetic: bool
class AlertOut(BaseModel):
    incident: IncidentOut
    status: str
    distance_to_interval_m: float
    relevance_factors: list[str]
    data_completeness: list[str]
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
    active_well_name: str | None = None
class DashboardOut(BaseModel):
    scenario: ScenarioOut
    active_well: WellOut
    offsets: list[WellOut]
    alerts: list[AlertOut]
    incident_count: int
class CorrelationBand(BaseModel):
    formation: str
    top_depth_m: float
    bottom_depth_m: float
    color: str
class CorrelationOut(BaseModel):
    scenario: ScenarioOut
    formations: list[CorrelationBand]
    incidents: list[IncidentOut]
    alerts: list[AlertOut]
class UploadOut(BaseModel):
    filename: str
    characters: int
    candidates: list[dict[str, str | float | int]]
    source_type: str = "uploaded"
