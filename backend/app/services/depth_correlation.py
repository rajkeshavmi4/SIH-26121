from typing import Any, Iterable
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import Formation, Incident, Well
def interval_overlap(active_top: float, active_bottom: float, event_top: float, event_bottom: float) -> float:
    if active_top == active_bottom:
        return 1.0 if event_top <= active_top <= event_bottom else 0.0
    overlap = max(0.0, min(active_bottom, event_bottom) - max(active_top, event_top))
    return overlap / max(active_bottom - active_top, 1.0)
def distance_to_interval(depth_m: float, top_m: float, bottom_m: float) -> float:
    if top_m <= depth_m <= bottom_m:
        return 0.0
    return top_m - depth_m if depth_m < top_m else depth_m - bottom_m
def interval_status(depth_m: float, top_m: float, bottom_m: float, lookahead_m: float = 100.0) -> str:
    distance = distance_to_interval(depth_m, top_m, bottom_m)
    if top_m <= depth_m <= bottom_m:
        return "in_zone"
    if depth_m < top_m and distance <= lookahead_m:
        return "upcoming"
    return "passed" if depth_m > bottom_m else "outside"
def _formation_name(item: Any) -> str | None:
    return getattr(item, "formation_name", None) or getattr(item, "name", None) or getattr(item, "formation", None)
def correlate_depth(db: Session, active_well_id: str, current_depth_m: float, target_formation: str | None = None, relevant_offset_well_ids: Iterable[str] | None = None, lookahead_m: float = 100.0) -> dict[str, Any]:
    active = db.get(Well, active_well_id)
    if not active:
        raise ValueError(f"Well '{active_well_id}' not found")
    offset_ids = set(relevant_offset_well_ids or [])
    if not offset_ids:
        offset_ids = {well.id for well in db.scalars(select(Well)).all() if well.id != active_well_id}
    wells = {well.id: well for well in db.scalars(select(Well).where(Well.id.in_(offset_ids))).all()}
    events = db.scalars(select(Incident).where(Incident.well_id.in_(offset_ids)).order_by(Incident.start_depth_m, Incident.id)).all() if offset_ids else []
    formations = db.scalars(select(Formation).where(Formation.well_id.in_(offset_ids)).order_by(Formation.top_depth_m, Formation.id)).all() if offset_ids else []
    target = target_formation.strip().casefold() if target_formation else None
    markers = []
    evidence = []
    for event in events:
        event_formation = event.formation_name
        formation_match = not target or (event_formation and event_formation.casefold() == target)
        marker = {"event_id": event.id, "event_type": event.event_type, "top_depth_m": event.start_depth_m, "bottom_depth_m": event.end_depth_m, "formation": event_formation, "severity": event.severity, "offset_well_id": event.well_id, "offset_well_name": wells.get(event.well_id).name if wells.get(event.well_id) else None, "source_document_id": event.source_document_id, "source_page": event.source_page, "distance_to_interval_m": distance_to_interval(current_depth_m, event.start_depth_m, event.end_depth_m), "lookahead_status": interval_status(current_depth_m, event.start_depth_m, event.end_depth_m, lookahead_m), "formation_match": formation_match, "overlap_ratio": interval_overlap(current_depth_m, current_depth_m, event.start_depth_m, event.end_depth_m)}
        markers.append(marker)
        if formation_match:
            evidence.append({"event_id": event.id, "offset_well_id": event.well_id, "event_type": event.event_type, "source_document_id": event.source_document_id, "source_page": event.source_page, "severity": event.severity, "interval": [event.start_depth_m, event.end_depth_m]})
    bands = [{"formation": formation.name, "top_depth_m": formation.top_depth_m, "bottom_depth_m": formation.base_depth_m, "offset_well_id": formation.well_id, "target_match": not target or formation.name.casefold() == target} for formation in formations]
    return {"active_well_id": active_well_id, "active_depth_m": current_depth_m, "target_formation": target_formation, "lookahead_m": lookahead_m, "event_markers": markers, "formation_bands": bands, "evidence": evidence, "offset_well_ids": sorted(wells)}
