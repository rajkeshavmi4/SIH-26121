import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models import AlertRecord, Incident, Scenario

class AlertLifecycleService:
    @staticmethod
    def generate_dedup_key(scenario_id: str, well_id: str, incident_id: str, depth_m: float) -> str:
        depth_bucket = int(depth_m // 10) * 10
        raw_key = f"{scenario_id}:{well_id}:{incident_id}:{depth_bucket}"
        return hashlib.md5(raw_key.encode("utf-8")).hexdigest()

    @staticmethod
    def process_alert(db: Session, scenario: Scenario, incident: Incident, distance_m: float, lookahead_m: float) -> AlertRecord:
        dedup_key = AlertLifecycleService.generate_dedup_key(scenario.id, incident.well_id, incident.id, scenario.current_depth_m)
        existing = db.scalars(select(AlertRecord).where(AlertRecord.dedup_key == dedup_key)).first()

        if existing:
            if existing.status == "NEW" and distance_m <= 50.0 and existing.escalation_level == "INFO":
                existing.escalation_level = "WARNING"
            elif existing.status == "NEW" and distance_m <= 20.0 and existing.escalation_level in ["INFO", "WARNING"]:
                existing.escalation_level = "CRITICAL"
            elif existing.status == "NEW" and scenario.current_depth_m >= incident.top_depth_m and existing.escalation_level != "ESCALATED":
                existing.escalation_level = "ESCALATED"
            existing.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing)
            return existing

        initial_escalation = "INFO"
        if distance_m <= 20.0:
            initial_escalation = "CRITICAL"
        elif distance_m <= 50.0:
            initial_escalation = "WARNING"

        alert_id = f"alt-{dedup_key[:12]}"
        new_alert = AlertRecord(
            id=alert_id,
            dedup_key=dedup_key,
            scenario_id=scenario.id,
            well_id=incident.well_id,
            incident_id=incident.id,
            event_type=incident.event_type,
            status="NEW",
            escalation_level=initial_escalation,
            distance_m=round(distance_m, 2),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(new_alert)
        db.commit()
        db.refresh(new_alert)
        return new_alert

    @staticmethod
    def acknowledge_alert(db: Session, alert_id: str, user_id: str, notes: Optional[str] = None) -> AlertRecord:
        alert = db.get(AlertRecord, alert_id)
        if not alert:
            raise ValueError(f"Alert {alert_id} not found")

        alert.status = "ACKNOWLEDGED"
        alert.acknowledged_by = user_id
        alert.acknowledged_at = datetime.utcnow()
        alert.notes = notes
        alert.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(alert)
        return alert

    @staticmethod
    def expire_stale_alerts(db: Session, scenario: Scenario, lookahead_m: float) -> int:
        alerts = db.scalars(select(AlertRecord).where(AlertRecord.scenario_id == scenario.id, AlertRecord.status.in_(["NEW", "ACKNOWLEDGED"]))).all()
        expired_count = 0

        for alert in alerts:
            incident = db.get(Incident, alert.incident_id)
            if incident and scenario.current_depth_m > (incident.bottom_depth_m + lookahead_m):
                alert.status = "EXPIRED"
                alert.updated_at = datetime.utcnow()
                expired_count += 1

        if expired_count > 0:
            db.commit()
        return expired_count

alert_lifecycle = AlertLifecycleService()
