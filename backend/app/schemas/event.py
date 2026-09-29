from datetime import datetime
from pydantic import Field, model_validator
from .common import PageMeta, SchemaBase
class EventResponse(SchemaBase):
    id: str
    external_id: str | None
    well_id: str
    event_type: str
    original_event_type: str | None
    start_depth_m: float
    end_depth_m: float
    formation_name: str
    severity: str
    description: str | None
    recorded_mitigation: str
    source_document_id: int | None
    source_page: int | None
    extraction_status: str
    data_origin: str
    is_synthetic: bool
    created_at: datetime
    @model_validator(mode="after")
    def validate_interval(self):
        if self.start_depth_m < 0 or self.end_depth_m < self.start_depth_m:
            raise ValueError("event depth interval must satisfy 0 <= start_depth_m <= end_depth_m")
        return self
class EventSearchResponse(SchemaBase):
    items: list[EventResponse]
    meta: PageMeta
