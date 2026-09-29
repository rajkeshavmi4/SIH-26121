from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from ...db.session import get_db
from ...models import Well
from ...repositories.well import list_wells
from ...schemas import OffsetWellListResponse, PageMeta, WellListResponse, WellResponse
from ...services.offset_engine import TargetInterval, rank_offsets
from ...services.depth_correlation import correlate_depth
from ...services.pagination import page_meta
router = APIRouter(prefix="/api", tags=["wells"])
def to_response(well: Well) -> WellResponse:
    return WellResponse.model_validate(well)
@router.get("/wells", response_model=WellListResponse, summary="List wells")
def get_wells(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), basin: str | None = None, status: str | None = None, well_type: str | None = None, db: Session = Depends(get_db)):
    items, total = list_wells(db, page, page_size, basin, status, well_type)
    return WellListResponse(items=[to_response(item) for item in items], meta=page_meta(page, page_size, total))
@router.get("/wells/{well_id}", response_model=WellResponse, summary="Get one well")
def get_well(well_id: str, db: Session = Depends(get_db)):
    well = db.get(Well, well_id)
    if not well:
        raise HTTPException(status_code=404, detail=f"Well '{well_id}' not found")
    return to_response(well)
def parse_target_depth(value: str) -> TargetInterval:
    parts = value.replace("to", "-").replace(",", "-").split("-")
    try:
        numbers = [float(part.strip()) for part in parts if part.strip()]
    except ValueError as exc:
        raise HTTPException(400, "target_depth_m must be a range such as 1200-1400") from exc
    if len(numbers) != 2:
        raise HTTPException(400, "target_depth_m must be a range such as 1200-1400")
    try:
        return TargetInterval(*numbers)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
@router.get("/wells/{well_id}/offsets", response_model=OffsetWellListResponse, summary="Rank offset wells")
def get_offsets(well_id: str, radius_km: float = Query(20, gt=0, le=500), target_depth_m: str = Query(..., description="Target depth range, for example 1200-1400"), formation: str | None = None, limit: int = Query(20, ge=1, le=100), min_score: float = Query(0, ge=0, le=100), event_type: str | None = None, sort_by: str = Query("score", pattern="^(score|distance)$"), db: Session = Depends(get_db)):
    active = db.get(Well, well_id)
    if not active:
        raise HTTPException(status_code=404, detail=f"Well '{well_id}' not found")
    result = rank_offsets(active, db.scalars(select(Well)).all(), radius_km, parse_target_depth(target_depth_m), formation, event_type)
    items = [item for item in result["items"] if item["relevance_score"] >= min_score]
    if sort_by == "distance":
        items.sort(key=lambda item: (item["distance_km"], -item["relevance_score"], item["well_id"]))
    result["items"] = items[:limit]
    return result
@router.get("/wells/{well_id}/correlation", response_model=dict, summary="Correlate active depth with offset evidence")
def get_correlation(well_id: str, current_depth_m: float = Query(..., ge=0), target_formation: str | None = None, relevant_offset_well_ids: str | None = None, lookahead_m: float = Query(100, ge=0), db: Session = Depends(get_db)):
    offset_ids = [item.strip() for item in relevant_offset_well_ids.split(",") if item.strip()] if relevant_offset_well_ids else None
    try:
        return correlate_depth(db, well_id, current_depth_m, target_formation, offset_ids, lookahead_m)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
