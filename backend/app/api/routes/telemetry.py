from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from ...db import get_db
from ...models import Telemetry, Well
from ...services.anomaly_detector import detect_anomalies
router = APIRouter(prefix="/api/telemetry", tags=["telemetry"])
class TelemetryIn(BaseModel):
    measured_depth_m: float = Field(ge=0)
    wob: float | None = None
    rpm: float | None = None
    torque: float | None = None
    flow_rate_lpm: float | None = None
    pressure: float | None = None
    mud_flow_rate: float | None = None
    rop_mhr: float | None = None
    ecd_kgL: float | None = None
    standpipe_pressure_kpa: float | None = None
    mwd_inclination: float | None = None
    mwd_azimuth: float | None = None
def _serialize(row: Telemetry) -> dict[str, Any]:
    return {
        "id": row.id,
        "well_id": row.well_id,
        "timestamp": row.timestamp.isoformat() if row.timestamp else None,
        "measured_depth_m": row.measured_depth_m,
        "wob": row.wob,
        "rpm": row.rpm,
        "torque": row.torque,
        "flow_rate_lpm": row.flow_rate_lpm,
        "pressure": row.pressure,
        "mud_flow_rate": row.mud_flow_rate,
        "rop_mhr": row.rop_mhr,
        "ecd_kgL": row.ecd_kgL,
        "standpipe_pressure_kpa": row.standpipe_pressure_kpa,
        "mwd_inclination": row.mwd_inclination,
        "mwd_azimuth": row.mwd_azimuth,
        "data_origin": row.data_origin,
        "is_synthetic": row.is_synthetic,
    }
def _get_well_or_404(well_id: str, db: Session) -> Well:
    well = db.get(Well, well_id)
    if not well:
        raise HTTPException(404, f"Well '{well_id}' not found")
    return well
@router.get("/{well_id}")
def get_telemetry(well_id: str, limit: int = Query(50, ge=1, le=500), db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    _get_well_or_404(well_id, db)
    rows = db.scalars(select(Telemetry).where(Telemetry.well_id == well_id).order_by(Telemetry.measured_depth_m.desc()).limit(limit)).all()
    return [_serialize(row) for row in reversed(rows)]
@router.get("/{well_id}/trend")
def get_telemetry_trend(well_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    _get_well_or_404(well_id, db)
    rows = db.scalars(select(Telemetry).where(Telemetry.well_id == well_id).order_by(Telemetry.measured_depth_m.desc()).limit(20)).all()
    records = list(reversed(rows))
    if len(records) < 2:
        return {"well_id": well_id, "sample_count": len(records), "trend": "insufficient_data"}
    def avg(items: list[Telemetry], attr: str) -> float | None:
        vals = [getattr(item, attr) for item in items if getattr(item, attr) is not None]
        return round(sum(vals) / len(vals), 4) if vals else None
    def trend_label(recent_avg: float | None, prev_avg: float | None, threshold: float = 0.05) -> str:
        if recent_avg is None or prev_avg is None or prev_avg == 0:
            return "unknown"
        change = (recent_avg - prev_avg) / abs(prev_avg)
        if change > threshold:
            return "increasing"
        if change < -threshold:
            return "decreasing"
        return "stable"
    split = len(records) // 2
    prev, recent = records[:split], records[split:]
    fields = ["wob", "rpm", "torque", "flow_rate_lpm", "mud_flow_rate", "rop_mhr", "ecd_kgL", "standpipe_pressure_kpa"]
    result: dict[str, Any] = {"well_id": well_id, "sample_count": len(records)}
    averages: dict[str, float | None] = {}
    for field in fields:
        recent_avg = avg(recent, field)
        prev_avg = avg(prev, field)
        averages[field] = recent_avg
        result[f"avg_{field}"] = recent_avg
        result[f"{field}_trend"] = trend_label(recent_avg, prev_avg)
    result["avg_wob"] = averages.get("wob")
    result["avg_rpm"] = averages.get("rpm")
    result["avg_torque"] = averages.get("torque")
    result["avg_rop"] = averages.get("rop_mhr")
    result["avg_spp"] = averages.get("standpipe_pressure_kpa")
    result["avg_ecd"] = averages.get("ecd_kgL")
    result["rop_trend"] = result.get("rop_mhr_trend", "unknown")
    result["torque_trend"] = result.get("torque_trend", "unknown")
    result["pressure_trend"] = result.get("standpipe_pressure_kpa_trend", "unknown")
    result["depth_range_m"] = {
        "min": records[0].measured_depth_m if records else None,
        "max": records[-1].measured_depth_m if records else None,
    }
    return result
@router.get("/{well_id}/anomalies")
def get_anomalies(well_id: str, limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    _get_well_or_404(well_id, db)
    rows = db.scalars(select(Telemetry).where(Telemetry.well_id == well_id).order_by(Telemetry.measured_depth_m.desc()).limit(limit)).all()
    records = [_serialize(row) for row in rows]
    return detect_anomalies(records)
@router.post("/{well_id}")
def ingest_telemetry(well_id: str, body: TelemetryIn, db: Session = Depends(get_db)) -> dict[str, Any]:
    _get_well_or_404(well_id, db)
    row = Telemetry(
        well_id=well_id,
        timestamp=datetime.now(timezone.utc),
        measured_depth_m=body.measured_depth_m,
        wob=body.wob,
        rpm=body.rpm,
        torque=body.torque,
        flow_rate_lpm=body.flow_rate_lpm,
        pressure=body.pressure,
        mud_flow_rate=body.mud_flow_rate,
        rop_mhr=body.rop_mhr,
        ecd_kgL=body.ecd_kgL,
        standpipe_pressure_kpa=body.standpipe_pressure_kpa,
        mwd_inclination=body.mwd_inclination,
        mwd_azimuth=body.mwd_azimuth,
        data_origin="live",
        is_synthetic=False,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _serialize(row)
