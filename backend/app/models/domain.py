from datetime import datetime
from typing import Optional, List
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym
from ..db import Base

class Well(Base):
    __tablename__ = "wells"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, index=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    total_depth_m: Mapped[float] = mapped_column(Float)
    formation: Mapped[str] = mapped_column(String, default="Barail")
    trajectory: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="historical")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    demo_label: Mapped[str] = mapped_column(String, default="Namowell synthetic demo")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    data_origin: Mapped[str] = mapped_column(String, default="synthetic")

    incidents: Mapped[List["Incident"]] = relationship(back_populates="well", cascade="all, delete-orphan")
    casings: Mapped[List["CasingData"]] = relationship(back_populates="well", cascade="all, delete-orphan")
    cementings: Mapped[List["CementingData"]] = relationship(back_populates="well", cascade="all, delete-orphan")
    muds: Mapped[List["MudData"]] = relationship(back_populates="well", cascade="all, delete-orphan")
    bhas: Mapped[List["BHAData"]] = relationship(back_populates="well", cascade="all, delete-orphan")
    trajectories: Mapped[List["TrajectoryData"]] = relationship(back_populates="well", cascade="all, delete-orphan")
    formation_data: Mapped[List["FormationData"]] = relationship(back_populates="well", cascade="all, delete-orphan")
    formations: Mapped[List["Formation"]] = relationship(back_populates="well", cascade="all, delete-orphan")
    telemetry: Mapped[List["Telemetry"]] = relationship(back_populates="well", cascade="all, delete-orphan")

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
    bounding_box: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    source_type: Mapped[str] = mapped_column(String, default="synthetic")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    approval_status: Mapped[str] = mapped_column(String, default="APPROVED")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    well: Mapped[Well] = relationship(back_populates="incidents")

    start_depth_m = synonym("top_depth_m")
    end_depth_m = synonym("bottom_depth_m")
    formation_name = synonym("formation")
    source_document_id = synonym("source_document")
    data_origin = synonym("source_type")

    @property
    def external_id(self) -> Optional[str]:
        return None

    @property
    def extraction_status(self) -> str:
        return "verified" if self.approval_status == "APPROVED" else "extracted"

    @property
    def description(self) -> str:
        return self.snippet or self.mitigation

    @property
    def recorded_mitigation(self) -> str:
        return self.mitigation

    @property
    def original_event_type(self) -> str:
        return self.event_type

WellEvent = Incident

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

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor: Mapped[str] = mapped_column(String, index=True)
    user_role: Mapped[str] = mapped_column(String)
    action: Mapped[str] = mapped_column(String, index=True)
    resource_type: Mapped[str] = mapped_column(String)
    resource_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class CasingData(Base):
    __tablename__ = "casing_data"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    well_id: Mapped[str] = mapped_column(ForeignKey("wells.id"), index=True)
    outer_diameter_in: Mapped[float] = mapped_column(Float)
    inner_diameter_in: Mapped[float] = mapped_column(Float)
    shoe_tvd_m: Mapped[float] = mapped_column(Float)
    shoe_md_m: Mapped[float] = mapped_column(Float)
    weight_ppf: Mapped[float] = mapped_column(Float)
    grade: Mapped[str] = mapped_column(String)
    collapse_psi: Mapped[float] = mapped_column(Float)
    burst_psi: Mapped[float] = mapped_column(Float)

    well: Mapped[Well] = relationship(back_populates="casings")

class CementingData(Base):
    __tablename__ = "cementing_data"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    well_id: Mapped[str] = mapped_column(ForeignKey("wells.id"), index=True)
    slurry_density_sg: Mapped[float] = mapped_column(Float)
    top_of_cement_m: Mapped[float] = mapped_column(Float)
    bottom_of_cement_m: Mapped[float] = mapped_column(Float)
    compressive_strength_psi: Mapped[float] = mapped_column(Float)
    displacement_bbl: Mapped[float] = mapped_column(Float)

    well: Mapped[Well] = relationship(back_populates="cementings")

class MudData(Base):
    __tablename__ = "mud_data"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    well_id: Mapped[str] = mapped_column(ForeignKey("wells.id"), index=True)
    depth_m: Mapped[float] = mapped_column(Float)
    mud_type: Mapped[str] = mapped_column(String)
    mud_weight_sg: Mapped[float] = mapped_column(Float)
    pv_cp: Mapped[float] = mapped_column(Float)
    yp_lb_100ft2: Mapped[float] = mapped_column(Float)
    gel_10s_lb: Mapped[float] = mapped_column(Float)
    gel_10m_lb: Mapped[float] = mapped_column(Float)
    ecd_sg: Mapped[float] = mapped_column(Float)
    ph: Mapped[float] = mapped_column(Float)
    filtrate_ml: Mapped[float] = mapped_column(Float)

    well: Mapped[Well] = relationship(back_populates="muds")

class BHAData(Base):
    __tablename__ = "bha_data"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    well_id: Mapped[str] = mapped_column(ForeignKey("wells.id"), index=True)
    top_depth_m: Mapped[float] = mapped_column(Float)
    bottom_depth_m: Mapped[float] = mapped_column(Float)
    bit_diameter_in: Mapped[float] = mapped_column(Float)
    bit_type: Mapped[str] = mapped_column(String)
    mwd_lwd_tools: Mapped[str] = mapped_column(String)
    motor_rss_flag: Mapped[str] = mapped_column(String)
    max_wob_kda: Mapped[float] = mapped_column(Float)
    collar_od_in: Mapped[float] = mapped_column(Float)

    well: Mapped[Well] = relationship(back_populates="bhas")

class TrajectoryData(Base):
    __tablename__ = "trajectory_data"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    well_id: Mapped[str] = mapped_column(ForeignKey("wells.id"), index=True)
    measured_depth_m: Mapped[float] = mapped_column(Float)
    inclination_deg: Mapped[float] = mapped_column(Float)
    azimuth_deg: Mapped[float] = mapped_column(Float)
    true_vertical_depth_m: Mapped[float] = mapped_column(Float)
    dogleg_severity_deg100ft: Mapped[float] = mapped_column(Float, default=0.0)
    northing_m: Mapped[float] = mapped_column(Float, default=0.0)
    easting_m: Mapped[float] = mapped_column(Float, default=0.0)

    well: Mapped[Well] = relationship(back_populates="trajectories")

class FormationData(Base):
    __tablename__ = "formation_data"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    well_id: Mapped[str] = mapped_column(ForeignKey("wells.id"), index=True)
    formation_name: Mapped[str] = mapped_column(String, index=True)
    top_tvd_m: Mapped[float] = mapped_column(Float)
    bottom_tvd_m: Mapped[float] = mapped_column(Float)
    top_md_m: Mapped[float] = mapped_column(Float)
    bottom_md_m: Mapped[float] = mapped_column(Float)
    lithology: Mapped[str] = mapped_column(String)
    pore_pressure_sg: Mapped[float] = mapped_column(Float)
    frac_gradient_sg: Mapped[float] = mapped_column(Float)
    permeability_md: Mapped[float] = mapped_column(Float)
    porosity_pct: Mapped[float] = mapped_column(Float)
    ucs_psi: Mapped[float] = mapped_column(Float)

    well: Mapped[Well] = relationship(back_populates="formation_data")

class AlertRecord(Base):
    __tablename__ = "alert_records"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    dedup_key: Mapped[str] = mapped_column(String, index=True)
    scenario_id: Mapped[str] = mapped_column(String)
    well_id: Mapped[str] = mapped_column(String)
    incident_id: Mapped[str] = mapped_column(String)
    event_type: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="NEW")
    escalation_level: Mapped[str] = mapped_column(String, default="INFO")
    distance_m: Mapped[float] = mapped_column(Float)
    acknowledged_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class ReviewItem(Base):
    __tablename__ = "review_items"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    entity_type: Mapped[str] = mapped_column(String, index=True)
    entity_id: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="PENDING_REVIEW")
    reviewer_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    reviewer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payload_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class ModelRegistry(Base):
    __tablename__ = "model_registry"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    model_name: Mapped[str] = mapped_column(String, index=True)
    version: Mapped[str] = mapped_column(String)
    metrics_json: Mapped[str] = mapped_column(Text)
    feature_names_json: Mapped[str] = mapped_column(Text)
    model_binary_b64: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, default="ACTIVE")
    trained_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    filename: Mapped[str] = mapped_column(String)
    document_type: Mapped[str] = mapped_column(String, default="report")
    storage_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    content_sha256: Mapped[str] = mapped_column(String)
    file_size_bytes: Mapped[int] = mapped_column(Integer)
    mime_type: Mapped[str] = mapped_column(String, default="text/plain")
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extraction_status: Mapped[str] = mapped_column(String, default="extracted")
    extraction_confidence: Mapped[float] = mapped_column(Float, default=1.0)
    review_status: Mapped[str] = mapped_column(String, default="verified")
    provenance: Mapped[str] = mapped_column(String, default="generated")
    page_count: Mapped[int] = mapped_column(Integer, default=1)
    data_origin: Mapped[str] = mapped_column(String, default="synthetic")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Telemetry(Base):
    __tablename__ = "telemetry"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    well_id: Mapped[str] = mapped_column(ForeignKey("wells.id"), index=True)
    measured_depth_m: Mapped[float] = mapped_column(Float, index=True)
    wob: Mapped[float] = mapped_column(Float)
    rpm: Mapped[float] = mapped_column(Float)
    torque: Mapped[float] = mapped_column(Float)
    mud_flow_rate: Mapped[float] = mapped_column(Float)
    rop_mhr: Mapped[float] = mapped_column(Float)
    ecd_kgL: Mapped[float] = mapped_column(Float)
    standpipe_pressure_kpa: Mapped[float] = mapped_column(Float)

    well: Mapped[Well] = relationship(back_populates="telemetry")

class Formation(Base):
    __tablename__ = "formations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    well_id: Mapped[str] = mapped_column(ForeignKey("wells.id"), index=True)
    name: Mapped[str] = mapped_column(String)
    top_depth_m: Mapped[float] = mapped_column(Float)
    base_depth_m: Mapped[float] = mapped_column(Float)

    well: Mapped[Well] = relationship(back_populates="formations")

class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    active_well_id: Mapped[str] = mapped_column(ForeignKey("wells.id", ondelete="CASCADE"), index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True, default="kick")
    interval_start_m: Mapped[float] = mapped_column(Float, index=True, default=0.0)
    interval_end_m: Mapped[float] = mapped_column(Float, index=True, default=0.0)
    current_depth_m: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(32), index=True, default="active")
    dedupe_key: Mapped[str] = mapped_column(String(255), index=True, default="")
    distance_to_interval_m: Mapped[float] = mapped_column(Float, default=0.0)
    severity: Mapped[str] = mapped_column(String(32), default="low")
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    evidence_event_ids: Mapped[list] = mapped_column(JSON, default=list)
    offset_well_ids: Mapped[list] = mapped_column(JSON, default=list)
    source_document_ids: Mapped[list] = mapped_column(JSON, default=list)
    matching_factors: Mapped[list] = mapped_column(JSON, default=list)
    data_completeness: Mapped[float] = mapped_column(Float, default=0.0)
    explanation: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
