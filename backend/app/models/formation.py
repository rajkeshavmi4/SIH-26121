from typing import Any
from sqlalchemy import CheckConstraint, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db.base import Base
class Formation(Base):
    __tablename__ = "formations"
    __table_args__ = (CheckConstraint("top_depth_m >= 0 AND base_depth_m > top_depth_m", name="ck_formation_valid_interval"), Index("ix_formations_well_depth", "well_id", "top_depth_m", "base_depth_m"))
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    well_id: Mapped[str] = mapped_column(ForeignKey("wells.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    top_depth_m: Mapped[float] = mapped_column(Float)
    base_depth_m: Mapped[float] = mapped_column(Float)
    source_document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    well: Mapped[Any] = relationship("Well", back_populates="formations")
