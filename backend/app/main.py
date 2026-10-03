from pathlib import Path
from collections import Counter
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from .alerts import build_alerts
from .core.config import settings
from .core.logging import configure_logging
from .db import Base, engine, get_db
from .models import Incident, Scenario, Well, AuditLog
from .schemas import AlertOut, CorrelationOut, DashboardOut, IncidentOut, ScenarioOut, WellOut
from .scoring import distance_km, rank_offset
from .api.routes import events as event_routes
from .api.routes import health as health_routes
from .api.routes import wells as well_routes
from .api.routes import documents as document_routes
from .api.routes import risk as risk_routes
from .api.routes import telemetry as telemetry_routes
from .api.v1.router import router as v1_router

configure_logging()

app = FastAPI(title="Namowell AI", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
Base.metadata.create_all(engine)

app.include_router(v1_router)
app.include_router(health_routes.router)
app.include_router(well_routes.router)
app.include_router(event_routes.router)
app.include_router(document_routes.router)
app.include_router(risk_routes.router)
app.include_router(telemetry_routes.router)

def well_out(well: Well, **extra) -> WellOut:
    return WellOut(id=well.id, name=well.name, latitude=well.latitude, longitude=well.longitude, total_depth_m=well.total_depth_m, formation=well.formation, trajectory=well.trajectory, status=well.status, provenance={"source_type": "synthetic", "is_synthetic": well.is_synthetic, "demo_label": well.demo_label}, **extra)

def incident_out(incident: Incident, well_name: str | None = None) -> IncidentOut:
    return IncidentOut(id=incident.id, well_id=incident.well_id, well_name=well_name, event_type=incident.event_type, top_depth_m=incident.top_depth_m, bottom_depth_m=incident.bottom_depth_m, formation=incident.formation, severity=incident.severity, mitigation=incident.mitigation, source_document=incident.source_document, source_page=incident.source_page, bounding_box=incident.bounding_box, snippet=incident.snippet, confidence=incident.confidence, source_type=incident.source_type, is_synthetic=incident.is_synthetic, approval_status=incident.approval_status)

def alert_out(item: dict, db: Session) -> AlertOut:
    incident = item["incident"]
    well = db.get(Well, incident.well_id)
    return AlertOut(incident=incident_out(incident, well.name if well else None), status=item["status"], distance_to_interval_m=item["distance_to_interval_m"], relevance_factors=item["relevance_factors"], data_completeness=item["data_completeness"])

def scenario_out(scenario: Scenario, db: Session) -> ScenarioOut:
    active = db.get(Well, scenario.active_well_id)
    payload = ScenarioOut.model_validate(scenario, from_attributes=True).model_dump()
    payload["active_well_name"] = active.name if active else None
    return ScenarioOut.model_validate(payload)

def get_scenario(scenario_id: str, db: Session) -> Scenario:
    scenario = db.get(Scenario, scenario_id)
    if not scenario:
        raise HTTPException(404, "Scenario not found")
    return scenario

@app.get("/api/scenarios", response_model=list[ScenarioOut])
def scenarios(db: Session = Depends(get_db)):
    return [scenario_out(item, db) for item in db.scalars(select(Scenario).order_by(Scenario.id))]

@app.get("/api/demo-wells", response_model=list[WellOut])
def wells(scenario_id: str = "scenario-1", radius_km: float = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    scenario = get_scenario(scenario_id, db)
    active = db.get(Well, scenario.active_well_id)
    results = []
    for candidate in db.scalars(select(Well)).all():
        if candidate.id == active.id:
            continue
        score = rank_offset(active, candidate, len(candidate.incidents))
        if score["distance_km"] <= radius_km:
            results.append(well_out(candidate, **score))
    return sorted(results, key=lambda item: item.relevance_score or 0, reverse=True)

@app.get("/api/incidents", response_model=list[IncidentOut])
def incidents(event_type: str | None = None, formation: str | None = None, severity: str | None = None, well_id: str | None = None, min_depth_m: float | None = None, max_depth_m: float | None = None, db: Session = Depends(get_db)):
    query = select(Incident, Well.name).join(Well)
    if event_type: query = query.where(Incident.event_type == event_type)
    if formation: query = query.where(Incident.formation == formation)
    if severity: query = query.where(Incident.severity == severity)
    if well_id: query = query.where(Incident.well_id == well_id)
    if min_depth_m is not None: query = query.where(Incident.bottom_depth_m >= min_depth_m)
    if max_depth_m is not None: query = query.where(Incident.top_depth_m <= max_depth_m)
    return [incident_out(item, name) for item, name in db.execute(query.order_by(Incident.top_depth_m)).all()]

@app.get("/api/dashboard", response_model=DashboardOut)
def dashboard(scenario_id: str = "scenario-1", radius_km: float = Query(50.0, ge=1, le=500), db: Session = Depends(get_db)):
    scenario = get_scenario(scenario_id, db)
    active = db.get(Well, scenario.active_well_id)
    offsets = wells(scenario_id, radius_km, db)
    related = db.scalars(select(Incident).where(Incident.well_id.in_([item.id for item in [active] + [db.get(Well, offset.id) for offset in offsets]]))).all()
    alerts = [alert_out(item, db) for item in build_alerts(scenario.current_depth_m, list(related), settings.lookahead_meters)]
    return DashboardOut(scenario=scenario_out(scenario, db), active_well=well_out(active), offsets=offsets, alerts=alerts, incident_count=len(related))

@app.get("/api/correlation", response_model=dict)
def correlation(scenario_id: str = "scenario-1", db: Session = Depends(get_db)):
    scenario = get_scenario(scenario_id, db)
    active = db.get(Well, scenario.active_well_id)
    related = db.scalars(select(Incident).where(Incident.well_id != active.id)).all()
    bands = [{"formation": formation, "top_depth_m": index * 500, "bottom_depth_m": (index + 1) * 500, "color": ["#f2cc8f", "#81b29a", "#e07a5f", "#3d405b"][index % 4]} for index, formation in enumerate([active.formation] + [f for f in ["Barail", "Tikak Parbat", "Girujan", "Lakshmi", "Tipam", "Narpuh", "Sylhet"] if f != active.formation])]
    alerts = [alert_out(item, db) for item in build_alerts(scenario.current_depth_m, list(related), settings.lookahead_meters)]
    return {"scenario": scenario_out(scenario, db), "formations": bands, "incidents": [incident_out(item, db.get(Well, item.well_id).name) for item in related], "alerts": alerts}

@app.post("/api/simulation/{action}", response_model=ScenarioOut)
def simulation(action: str, scenario_id: str = "scenario-1", db: Session = Depends(get_db)):
    scenario = get_scenario(scenario_id, db)
    if action == "start": scenario.running = True
    elif action == "pause": scenario.running = False
    elif action == "reset": scenario.current_depth_m, scenario.running = scenario.start_depth_m, False
    elif action == "step": scenario.current_depth_m = min(scenario.end_depth_m, scenario.current_depth_m + scenario.step_m)
    else: raise HTTPException(400, "Action must be start, pause, step, or reset")
    db.commit()
    db.refresh(scenario)
    return scenario_out(scenario, db)

@app.get("/api/search")
def search(q: str = Query(min_length=2), db: Session = Depends(get_db)):
    term = f"%{q.lower()}%"
    found = db.execute(select(Incident, Well.name).join(Well).where(or_(Incident.event_type.ilike(term), Incident.formation.ilike(term), Incident.mitigation.ilike(term), Incident.source_document.ilike(term)))).all()
    return {"query": q, "results": [incident_out(item, name).model_dump() for item, name in found]}

@app.get("/api/namowell/summary")
@app.get("/api/namowell/summary")
def namowell_summary(scenario_id: str = "scenario-1", radius_km: float = Query(50, ge=1, le=200), lookahead_m: float = Query(300, ge=0), db: Session = Depends(get_db)):
    from .services.offset_engine import TargetInterval, rank_offsets
    from .services.depth_correlation import correlate_depth
    from .services.anomaly_detector import detect_anomalies
    from .models import Telemetry
    scenario = get_scenario(scenario_id, db)
    active = db.get(Well, scenario.active_well_id)
    depth = scenario.current_depth_m
    target_interval = TargetInterval(max(0, depth - 200), depth + lookahead_m)
    all_wells = db.scalars(select(Well)).all()
    offset_result = rank_offsets(active, all_wells, radius_km, target_interval)
    top_offsets = offset_result["items"][:8]
    top_offset_ids = [item["well_id"] for item in top_offsets]
    correlation_res = correlate_depth(db, active.id, depth, None, top_offset_ids, lookahead_m)
    depth_alerts = [alert_out(item, db) for item in build_alerts(depth, db.scalars(select(Incident).where(Incident.well_id.in_(top_offset_ids))).all(), lookahead_m)]
    telemetry_rows = db.scalars(select(Telemetry).where(Telemetry.well_id == active.id).order_by(Telemetry.measured_depth_m.desc()).limit(20)).all()
    telemetry_records = [{key: getattr(row, key) for key in ("id", "measured_depth_m", "wob", "rpm", "torque", "mud_flow_rate", "rop_mhr", "ecd_kgL", "standpipe_pressure_kpa")} for row in telemetry_rows]
    telemetry_anomalies = detect_anomalies(telemetry_records)
    all_incidents = db.scalars(select(Incident).where(Incident.well_id.in_(top_offset_ids))).all()
    event_counts = dict(Counter(item.event_type for item in all_incidents))
    severity_counts = dict(Counter(item.severity for item in all_incidents))
    completed_fields = sum(1 for item in top_offsets if not item.get("missing_fields"))
    data_completeness = round(completed_fields / max(len(top_offsets), 1), 2) if top_offsets else 0.0
    return {
        "scenario": scenario_out(scenario, db),
        "active_well": well_out(active),
        "offset_wells": top_offsets,
        "excluded_wells": offset_result.get("excluded", []),
        "depth_correlation": {
            "event_markers": correlation_res["event_markers"][:20],
            "formation_bands": correlation_res["formation_bands"][:16],
            "lookahead_m": lookahead_m,
        },
        "historical_alerts": [item.model_dump() for item in depth_alerts],
        "telemetry_anomalies": telemetry_anomalies,
        "incident_statistics": {
            "total": len(all_incidents),
            "by_event_type": event_counts,
            "by_severity": severity_counts,
        },
        "search_radius_km": radius_km,
        "data_provenance": {
            "offset_well_count": len(top_offsets),
            "excluded_count": len(offset_result.get("excluded", [])),
            "data_completeness": data_completeness,
            "weight_note": offset_result.get("weight_note", ""),
            "telemetry_records_analyzed": len(telemetry_records),
            "all_data_synthetic": True,
        },
    }
