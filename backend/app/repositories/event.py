from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from ..models import WellEvent
def search_events(db: Session, page: int, page_size: int, q: str | None = None, well_id: str | None = None, event_type: str | None = None, formation_name: str | None = None, min_depth_m: float | None = None, max_depth_m: float | None = None) -> tuple[list[WellEvent], int]:
    query = select(WellEvent); count_query = select(func.count()).select_from(WellEvent); filters = []
    if q:
        term = f"%{q}%"; filters.append(or_(WellEvent.event_type.ilike(term), WellEvent.original_event_type.ilike(term), WellEvent.description.ilike(term), WellEvent.recorded_mitigation.ilike(term), WellEvent.formation_name.ilike(term)))
    if well_id: filters.append(WellEvent.well_id == well_id)
    if event_type: filters.append(WellEvent.event_type == event_type)
    if formation_name: filters.append(WellEvent.formation_name == formation_name)
    if min_depth_m is not None: filters.append(WellEvent.end_depth_m >= min_depth_m)
    if max_depth_m is not None: filters.append(WellEvent.start_depth_m <= max_depth_m)
    if filters:
        query = query.where(*filters); count_query = count_query.where(*filters)
    total = db.scalar(count_query) or 0
    items = db.scalars(query.order_by(WellEvent.start_depth_m, WellEvent.id).offset((page - 1) * page_size).limit(page_size)).all()
    return items, total
