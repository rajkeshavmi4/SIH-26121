from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base
class Well(Base):
    __tablename__ = "wells"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, index=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    total_depth_m: Mapped[float] = mapped_column(Float)
    formation: Mapped[str] = mapped_column(String)
    trajectory: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="historical")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    demo_label: Mapped[str] = mapped_column(String, default="NWIS synthetic demo")
    incidents: Mapped[list["Incident"]] = relationship(back_populates="well", cascade="all, delete-orphan")
class Incident(Base):
    __tablename__ = "incidents"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    well_id: Mapped[str] = mapped_column(ForeignKey("wells.id"), index=True)
    event_type: Mapped[str] = mapped_column(String, index=True)
    top_depth_m: Mapped[float] = mapped_column(Float)
    bottom_depth_m: Mapped[float] = mapped_column(Float)
    formation: Mapped[str] = mapped_column(String, index=True)
    severity: Mapped[str] = mapped_column(String, index=True)
    mitigation: Mapped[str] = mapped_column(Text)
    source_document: Mapped[str] = mapped_column(String)
    source_page: Mapped[int] = mapped_column(Integer, default=1)
    source_type: Mapped[str] = mapped_column(String, default="synthetic")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    well: Mapped[Well] = relationship(back_populates="incidents")
class Scenario(Base):
    __tablename__ = "scenarios"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    active_well_id: Mapped[str] = mapped_column(ForeignKey("wells.id"))
    current_depth_m: Mapped[float] = mapped_column(Float)
    start_depth_m: Mapped[float] = mapped_column(Float)
    end_depth_m: Mapped[float] = mapped_column(Float)
    step_m: Mapped[float] = mapped_column(Float, default=100)
    running: Mapped[bool] = mapped_column(Boolean, default=False)
