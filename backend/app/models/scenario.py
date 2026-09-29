from sqlalchemy import Boolean, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from ..db.base import Base
class Scenario(Base):
    __tablename__ = "scenarios"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    active_well_id: Mapped[str] = mapped_column(ForeignKey("wells.id"))
    current_depth_m: Mapped[float] = mapped_column(Float)
    start_depth_m: Mapped[float] = mapped_column(Float)
    end_depth_m: Mapped[float] = mapped_column(Float)
    step_m: Mapped[float] = mapped_column(Float, default=100)
    running: Mapped[bool] = mapped_column(Boolean, default=False)
