from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from server.models.base import Base


class RouteStop(Base):
    __tablename__ = "Route_stops"
    __table_args__ = (
        CheckConstraint("stop_type IN ('pickup','dropoff')", name="CHK_StopType"),
        CheckConstraint("status IN ('pending','completed','skipped')", name="CHK_StopStatus"),
        UniqueConstraint("route_id", "stop_sequence", name="UQ_RouteSequence"),
        {"schema": "dbo"}, 
    )

    stop_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # ADD 'dbo.' to all of these:
    route_id: Mapped[int] = mapped_column(ForeignKey("dbo.Optimized_routes.route_id"), nullable=False)
    request_id: Mapped[int] = mapped_column(ForeignKey("dbo.Ride_requests.request_id"), nullable=False)
    location_id: Mapped[int] = mapped_column(ForeignKey("dbo.Locations.location_id"), nullable=False)

    stop_sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    stop_type: Mapped[str] = mapped_column(String(20), nullable=False)
    actual_arrival: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    planned_arrival: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
