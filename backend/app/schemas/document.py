from datetime import datetime
from typing import Literal
from pydantic import BaseModel
from .common import SchemaBase
class DocumentResponse(SchemaBase):
    id: int
    document_id: str
    filename: str
    document_type: str
    storage_path: str | None
    mime_type: str
    file_size_bytes: int
    extracted_text: str | None
    extraction_status: str
    extraction_confidence: float | None
    review_status: str
    provenance: str
    page_count: int | None
    data_origin: str
    is_synthetic: bool
    created_at: datetime
class DocumentExtractionResponse(DocumentResponse):
    candidates: list[dict]
class DocumentReviewUpdate(BaseModel):
    review_status: Literal["needs_review", "verified", "rejected"] | None = None
    extracted_text: str | None = None
