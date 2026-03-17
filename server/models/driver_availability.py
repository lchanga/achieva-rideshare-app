from __future__ import annotations

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from server.models.base import Base


class DriverAvailability(Base):
    __tablename__ = "Driver_availability"
    __table_args__ = (
        UniqueConstraint("driver_id", name="UQ_DriverAvailability_driver_id"),
        {"schema": "dbo"},
    )

    availability_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    driver_id: Mapped[int] = mapped_column(ForeignKey("dbo.Users.user_id"), nullable=False)
    is_available: Mapped[bool] = mapped_column(nullable=False, default=True)
