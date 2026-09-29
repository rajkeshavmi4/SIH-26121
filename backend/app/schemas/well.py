from datetime import datetime
from pydantic import Field, field_validator, model_validator
from .common import PageMeta, SchemaBase
class WellCreate(SchemaBase):
    external_id: str | None = None
    name: str = Field(min_length=1, max_length=255)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    basin: str | None = None
    total_depth_m: float = Field(ge=0)
    well_type: str = "historical"
    status: str = "historical"
    data_origin: str = "uploaded"
    is_synthetic: bool = False
class WellResponse(WellCreate):
    id: str
    created_at: datetime
    formation: str | None = None
    trajectory: str | None = None
class WellListResponse(SchemaBase):
    items: list[WellResponse]
    meta: PageMeta
class OffsetWellResponse(SchemaBase):
    well_id: str
    well_name: str
    relevance_score: float
    distance_km: float
    score_breakdown: dict[str, float]
    matching_formations: list[str]
    relevant_event_count: int
    data_completeness: float
    missing_fields: list[str]
    weight_total_used: float
    weights_validated: bool
    weight_note: str
class OffsetExclusion(SchemaBase):
    well_id: str
    reason: str
class OffsetWellListResponse(SchemaBase):
    items: list[OffsetWellResponse]
    excluded: list[OffsetExclusion]
    weights: dict[str, float]
    weight_note: str
