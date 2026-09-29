from sqlalchemy import func, select
from sqlalchemy.orm import Session
from ..models import Well
def list_wells(db: Session, page: int, page_size: int, basin: str | None = None, status: str | None = None, well_type: str | None = None) -> tuple[list[Well], int]:
    query = select(Well)
    count_query = select(func.count()).select_from(Well)
    filters = []
    if basin: filters.append(Well.basin == basin)
    if status: filters.append(Well.status == status)
    if well_type: filters.append(Well.well_type == well_type)
    if filters:
        query = query.where(*filters); count_query = count_query.where(*filters)
    total = db.scalar(count_query) or 0
    items = db.scalars(query.order_by(Well.name).offset((page - 1) * page_size).limit(page_size)).all()
    return items, total
