from datetime import datetime, timezone
from typing import Any
from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db.base import Base
class WellEvent(Base):
    __tablename__ = "incidents"
    __table_args__ = (CheckConstraint("start_depth_m >= 0 AND end_depth_m >= start_depth_m", name="ck_event_valid_interval"), Index("ix_incidents_well_depth", "well_id", "start_depth_m", "end_depth_m"), Index("ix_incidents_event_type_severity", "event_type", "severity"))
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    external_id: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    well_id: Mapped[str] = mapped_column(ForeignKey("wells.id", ondelete="CASCADE"), index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    original_event_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    start_depth_m: Mapped[float] = mapped_column(Float, index=True)
    end_depth_m: Mapped[float] = mapped_column(Float, index=True)
    formation_name: Mapped[str] = mapped_column(String(128), index=True)
    severity: Mapped[str] = mapped_column(String(32), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_mitigation: Mapped[str] = mapped_column(Text, default="")
    source_document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    source_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    extraction_status: Mapped[str] = mapped_column(String(32), default="verified", index=True)
    data_origin: Mapped[str] = mapped_column(String(32), default="synthetic", index=True)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    well: Mapped[Any] = relationship("Well", back_populates="incidents")
    @property
    def top_depth_m(self) -> float: return self.start_depth_m
    @property
    def bottom_depth_m(self) -> float: return self.end_depth_m
    @property
    def formation(self) -> str: return self.formation_name
    @property
    def mitigation(self) -> str: return self.recorded_mitigation
    @property
    def source_document(self) -> str: return str(self.source_document_id or "uploaded-report")
    @property
    def source_type(self) -> str: return self.data_origin
Incident = WellEvent
