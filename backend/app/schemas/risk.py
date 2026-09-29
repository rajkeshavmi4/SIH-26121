from pydantic import BaseModel, Field
class RiskEvaluateRequest(BaseModel):
    active_well_id: str
    current_depth_m: float = Field(ge=0)
    relevant_offset_well_ids: list[str] = Field(default_factory=list)
    target_formation: str | None = None
    lookahead_m: float = Field(default=100.0, ge=0)
class SimulationRequest(BaseModel):
    scenario_id: str = "scenario-1"
class AlertResponse(BaseModel):
    id: int | None = None
    dedupe_key: str
    active_well_id: str
    event_type: str
    interval_start_m: float
    interval_end_m: float
    current_depth_m: float
    status: str
    distance_to_interval_m: float
    severity: str
    relevance_score: float
    evidence_event_ids: list[str]
    offset_well_ids: list[str]
    source_document_ids: list[int]
    matching_factors: list[str]
    data_completeness: float
    explanation: str
