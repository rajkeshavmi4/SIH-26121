from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from ...db import get_db
from ...models import Alert, Incident, Scenario, Telemetry, Well
from ...schemas import AlertResponse, RiskEvaluateRequest, ScenarioOut
from ...services.depth_correlation import correlate_depth
from ...services.risk_engine import evaluate_alerts
from ...services.simulation import advance_scenario
from ...services.anomaly_detector import detect_anomalies
router = APIRouter(prefix="/api", tags=["risk"])
def _alert_response(alert: Alert) -> dict:
    return {key: getattr(alert, key) for key in ("id", "dedupe_key", "active_well_id", "event_type", "interval_start_m", "interval_end_m", "current_depth_m", "status", "distance_to_interval_m", "severity", "relevance_score", "evidence_event_ids", "offset_well_ids", "source_document_ids", "matching_factors", "data_completeness", "explanation")}
def _persist_alerts(db: Session, evaluated: list[dict], active_well_id: str) -> list[Alert]:
    existing = db.scalars(select(Alert).where(Alert.active_well_id == active_well_id)).all()
    persisted = []
    for item in evaluated:
        alert = next((current for current in existing if current.event_type == item["event_type"] and current.interval_start_m <= item["interval_end_m"] and item["interval_start_m"] <= current.interval_end_m), None)
        if alert is None:
            alert = Alert(active_well_id=active_well_id, event_type=item["event_type"], interval_start_m=item["interval_start_m"], interval_end_m=item["interval_end_m"], dedupe_key=item["dedupe_key"], relevance_score=item["relevance_score"], explanation=item["explanation"])
            db.add(alert)
        for field in ("dedupe_key", "interval_start_m", "interval_end_m", "current_depth_m", "status", "distance_to_interval_m", "severity", "relevance_score", "evidence_event_ids", "offset_well_ids", "source_document_ids", "matching_factors", "data_completeness", "explanation"):
            setattr(alert, field, item[field])
        persisted.append(alert)
    active_keys = {item["dedupe_key"] for item in evaluated}
    for alert in existing:
        if alert.dedupe_key not in active_keys and alert.status != "passed":
            alert.status = "passed"
    db.commit()
    return persisted
def _evaluate_and_persist(db: Session, request: RiskEvaluateRequest) -> list[Alert]:
    try:
        correlation = correlate_depth(db, request.active_well_id, request.current_depth_m, request.target_formation, request.relevant_offset_well_ids, request.lookahead_m)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    evaluated = evaluate_alerts(request.active_well_id, request.current_depth_m, correlation["evidence"], request.lookahead_m)
    return _persist_alerts(db, evaluated, request.active_well_id)
@router.post("/risk/evaluate")
def evaluate_risk(request: RiskEvaluateRequest, db: Session = Depends(get_db)):
    alerts = _evaluate_and_persist(db, request)
    telemetry_rows = db.scalars(select(Telemetry).where(Telemetry.well_id == request.active_well_id).order_by(Telemetry.measured_depth_m.desc()).limit(20)).all()
    telemetry_records = [{key: getattr(row, key) for key in ("id", "measured_depth_m", "wob", "rpm", "torque", "flow_rate_lpm", "mud_flow_rate", "rop_mhr", "ecd_kgL", "standpipe_pressure_kpa")} for row in telemetry_rows]
    anomalies = detect_anomalies(telemetry_records)
    return {"historical_alerts": [_alert_response(alert) for alert in alerts], "telemetry_anomalies": anomalies, "total_alert_count": len(alerts) + len(anomalies)}
@router.get("/risk/alerts", response_model=list[AlertResponse])
def get_alerts(active_well_id: str | None = None, status: str | None = Query(None, pattern="^(upcoming|in_zone|passed)$"), db: Session = Depends(get_db)):
    query = select(Alert).order_by(Alert.current_depth_m, Alert.event_type)
    if active_well_id:
        query = query.where(Alert.active_well_id == active_well_id)
    if status:
        query = query.where(Alert.status == status)
    return [_alert_response(alert) for alert in db.scalars(query).all()]
@router.post("/simulation/{action}", response_model=ScenarioOut)
def simulation(action: str, scenario_id: str = "scenario-1", db: Session = Depends(get_db)):
    scenario = db.get(Scenario, scenario_id)
    if not scenario:
        raise HTTPException(404, "Scenario not found")
    try:
        advance_scenario(scenario, action)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    db.commit(); db.refresh(scenario)
    _evaluate_and_persist(db, RiskEvaluateRequest(active_well_id=scenario.active_well_id, current_depth_m=scenario.current_depth_m))
    active = db.get(Well, scenario.active_well_id)
    return {**{key: getattr(scenario, key) for key in ("id", "name", "active_well_id", "current_depth_m", "start_depth_m", "end_depth_m", "step_m", "running")}, "active_well_name": active.name if active else None}
@router.get("/simulation/state", response_model=ScenarioOut)
def simulation_state(scenario_id: str = "scenario-1", db: Session = Depends(get_db)):
    scenario = db.get(Scenario, scenario_id)
    if not scenario:
        raise HTTPException(404, "Scenario not found")
    active = db.get(Well, scenario.active_well_id)
    return {**{key: getattr(scenario, key) for key in ("id", "name", "active_well_id", "current_depth_m", "start_depth_m", "end_depth_m", "step_m", "running")}, "active_well_name": active.name if active else None}
