from __future__ import annotations
from datetime import date, datetime
from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from server.models.base import Base

class OptimizedRoute(Base):
    __tablename__ = "Optimized_routes"
    __table_args__ = (
        CheckConstraint("status IN ('available','assigned','in_progress','completed')", name="CHK_RouteStatus"),
        {"schema": "dbo"}, 
    )

    route_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    
    driver_id: Mapped[int | None] = mapped_column(ForeignKey("dbo.Users.user_id"), nullable=True)
    
    route_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="available")
    polyline: Mapped[str | None] = mapped_column(String, nullable=True)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    
    run_id: Mapped[int] = mapped_column(ForeignKey("dbo.Optimization_runs.run_id"), nullable=False)