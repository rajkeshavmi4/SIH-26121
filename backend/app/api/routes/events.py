from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ...db.session import get_db
from ...repositories.event import search_events
from ...schemas import EventResponse, EventSearchResponse
from ...services.pagination import page_meta
router = APIRouter(prefix="/api", tags=["events"])
@router.get("/wells/{well_id}/events", response_model=EventSearchResponse, summary="List events for a well")
def get_well_events(well_id: str, page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), event_type: str | None = None, min_depth_m: float | None = Query(None, ge=0), max_depth_m: float | None = Query(None, ge=0), db: Session = Depends(get_db)):
    items, total = search_events(db, page, page_size, well_id=well_id, event_type=event_type, min_depth_m=min_depth_m, max_depth_m=max_depth_m)
    return EventSearchResponse(items=[EventResponse.model_validate(item) for item in items], meta=page_meta(page, page_size, total))
@router.get("/events/search", response_model=EventSearchResponse, summary="Search historical events")
def search_well_events(q: str | None = Query(None, min_length=2), page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), well_id: str | None = None, event_type: str | None = None, formation_name: str | None = None, min_depth_m: float | None = Query(None, ge=0), max_depth_m: float | None = Query(None, ge=0), db: Session = Depends(get_db)):
    items, total = search_events(db, page, page_size, q, well_id, event_type, formation_name, min_depth_m, max_depth_m)
    return EventSearchResponse(items=[EventResponse.model_validate(item) for item in items], meta=page_meta(page, page_size, total))
