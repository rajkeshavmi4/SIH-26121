from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from ..db.base import Base
class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    active_well_id: Mapped[str] = mapped_column(ForeignKey("wells.id", ondelete="CASCADE"), index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    interval_start_m: Mapped[float] = mapped_column(Float, index=True)
    interval_end_m: Mapped[float] = mapped_column(Float, index=True)
    current_depth_m: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(32), index=True)
    dedupe_key: Mapped[str] = mapped_column(String(255), index=True)
    distance_to_interval_m: Mapped[float] = mapped_column(Float, default=0.0)
    severity: Mapped[str] = mapped_column(String(32), default="low")
    relevance_score: Mapped[float] = mapped_column(Float)
    evidence_event_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    offset_well_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    source_document_ids: Mapped[list[int]] = mapped_column(JSON, default=list)
    matching_factors: Mapped[list[str]] = mapped_column(JSON, default=list)
    data_completeness: Mapped[float] = mapped_column(Float, default=0.0)
    explanation: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
