from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from ..db.base import Base
class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), index=True)
    document_type: Mapped[str] = mapped_column(String(64), default="report")
    storage_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    document_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    content_sha256: Mapped[str] = mapped_column(String(64), index=True)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    mime_type: Mapped[str] = mapped_column(String(128), default="text/plain")
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extraction_status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    extraction_confidence: Mapped[float | None] = mapped_column(nullable=True)
    review_status: Mapped[str] = mapped_column(String(32), default="needs_review", index=True)
    provenance: Mapped[str] = mapped_column(Text, default="uploaded by user")
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    data_origin: Mapped[str] = mapped_column(String(32), default="uploaded", index=True)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
