from fastapi import APIRouter
from sqlalchemy import text
from ...db.session import engine

router = APIRouter(prefix="/api", tags=["health"])

@router.get("/health", summary="Health check")
def health() -> dict[str, str]:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ok", "service": "namowell-ai", "database": "ok"}
