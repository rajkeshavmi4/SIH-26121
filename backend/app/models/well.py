from datetime import datetime, timezone
from typing import Any
from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db.base import Base
class Well(Base):
    __tablename__ = "wells"
    __table_args__ = (CheckConstraint("total_depth_m >= 0", name="ck_well_total_depth_nonnegative"), Index("ix_wells_location", "latitude", "longitude"))
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    external_id: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    basin: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    total_depth_m: Mapped[float] = mapped_column(Float)
    well_type: Mapped[str] = mapped_column(String(64), default="historical")
    status: Mapped[str] = mapped_column(String(64), default="historical", index=True)
    data_origin: Mapped[str] = mapped_column(String(32), default="synthetic", index=True)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    formation: Mapped[str] = mapped_column(String(128), default="Unknown", index=True)
    trajectory: Mapped[str | None] = mapped_column(String(64), nullable=True)
    demo_label: Mapped[str] = mapped_column(String(128), default="NWIS synthetic demo")
    incidents: Mapped[list[Any]] = relationship("WellEvent", back_populates="well", cascade="all, delete-orphan")
    formations: Mapped[list[Any]] = relationship("Formation", back_populates="well", cascade="all, delete-orphan")
    telemetry: Mapped[list[Any]] = relationship("Telemetry", back_populates="well", cascade="all, delete-orphan")
    @property
    def data_origin_label(self) -> str:
        return self.data_origin
