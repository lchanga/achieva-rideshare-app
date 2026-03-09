from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from server.models.base import Base


class RideRequest(Base):
    __tablename__ = "Ride_requests"
    __table_args__ = (
        CheckConstraint(
            "status IN ('requested','scheduled','cancelled_by_passenger','cancelled_by_driver','completed')",
            name="CHK_RequestStatus",
        ),
    )

    request_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    passenger_id: Mapped[int] = mapped_column(ForeignKey("Users.user_id"), nullable=False)
    pickup_client_location_id: Mapped[int] = mapped_column(
        ForeignKey("Client_locations.client_location_id"), nullable=False
    )
    dropoff_client_location_id: Mapped[int] = mapped_column(
        ForeignKey("Client_locations.client_location_id"), nullable=False
    )

    ride_date: Mapped[date] = mapped_column(Date, nullable=False)
    pickup_window_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    pickup_window_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    dropoff_window_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    dropoff_window_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="requested")
    api_shipment_label: Mapped[str] = mapped_column(String(255), nullable=False)

