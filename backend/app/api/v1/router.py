import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from ...db import get_db
from ...models import Well, Incident, Scenario, AuditLog, CasingData, CementingData, MudData, BHAData, TrajectoryData, FormationData, AlertRecord, ReviewItem, ModelRegistry
from ...schemas import (
    WellOut, IncidentOut, AlertOut, ScenarioOut, DashboardOut, CorrelationOut, UploadOut,
    AuditLogOut, CasingOut, CementingOut, MudOut, BHAOut, TrajectoryOut, FormationOut,
    AlertRecordOut, ReviewItemOut, ReviewActionInput, AlertAcknowledgeInput,
    ModelTrainInput, ModelPredictInput, ModelPredictOut, ReplayCourtInput, BenchmarkMetricOut, APIResponse
)
from ...core.rbac import require_read, require_reviewer, require_engineer, require_admin, UserRole
from ...core.events import event_bus, DomainEvent
from ...services.ocr_service import ocr_pipeline
from ...services.tvd_engine import tvd_engine, TVDEngine
from ...services.witsml_adapter import witsml_adapter
from ...services.alert_lifecycle import alert_lifecycle
from ...services.replay_court import replay_court
from ...services.ml_pipeline import ml_pipeline
from ...scoring import rank_offset

router = APIRouter(prefix="/api/v1")

def record_audit(db: Session, actor: str, role: str, action: str, res_type: str, res_id: Optional[str] = None, details: Optional[str] = None):
    log_entry = AuditLog(
        actor=actor,
        user_role=role,
        action=action,
        resource_type=res_type,
        resource_id=res_id,
        details=details
    )
    db.add(log_entry)
    db.commit()

@router.get("/health")
def health_check():
    return {"status": "ok", "service": "namowell-ai", "version": "1.0.0"}

@router.get("/scenarios", response_model=List[ScenarioOut])
def get_scenarios(db: Session = Depends(get_db), role: UserRole = Depends(require_read)):
    scenarios = db.scalars(select(Scenario).order_by(Scenario.id)).all()
    results = []
    for sc in scenarios:
        active = db.get(Well, sc.active_well_id)
        payload = ScenarioOut.model_validate(sc, from_attributes=True).model_dump()
        payload["active_well_name"] = active.name if active else None
        results.append(ScenarioOut.model_validate(payload))
    return results

@router.get("/wells", response_model=List[WellOut])
def get_wells(scenario_id: Optional[str] = None, radius_km: float = Query(50.0, ge=1, le=500), db: Session = Depends(get_db), role: UserRole = Depends(require_read)):
    all_wells = db.scalars(select(Well)).all()
    if not all_wells:
        return []
        
    active = None
    if scenario_id:
        scenario = db.get(Scenario, scenario_id)
        if scenario:
            active = db.get(Well, scenario.active_well_id)
            
    if not active:
        active = all_wells[0]

    results = []
    for candidate in all_wells:
        if candidate.id == active.id:
            continue
        score = rank_offset(active, candidate, len(candidate.incidents))
        if score["distance_km"] <= radius_km:
            prov = {"source_type": "synthetic", "is_synthetic": candidate.is_synthetic, "demo_label": candidate.demo_label}
            results.append(WellOut(
                id=candidate.id,
                name=candidate.name,
                latitude=candidate.latitude,
                longitude=candidate.longitude,
                total_depth_m=candidate.total_depth_m,
                formation=candidate.formation,
                trajectory=candidate.trajectory,
                status=candidate.status,
                provenance=prov,
                distance_km=score["distance_km"],
                relevance_score=score["relevance_score"],
                score_factors=score["score_factors"],
                missing_fields=score["missing_fields"]
            ))
    return sorted(results, key=lambda x: x.relevance_score or 0, reverse=True)

@router.get("/incidents", response_model=List[IncidentOut])
def get_incidents(well_id: Optional[str] = None, event_type: Optional[str] = None, formation: Optional[str] = None, severity: Optional[str] = None, db: Session = Depends(get_db), role: UserRole = Depends(require_read)):
    query = select(Incident, Well.name).join(Well)
    if well_id:
        query = query.where(Incident.well_id == well_id)
    if event_type:
        query = query.where(Incident.event_type == event_type)
    if formation:
        query = query.where(Incident.formation == formation)
    if severity:
        query = query.where(Incident.severity == severity)
        
    rows = db.execute(query.order_by(Incident.top_depth_m)).all()
    results = []
    for inc, well_name in rows:
        results.append(IncidentOut(
            id=inc.id,
            well_id=inc.well_id,
            well_name=well_name,
            event_type=inc.event_type,
            top_depth_m=inc.top_depth_m,
            bottom_depth_m=inc.bottom_depth_m,
            formation=inc.formation,
            severity=inc.severity,
            mitigation=inc.mitigation,
            source_document=inc.source_document,
            source_page=inc.source_page,
            bounding_box=inc.bounding_box,
            snippet=inc.snippet,
            confidence=inc.confidence,
            source_type=inc.source_type,
            is_synthetic=inc.is_synthetic,
            approval_status=inc.approval_status
        ))
    return results

@router.get("/engineering/{well_id}")
def get_engineering_data(well_id: str, db: Session = Depends(get_db), role: UserRole = Depends(require_read)):
    well = db.get(Well, well_id)
    if not well:
        raise HTTPException(404, "Well not found")

    return {
        "well_id": well_id,
        "casings": [CasingOut.model_validate(c) for c in well.casings],
        "cementings": [CementingOut.model_validate(c) for c in well.cementings],
        "muds": [MudOut.model_validate(m) for m in well.muds],
        "bhas": [BHAOut.model_validate(b) for b in well.bhas],
        "trajectories": [TrajectoryOut.model_validate(t) for t in well.trajectories],
        "formations": [FormationOut.model_validate(f) for f in well.formation_data]
    }

@router.get("/correlation/tvd-aware")
def get_tvd_correlation(scenario_id: str = "scenario-1", db: Session = Depends(get_db), role: UserRole = Depends(require_read)):
    scenario = db.get(Scenario, scenario_id)
    if not scenario:
        raise HTTPException(404, "Scenario not found")

    active = db.get(Well, scenario.active_well_id)
    all_wells = db.scalars(select(Well)).all()
    offset_ids = [w.id for w in all_wells if w.id != active.id]

    res = tvd_engine.formation_aware_correlation(db, active.id, scenario.current_depth_m, offset_ids)
    return res

@router.get("/alerts", response_model=List[AlertRecordOut])
def get_alerts(scenario_id: str = "scenario-1", status: Optional[str] = None, db: Session = Depends(get_db), role: UserRole = Depends(require_read)):
    scenario = db.get(Scenario, scenario_id)
    if not scenario:
        raise HTTPException(404, "Scenario not found")

    alert_lifecycle.expire_stale_alerts(db, scenario, 300.0)

    query = select(AlertRecord).where(AlertRecord.scenario_id == scenario_id)
    if status:
        query = query.where(AlertRecord.status == status)

    records = db.scalars(query.order_by(AlertRecord.created_at.desc())).all()
    return [AlertRecordOut.model_validate(r) for r in records]

@router.post("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: str, input_data: AlertAcknowledgeInput, db: Session = Depends(get_db), role: UserRole = Depends(require_engineer)):
    try:
        updated = alert_lifecycle.acknowledge_alert(db, alert_id, input_data.user_id, input_data.notes)
        record_audit(db, input_data.user_id, role.value, "ACKNOWLEDGE_ALERT", "AlertRecord", alert_id, f"Notes: {input_data.notes}")
        event_bus.publish(DomainEvent(
            event_type="ALERT_ACKNOWLEDGED",
            aggregate_id=alert_id,
            payload={"acknowledged_by": input_data.user_id, "notes": input_data.notes},
            actor=input_data.user_id
        ))
        return AlertRecordOut.model_validate(updated)
    except ValueError as e:
        raise HTTPException(404, str(e))

@router.post("/documents/ocr-process")
def process_ocr_document(filename: str, content: str, db: Session = Depends(get_db), role: UserRole = Depends(require_engineer)):
    res = ocr_pipeline.process_text_or_file(content, filename)
    record_audit(db, "system", role.value, "OCR_PROCESS", "Document", filename, f"Pages: {res['page_count']}, Evidence count: {len(res['evidence'])}")
    event_bus.publish(DomainEvent(
        event_type="DOCUMENT_PROCESSED",
        aggregate_id=filename,
        payload={"page_count": res["page_count"], "evidence_count": len(res["evidence"])}
    ))
    return res

@router.get("/reviews/pending", response_model=List[ReviewItemOut])
def get_pending_reviews(db: Session = Depends(get_db), role: UserRole = Depends(require_reviewer)):
    items = db.scalars(select(ReviewItem).where(ReviewItem.status == "PENDING_REVIEW")).all()
    return [ReviewItemOut.model_validate(i) for i in items]

@router.post("/reviews/{review_id}/approve")
def approve_review(review_id: str, input_data: ReviewActionInput, db: Session = Depends(get_db), role: UserRole = Depends(require_reviewer)):
    item = db.get(ReviewItem, review_id)
    if not item:
        raise HTTPException(404, "Review item not found")

    item.status = "APPROVED"
    item.reviewer_id = input_data.reviewer_id
    item.reviewer_notes = input_data.notes
    db.commit()

    record_audit(db, input_data.reviewer_id, role.value, "APPROVE_ITEM", item.entity_type, item.entity_id, input_data.notes)
    event_bus.publish(DomainEvent(
        event_type="REVIEW_APPROVED",
        aggregate_id=review_id,
        payload={"entity_type": item.entity_type, "reviewer_id": input_data.reviewer_id},
        actor=input_data.reviewer_id
    ))
    return ReviewItemOut.model_validate(item)

@router.post("/reviews/{review_id}/reject")
def reject_review(review_id: str, input_data: ReviewActionInput, db: Session = Depends(get_db), role: UserRole = Depends(require_reviewer)):
    item = db.get(ReviewItem, review_id)
    if not item:
        raise HTTPException(404, "Review item not found")

    item.status = "REJECTED"
    item.reviewer_id = input_data.reviewer_id
    item.reviewer_notes = input_data.notes
    db.commit()

    record_audit(db, input_data.reviewer_id, role.value, "REJECT_ITEM", item.entity_type, item.entity_id, input_data.notes)
    return ReviewItemOut.model_validate(item)

@router.get("/audit-trail", response_model=List[AuditLogOut])
def get_audit_trail(limit: int = 50, db: Session = Depends(get_db), role: UserRole = Depends(require_read)):
    logs = db.scalars(select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)).all()
    return [AuditLogOut.model_validate(l) for l in logs]

@router.post("/witsml/connect")
def connect_witsml(server_url: str = "wss://etp.namowell.local/v12", role: UserRole = Depends(require_engineer)):
    return witsml_adapter.connect_etp_session(server_url)

@router.post("/witsml/subscribe")
def subscribe_witsml(well_id: str, mnemonic: str = "WOB", role: UserRole = Depends(require_engineer)):
    return witsml_adapter.subscribe_channel(well_id, mnemonic)

@router.post("/models/train")
def train_model(input_data: ModelTrainInput, db: Session = Depends(get_db), role: UserRole = Depends(require_engineer)):
    res = ml_pipeline.train_baseline_model(synthetic_samples=250)
    reg_id = f"mod-{res['version']}"
    reg = ModelRegistry(
        id=reg_id,
        model_name=res["model_name"],
        version=res["version"],
        metrics_json=json.dumps({"accuracy": res["accuracy"]}),
        feature_names_json=json.dumps(res["features"]),
        model_binary_b64=res["model_b64"],
        status="ACTIVE"
    )
    db.add(reg)
    db.commit()

    record_audit(db, "engineer", role.value, "TRAIN_MODEL", "ModelRegistry", reg_id, f"Accuracy: {res['accuracy']}")
    event_bus.publish(DomainEvent(
        event_type="MODEL_TRAINED",
        aggregate_id=reg_id,
        payload={"accuracy": res["accuracy"], "model_name": res["model_name"]}
    ))
    return res

@router.post("/models/predict", response_model=ModelPredictOut)
def predict_hazard(input_data: ModelPredictInput, role: UserRole = Depends(require_read)):
    res = ml_pipeline.predict_hazard(input_data.model_dump())
    return ModelPredictOut.model_validate(res)

@router.post("/benchmark/run", response_model=BenchmarkMetricOut)
def run_benchmark(input_data: ReplayCourtInput, db: Session = Depends(get_db), role: UserRole = Depends(require_engineer)):
    res = replay_court.run_benchmark(db, input_data.scenario_id, input_data.step_size_m, input_data.lookahead_m)
    record_audit(db, "engineer", role.value, "RUN_BENCHMARK", "Scenario", input_data.scenario_id, f"F1: {res['f1_score']}, Grade: {res['grade']}")
    event_bus.publish(DomainEvent(
        event_type="BENCHMARK_COMPLETED",
        aggregate_id=input_data.scenario_id,
        payload={"f1_score": res["f1_score"], "grade": res["grade"]}
    ))
    return BenchmarkMetricOut.model_validate(res)
