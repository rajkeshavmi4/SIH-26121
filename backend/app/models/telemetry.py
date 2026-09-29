from typing import Any
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db.base import Base
class Telemetry(Base):
    __tablename__ = "telemetry"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    well_id: Mapped[str] = mapped_column(ForeignKey("wells.id", ondelete="CASCADE"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    measured_depth_m: Mapped[float] = mapped_column(Float, index=True)
    wob: Mapped[float | None] = mapped_column(Float, nullable=True)
    rpm: Mapped[float | None] = mapped_column(Float, nullable=True)
    torque: Mapped[float | None] = mapped_column(Float, nullable=True)
    flow_rate_lpm: Mapped[float | None] = mapped_column(Float, nullable=True)
    standpipe_pressure_kpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    rop_mhr: Mapped[float | None] = mapped_column(Float, nullable=True)
    ecd_kgL: Mapped[float | None] = mapped_column(Float, nullable=True)
    mwd_inclination: Mapped[float | None] = mapped_column(Float, nullable=True)
    mwd_azimuth: Mapped[float | None] = mapped_column(Float, nullable=True)
    pressure: Mapped[float | None] = mapped_column(Float, nullable=True)
    mud_flow_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    data_origin: Mapped[str] = mapped_column(String(32), default="synthetic", index=True)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    well: Mapped[Any] = relationship("Well", back_populates="telemetry")
